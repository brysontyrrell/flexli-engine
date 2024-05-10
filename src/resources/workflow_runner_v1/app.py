from __future__ import annotations

import copy
from datetime import datetime, timedelta

# from functools import lru_cache
import json
import os
import posixpath
import time
from typing import Optional, Union
from urllib.parse import urlunparse

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
import requests
from ulid import ULID

import flexli_globals
from aws_utils import get_boto3_client, get_boto3_resource
from conditions import ConditionEvaluator
from database.connectors import read_connector
from database.workflows import read_workflow_version
from transforms import TransformError, transform

MAIN_TABLE_NAME = os.environ["MAIN_TABLE_NAME"]
WORKFLOW_HISTORY_V1_TABLE_NAME = os.environ["WORKFLOW_HISTORY_V1_TABLE_NAME"]
DATA_V1_TABLE_NAME = os.environ["DATA_V1_TABLE_NAME"]
EVENTS_QUEUE_URL = os.environ["EVENTS_QUEUE_URL"]
RUN_QUEUE_URL = os.environ["RUN_QUEUE_URL"]

logger = Logger()
tracer = Tracer()

processor = BatchProcessor(event_type=EventType.SQS)

main_table = get_boto3_resource("dynamodb").Table(MAIN_TABLE_NAME)
workflow_history_v1_table = get_boto3_resource("dynamodb").Table(
    WORKFLOW_HISTORY_V1_TABLE_NAME
)
data_table = get_boto3_resource("dynamodb").Table(DATA_V1_TABLE_NAME)

kms_client = get_boto3_client("kms")
sqs_client = get_boto3_client("sqs")


class WorkflowError(Exception):
    def __init__(self, failed_action: dict, exception: Exception = None):
        self.failed_action = failed_action
        self.exception = exception


class WorkflowFailed(WorkflowError):
    pass


class CoreActionFailure(Exception):
    pass


class ConditionFailedFail(WorkflowError):
    pass


class ConditionFailedStop(WorkflowError):
    pass


# TODO: Fix your bug that's mutating the cached response
# @lru_cache
def read_connector_cached(tenant_id: str, connector_id: str) -> dict:
    return read_connector(
        table_resource=main_table, tenant_id=tenant_id, connector_id=connector_id
    )


