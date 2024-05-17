from decimal import Decimal
from typing import Annotated, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    conint,
    conlist,
    constr,
    field_validator,
    model_validator,
)

from conditions.models import Condition, OnFailOptions

# CORE V1 SOURCES


class CoreV1CustomEventSourceParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str


class CoreV1CustomEventSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Flexli:CoreV1:CustomEvent"]
    condition: Optional[Condition] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    parameters: CoreV1CustomEventSourceParams


CRON_REGEX = r"^(?:([0-9]|[1-5][0-9])|[*]) (?:[0-9]|1[0-9]|2[0-3]|[*]) (?:[1-9]|[12][0-9]|3[01]|[*]) (?:[1-9]|1[0-2]|[*]) (?:[1-7]|[*?])$"
RATE_REGEX = r"^\d+ (?:minute|minutes|hour|hours|day|days)$"


class CoreV1ScheduleParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # TODO: ? https://github.com/vcoder4c/cron-validator
    cron: Optional[constr(pattern=CRON_REGEX)] = None
    rate: Optional[constr(pattern=RATE_REGEX)] = None

    @model_validator(mode="before")
    def cron_or_rate(cls, values):
        if not (values.get("cron") or values.get("rate")):
            raise ValueError("Must set one of 'cron' or 'rate'")
        elif values.get("cron") and values.get("rate"):
            raise ValueError("Can only set one of 'cron' or 'rate'")
        return values


class CoreV1Schedule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Flexli:CoreV1:Schedule"]
    parameters: CoreV1ScheduleParams


CoreV1Sources = Annotated[
    Union[CoreV1CustomEventSource, CoreV1Schedule],
    Field(discriminator="type"),
]


class WorkflowsV1WriteEventSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector_id: str
    type: constr(pattern="^[a-zA-Z0-9]+$")
    # TODO: 'condition.on_fail' is ignored for sources
    condition: Optional[Condition] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


# WORKFLOW V1 ACTION


class WorkflowV1WriteActionOnErrorBackoff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wait: Optional[int] = 3
    rate: Optional[float] = 1.5


class WorkflowV1WriteActionOnError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_retries: conint(gt=0, lt=11)
    retry_on: Optional[list[str]] = None
    on_fail: Optional[OnFailOptions] = None
    backoff: Optional[WorkflowV1WriteActionOnErrorBackoff] = None


class WorkflowsV1WriteAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connector_id: str
    type: constr(pattern="^[a-zA-Z0-9]+$")
    description: Optional[str] = None
    order: conint(gt=0, lt=101)
    condition: Optional[Condition] = None
    timeout: Optional[conint(gt=0, lt=121)] = 3
    on_error: Optional[WorkflowV1WriteActionOnError] = None
    wait_for_callback: bool = True
    parameters: Optional[dict] = None
    variables: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    # TODO: `on_fail` for Actions (example: handle a 404 error)


# CORE V1 ACTIONS


class CoreV1Transform(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Flexli:CoreV1:Transform"]
    description: Optional[str] = None
    order: conint(gt=0, lt=101)
    condition: Optional[Condition] = None
    variables: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


class CoreV1WaitParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seconds: int


class CoreV1Wait(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Flexli:CoreV1:Wait"]
    description: Optional[str] = None
    order: conint(gt=0, lt=101)
    condition: Optional[Condition] = None
    parameters: CoreV1WaitParams
    variables: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


class CoreV1CustomEventParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    content_type: Optional[str] = None  # TODO: Allowed mimetypes
    body: Optional[Union[dict, str]] = None

    @model_validator(mode="before")
    def content_type_and_body_required(cls, values):
        if (values.get("content_type") and not values.get("body")) or (
            values.get("body") and not values.get("content_type")
        ):
            raise ValueError(
                "'content_type' and 'body' are both required if either is provided"
            )
        return values


class CoreV1CustomEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Flexli:CoreV1:CustomEvent"]
    description: Optional[str] = None
    order: conint(gt=0, lt=101)
    condition: Optional[Condition] = None
    parameters: CoreV1CustomEventParams
    variables: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


class CoreV1RunWorkflowParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    workflow_version: int
    # TODO: Accept string IF it is an expression
    workflow_input: dict


class CoreV1RunWorkflow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Flexli:CoreV1:RunWorkflow"]
    description: Optional[str] = None
    order: conint(gt=0, lt=101)
    condition: Optional[Condition] = None
    # timeout: Optional[conint(gt=0, lt=901)] = None  # Max timeout equals workflow timeout IF wait_for_callback = True
    # on_error: Optional[] = None  # These should be the WorkflowOnError options
    wait_for_callback: bool = True
    parameters: CoreV1RunWorkflowParams
    variables: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


class CoreV1IteratorParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # This must be a JMESPath expression that returns the array to iterate over
    array_path: str
    iterator_input: Optional[dict] = None
    # Iterators cannot be nested in and Iterator.
    actions: conlist(
        Union[
            Annotated[
                Union[
                    CoreV1Transform,
                    CoreV1Wait,
                    CoreV1RunWorkflow,
                    CoreV1CustomEvent,
                ],
                Field(discriminator="type"),
            ],
            WorkflowsV1WriteAction,
        ],
        min_length=1,
        max_length=100,
    )

    # TODO: Reusable validator
    @field_validator("actions")
    def validate_iter_actions_order_values(cls, v):
        # assert len(v) <= 100, "Cannot define more than 100 actions"
        assert len(order_ids := [i.order for i in v]) == len(
            set(order_ids)
        ), "Action order values must be unique"
        return v


class CoreV1Iterator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Flexli:CoreV1:Iterator"]
    description: Optional[str] = None
    order: conint(gt=0, lt=101)
    condition: Optional[Condition] = None
    parameters: CoreV1IteratorParams
    variables: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    # transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


class CoreV1BranchItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = None
    order: conint(gt=0, lt=101)
    condition: Optional[Condition] = None
    actions: conlist(
        Union[
            Annotated[
                Union[
                    CoreV1Transform,
                    CoreV1Wait,
                    CoreV1RunWorkflow,
                    CoreV1CustomEvent,
                    CoreV1Iterator,
                ],
                Field(discriminator="type"),
            ],
            WorkflowsV1WriteAction,
        ],
        min_length=1,
        max_length=100,
    )


class CoreV1BranchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branches: conlist(CoreV1BranchItem, min_length=1, max_length=100)


class CoreV1Branch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Flexli:CoreV1:Branch"]
    description: Optional[str] = None
    order: conint(gt=0, lt=101)
    condition: Optional[Condition] = None
    parameters: CoreV1BranchParams
    variables: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None
    transform: Optional[dict[str, Union[StrictBool, Decimal, int, str]]] = None


WorkflowsV1WriteCoreV1Actions = Annotated[
    Union[
        CoreV1Transform,
        CoreV1Wait,
        CoreV1RunWorkflow,
        CoreV1CustomEvent,
        CoreV1Iterator,
        CoreV1Branch,
    ],
    Field(discriminator="type"),
]


class WorkflowV1WriteWorkflowOnErrorBackoff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wait: Optional[int] = 30
    rate: Optional[float] = 2.5


class WorkflowV1WriteWorkflowOnError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_retries: conint(gt=0, lt=11)
    retry_on: Optional[list[str]] = None
    backoff: Optional[WorkflowV1WriteWorkflowOnErrorBackoff] = None
