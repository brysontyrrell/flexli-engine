import copy
from functools import lru_cache
import json
import os
from typing import Iterator

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSEvent, SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from boto3.dynamodb.conditions import Key
from ulid import ULID

from apis.models import DecimalEncoder
from aws_utils import get_boto3_client, get_boto3_resource
from conditions import ConditionEvaluator
from transforms import transform

from local import Event, EventToSend

MAIN_TABLE_NAME = os.environ["MAIN_TABLE_NAME"]
RUN_QUEUE_URL = os.environ["RUN_QUEUE_URL"]

logger = Logger()
tracer = Tracer()

main_table = get_boto3_resource("dynamodb").Table(MAIN_TABLE_NAME)
sqs_client = get_boto3_client("sqs")


class EventProcessor:
    def __init__(self, records: Iterator[SQSRecord]):
        """
        For each event:
        - Get type, query all workflows with sources matched to the type
            -> Cache workflows to prevent repeat, duplicate reads
            -> Discard event if there are no workflows that source it
        - Evaluate workflow's source condition if present
            -> Discard if condition is present and fails
            -> A condition failure is not a SQS item failure
        - Apply transform if present
            -> A transform failure is not a SQS item failure
        - Add to internal list of runs to be batched to SQS
        - Process batches to SQS
        """
        self.records = records

        self.events_to_send: list[EventToSend] = []

        self.failed_item_ids: list[str] = []

    @lru_cache
    def _query_workflows_for_tenant(
        self, tenant_id: str, connector_id: str, event_type: str
    ) -> list[dict]:
        response = main_table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("gsi1pk").eq(f"T#{tenant_id}#C#{connector_id}")
            & Key("gsi1sk").eq(f"E#{event_type}"),
        )

        return response["Items"]

    def get_workflows_for_event_type(
        self, tenant_id: str, connector_id: str, event_type: str
    ) -> list[dict]:
        return self._query_workflows_for_tenant(
            tenant_id=tenant_id, connector_id=connector_id, event_type=event_type
        )

    def evaluate_events(self):
        for record in self.records:
            logger.debug(record)
            try:
                logger.debug(dir(record))
                event = Event(**record.json_body)
            except:
                logger.exception(f"Failed to parse event: %s", record.raw_event)
                self.failed_item_ids.append(copy.copy(record.message_id))
                continue

            logger.debug(event)

            for workflow in self.get_workflows_for_event_type(
                tenant_id=event.tenant_id,
                connector_id=event.connector_id,
                event_type=event.event_type,
            ):
                # Workflows returned in this query are guaranteed to have `source` objects.
                # if workflow_source := workflow.get("source"):
                if source_condition := workflow["source"].get("condition"):
                    if not ConditionEvaluator(source_condition).evaluate(event.data):
                        logger.info(
                            "Workflow %s source condition failed for event %s",
                            workflow["id"],
                            event.id,
                        )
                        continue

                # TODO: Optimize for memory use (only store unique workflows once)
                self.events_to_send.append(EventToSend(workflow=workflow, event=event))

    def send_events_to_run_queue(self):
        # TODO: Optimize for SQS batching
        for event in self.events_to_send:
            if event.workflow["source"].get("transform"):
                logger.debug("***** RUNNING SOURCE TRANSFORM *****")
                source_input = transform(
                    source=event.event.data,
                    updates=event.workflow["source"]["transform"],
                )
            else:
                source_input = event.event.data

            logger.debug(source_input)
            new_run_id = str(ULID())  # TODO: Should this be upstream?
            sqs_client.send_message(
                QueueUrl=RUN_QUEUE_URL,
                MessageBody=json.dumps(
                    {
                        "tenant_id": event.event.tenant_id,
                        "workflow_id": event.workflow["id"],
                        "workflow_version": event.workflow["version"],
                        "run_id": new_run_id,
                        "source_input": source_input,
                        "actions": event.workflow["actions"],
                    },
                    cls=DecimalEncoder,
                ),
            )

    def sqs_batch_failures(self) -> dict:
        return {
            "batchItemFailures": [{"itemIdentifier": i} for i in self.failed_item_ids]
        }


@event_source(data_class=SQSEvent)
def lambda_handler(event: SQSEvent, context: LambdaContext):
    """Process large batches of events, query for workflows subscribed to those events, and evaluate
    the conditions before batching to the run queues.

    Each SQS record will be an event following the CloudEvents spec:

        {
            "specversion" : "1.0",
            "type" : "<?Namespace>:<ConnectorType>:<SourceType>",
            "source" : "<Provider>.<Service>",
            "id" : "<EventId>",
            "tenantid": "<TenantId>",  # Extended attribute
            "connectorid": "<ConnectorId>",  # Extended attribute
            "time" : "<ISO 8601 Timestamp>",
            "datacontenttype" : "application/json",
            "data" : "{}"
        }

    Event examples:

        {
            "specversion" : "1.0",
            "type" : "MyConnector:MyEventType",
            "source" : "flexli.events-api",
            "id" : "01HEXYPRM99QFXBY4W9622CE6Y",
            "tenantid": "01HBCG5JPKYV1XQ1J2TPJNY94M",
            "connectorid": "01HEQWYRRB2TBA9HMB52ZN85BD",
            "time" : "2023-11-11T05:20:05.251Z",
            "datacontenttype" : "application/json",
            "data" : "{}"
        }

        {
            "specversion" : "1.0",
            "type" : "Flexli:CoreV1:MyCustomEvent",
            "source" : "flexli.workflow",
            "id" : "01HEYDEWGEGSBQSJFT2JB2XCZR",
            "tenantid": "01HBCG5JPKYV1XQ1J2TPJNY94M",
            "connectorid": "Flexli",
            "time" : "2023-11-11T05:24:38.524Z",
            "datacontenttype" : "application/json",
            "data" : "{}"
        }
    """
    logger.debug(event)
    processor = EventProcessor(records=event.records)

    processor.evaluate_events()
    logger.debug(processor.events_to_send)

    processor.send_events_to_run_queue()

    return processor.sqs_batch_failures()