class FlexliCoreV1:
    def __init__(self, runner: WorkflowRunnerV1):
        self._runner = runner

    def customevent(
        self, event_type: str, content_type: str, body: Union[str, dict], **kwargs
    ):
        if content_type.lower() == "application/json":
            data = json.dumps(body)
        else:
            data = body

        # TODO: This must include the parent run ID for tracing
        sqs_client.send_message(
            QueueUrl=EVENTS_QUEUE_URL,
            MessageBody=json.dumps(
                {
                    "specversion": "1.0",
                    "type": f"Flexli:CoreV1:{event_type}",
                    "source": "flexli.workflow",
                    "id": str(ULID()),
                    "tenantid": self._runner.tenant_id,
                    "connectorid": "Flexli:CoreV1",
                    "time": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
                    "datacontenttype": content_type,
                    "data": data,
                }
                # cls=DecimalEncoder,
            ),
        )

    def runworkflow(
        self, workflow_id: str, workflow_version: int, workflow_input: dict, **kwargs
    ):
        # TODO: This code is shared ith the Run API and needs to be in a module
        workflow_data = read_workflow_version(
            main_table,
            tenant_id=self._runner.tenant_id,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
        )

        # Source-less workflows are allowed through the Run API
        if workflow_source := workflow_data.get("source"):
            if source_condition := workflow_source.get("condition"):
                if not ConditionEvaluator(source_condition).evaluate(workflow_input):
                    raise CoreActionFailure("Nested workflow condition failed.")

        new_run_id = str(ULID())

        sqs_client.send_message(
            QueueUrl=RUN_QUEUE_URL,
            MessageBody=json.dumps(
                {
                    "tenant_id": self._runner.tenant_id,
                    "workflow_id": workflow_id,
                    "workflow_version": workflow_version,
                    "parent_run_id": self._runner.run_id,
                    "run_id": new_run_id,
                    "source_input": workflow_input,
                    "actions": workflow_data["actions"],
                },
                # cls=DecimalEncoder,
            ),
        )

        main_table.put_item(
            Item={
                "pk": f"T#{self._runner.tenant_id}#WH#{self._runner.workflow_id}",
                "sk": f"RH#{new_run_id}",
                "_item_type": "WorkflowRunHistory",
                "gsi1pk": f"T#{self._runner.tenant_id}#WH",
                "gsi1sk": f"RH#{new_run_id}",
                "run_id": new_run_id,
                "parent_run_id": self._runner.run_id,
                "workflow_id": workflow_id,
                "workflow_version": workflow_version,
                "workflow_name": workflow_data["name"],
                "status": "queued",
                "start_time": datetime.utcnow().isoformat(),
            }
        )

    def iterator(
        self,
        array_path: list,
        actions: list[dict],
        iterator_input: Optional[dict] = None,
    ):
        if not isinstance(array_path, list):
            raise CoreActionFailure("The value for 'array_path' is not an array.")

        logger.debug({"message": "***** ITERATOR ARRAY *****", "item": array_path})

        for i in array_path:
            # TODO: Store iterator value in secure location for retrival by flexli_iterator_value()
            # TODO: Use `iterator_input` with an applied transform is provided
            logger.debug({"message": "***** ITERATOR ITEM *****", "item": i})

            iterator_runner = WorkflowRunnerV1(
                tenant_id=self._runner.tenant_id,
                workflow_id=self._runner.workflow_id,
                workflow_version=self._runner.workflow_version,
                run_id=str(ULID()),
                source_input=i,
                actions=copy.deepcopy(actions),
                parent_run_id=self._runner.run_id,
            )
            iterator_runner.run()

    def data(self, operation: str, scope: str, key: str, value, **kwargs):
        """Action data:
        {
          "type": "Flexli:CoreV1:Data",
          "parameters": {
            "operation": "read | write | query | increment | decrement",
            "scope": "account | workflow | run",
            "key": "value | expression",
            "value": "value | expression"
          },
          "variables": {
            "<name>": "value | expression"
          },
          "transform": {
            "<key>": "value | expression"
          }
        }
        """
        return {}

    @staticmethod
    def wait(seconds: Union[int, str], **kwargs):
        # TODO: Conditional based on the amount of time. < X use `sleep`, > X perform a callback
        time.sleep(int(seconds))
        return {}


class WorkflowRunnerV1:
    def __init__(
        self,
        tenant_id: str,
        workflow_id: str,
        workflow_version: int,
        run_id: str,
        source_input: dict,
        actions: list[dict],
        parent_run_id: Optional[str] = None,
    ):
        self.tenant_id = tenant_id
        self.workflow_id = workflow_id
        self.workflow_version = workflow_version

        # TODO: Temp fix for scheduled workflows - needs to create workflow run record
        self.run_id = run_id if run_id else ULID()

        self.parent_run_id = parent_run_id
        # self.run_name = f"{tenant_id}-{workflow_id}:{workflow_version}-{run_id}"

        self.run_history_ttl = int((datetime.utcnow() + timedelta(days=7)).timestamp())

        self.core_actions = FlexliCoreV1(runner=self)

        try:
            updates: dict = source_input["transform"]
        except KeyError:
            self.state = source_input
        else:
            self.state = transform(source=source_input, updates=updates)

        self.actions = sorted(actions, key=lambda i: i["order"])

        # Each workflow object gets its own session
        self._session = requests.Session()

    def get_next_action(self) -> dict:
        """Extract the next action from the internal actions list. This mutates the list.
        Catch "IndexError" to signal the actions have been depleted.
        """
        # TODO: Stop mutating the actions. Track the current `order` in class, get next, return action ref.
        return self.actions.pop(0)

    def log_workflow_history_update(
        self,
        status="running",
        action: dict = None,
        reason: Union[str, dict] = None,
        include_state: bool = True,
    ):
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds")

        item = {
            "pk": f"T#{self.tenant_id}#RH#{self.parent_run_id if self.parent_run_id else self.run_id}",
            "sk": f"TS#{timestamp}",
            "_item_type": "WorkflowRunHistoryUpdate",
            "status": status,
            "reason": reason,
            "time": timestamp + "Z",
            "ttl": self.run_history_ttl,
        }

        if self.parent_run_id:
            item["nested_run_id"] = self.run_id

        if action:
            item["action"] = {
                "connector_type": action.get("connector_type"),
                "order": action["order"],
                "type": action["type"],
            }

        if include_state:
            item["state"] = self.state

        workflow_history_v1_table.put_item(Item=item)

    @staticmethod
    def _action_auth_headers(credentials: dict) -> dict:
        # TODO: Should be a function that returns a type
        decrypted_credentials = kms_client.decrypt(
            CiphertextBlob=credentials["CiphertextBlob"].value,
            KeyId=credentials["KeyId"],
        )

        connector_credentials = json.loads(decrypted_credentials["Plaintext"])

        match connector_credentials["type"]:
            case "ApiKey":
                auth_header = {
                    connector_credentials["api_key_header"]: connector_credentials[
                        "api_key"
                    ]
                }
            case "BearerToken":
                auth_header = {
                    "Authorization": f"Bearer {connector_credentials['bearer_token']}"
                }
            case "OAuth2Client":
                # TODO: Not implemented
                # Cached request to obtain token and return
                auth_header = {"Authorization": "Bearer Token"}
            case _:
                raise Exception("Unsupported Auth Type")

        return auth_header

    def _run_action(self, action: dict, connector: dict) -> dict:
        request_args = {
            "method": action["method"],
            "url": posixpath.join(
                urlunparse(
                    (
                        "https",
                        connector["config"]["host"],
                        connector["config"].get("base_path"),
                        None,
                        None,
                        None,
                    )
                ),
                action["path"].strip("/"),
            ),
            "params": action.get("query"),
            "headers": {},
        }

        # Headers setup
        if (default_headers := connector["config"].get("default_headers")) is not None:
            request_args["headers"].update(default_headers)

        if (action_headers := action.get("headers")) is not None:
            request_args["headers"].update(action_headers)

        # Apply auth headers if credentials
        if action_credentials := connector.get("credentials"):
            request_args["headers"].update(
                self._action_auth_headers(action_credentials)
            )

        # Handle body content based on MIME type (needs a lot of work)
        if (body := action.get("body")) is not None:
            for k, v in request_args["headers"].items():
                if k.lower() == "content-type" and v.lower() == "application/json":
                    request_args["json"] = body
                    break
            else:
                request_args["body"] = body

        logger.debug(request_args)

        response = self._session.request(**request_args)

        logger.debug(
            {
                "status_code": response.status_code,
                "headers": response.headers,
                "body": response.text,
            }
        )

        response.raise_for_status()

        # TODO: Non-JSON HTTP APIs
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return {}

    def _run(self):
        while True:
            try:
                action = self.get_next_action()
            except IndexError:
                logger.debug("***** Workflow Run %s Complete *****", self.run_id)
                break

            # Log start of action - do I want to log the end of the action?
            self.log_workflow_history_update(action=action)
            logger.debug(action)

            if action_condition := action.get("condition"):
                if not ConditionEvaluator(action_condition).evaluate(self.state):
                    if (on_fail := action_condition.get("on_fail")) == "fail":
                        raise ConditionFailedFail(failed_action=action, exception=None)
                    elif on_fail == "stop":
                        raise ConditionFailedStop(failed_action=action, exception=None)
                    elif on_fail == "skip":
                        # Skip the remainder of this action and proceed to the next
                        continue

            # Prevent expression and string formatting on certain key-paths for core actions
            if action["type"] == "Flexli:CoreV1:Iterator":
                ignored_paths = ["actions"]
            else:
                ignored_paths = None

            # Parameters are processed from the workflow state
            prepared_action_params = transform(
                source=self.state,
                updates=action.get("parameters"),
                variables=action.get("variables"),
                ignored_paths=ignored_paths,
            )
            logger.debug(
                {"object": "prepared_action_params", "contents": prepared_action_params}
            )

            if action["type"].startswith("Flexli:CoreV1:"):
                logger.debug({"action_type": action["type"]})
                core_v1_action = action["type"].split(":")[-1].lower()
                action_response = getattr(self.core_actions, core_v1_action)(
                    **prepared_action_params
                )

            else:
                action_connector = read_connector_cached(
                    tenant_id=self.tenant_id,
                    connector_id=action["connector_id"],
                )

                # Find matching action
                for i in action_connector["actions"]:
                    if i["type"] == action["type"]:
                        connector_action = i
                        break
                else:
                    raise Exception("How did we not find a matching action??")

                logger.debug("***** ACTION CONNECTOR FROM LRU_CACHE CALL *****")
                logger.debug({k: str(v) for k, v in action_connector.items()})

                # The prepared action is processed from the prepared param
                # (also used for variable subs)
                prepared_action = transform(
                    source=prepared_action_params,
                    updates=connector_action,
                    variables=prepared_action_params,
                )
                logger.debug({"object": "prepared_action", "contents": prepared_action})

                try:
                    action_response = self._run_action(
                        action=prepared_action,
                        connector=action_connector,
                    )
                except Exception as error:
                    raise WorkflowFailed(failed_action=action, exception=error)

            if action.get("transform"):
                self.state = transform(
                    source=action_response,
                    target=self.state,
                    updates=action["transform"],
                )

    def run(self):
        try:
            self._run()
        except TransformError as error:
            logger.exception(error)
            self.log_workflow_history_update(
                status="failed",
                reason={
                    "message": f"The workflow encountered an error.",
                    "error": str(error),
                },
            )
        except ConditionFailedFail as error:
            logger.exception(error.exception)
            self.log_workflow_history_update(
                status="failed", reason="Action condition failed", include_state=False
            )
        except ConditionFailedStop as error:
            logger.exception(error.exception)
            self.log_workflow_history_update(
                status="stopped", reason="Action condition failed", include_state=False
            )
        except WorkflowFailed as error:
            logger.exception(error.exception)
            self.log_workflow_history_update(
                status="failed",
                action=error.failed_action,
                reason={
                    "message": f"The workflow encountered an error.",
                    "error": str(error.exception),
                    "response": error.exception.response.text,
                },
                include_state=False,
            )
        else:
            self.log_workflow_history_update(status="successful", include_state=False)
            # TODO: This needs to be an async process that also handles stopped/failed
            main_table.update_item(
                Key={
                    "pk": f"T#{self.tenant_id}#WH#{self.workflow_id}",
                    "sk": f"RH#{self.run_id}",
                },
                UpdateExpression="SET #st = :su, end_time = :ts",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":su": "successful",
                    ":ts": datetime.utcnow().isoformat(),
                },
            )


@tracer.capture_method
def run_workflow_handler(record: SQSRecord):
    # This is incompatible with multi-threading
    flexli_globals.reset()

    item: dict = json.loads(record.body)

    logger.info(
        {
            "tenant_id": item["tenant_id"],
            "workflow_id": item["workflow_id"],
            "workflow_version": item["workflow_version"],
            "run_id": item["run_id"],
        }
    )

    if not item.get("run_id"):
        item["run_id"] = str(ULID())

        # TODO: Move to database module
        main_table.put_item(
            Item={
                "pk": f"T#{item['tenant_id']}#WH#{item['workflow_id']}",
                "sk": f"RH#{item['run_id']}",
                "_item_type": "WorkflowRunHistory",
                "gsi1pk": f"T#{item['tenant_id']}#WH",
                "gsi1sk": f"RH#{item['run_id']}",
                "run_id": item["run_id"],
                "workflow_id": item["workflow_id"],
                "workflow_version": item["workflow_version"],
                "workflow_name": item["workflow_name"],
                "status": "running",
                "start_time": datetime.utcnow().isoformat(),
            }
        )

    runner = WorkflowRunnerV1(
        tenant_id=item["tenant_id"],
        workflow_id=item["workflow_id"],
        workflow_version=item["workflow_version"],
        run_id=item["run_id"],
        source_input=item.get("source_input", {}),
        actions=item["actions"],
        parent_run_id=item.get("parent_run_id"),
    )

    runner.run()


def lambda_handler(event, context: LambdaContext):
    """Notes:

    Queue source:

        {
            "tenant_id": "<Tenant ID>",
            "workflow_id": "<Workflow ID>",
            "run_id": "<Run ID>",
            "version": 1,
            "schema_version": 1,
            "source_input": {} | null,
            "actions": [<Action1>. <Action2>],
        }

    Translate to:

        {
            "tenant_id": <Tenant ID>,
            "workflow_id":  "<Workflow ID>",
            "state": {},
            "next_action": <Action1>,
            "remaining_actions: [<Action2>]
        }

    Initial `state` is optionally provided in the event/run request.
    If a source is present the `transform` will be applied to the run input.
    """
    # TODO: Future enhancement: multithread the batch.
    return process_partial_response(
        event=event,
        record_handler=run_workflow_handler,
        processor=processor,
        context=context,
    )
