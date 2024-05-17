from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, conint, conlist, constr, field_validator

from shared_models.workflows_v1_write import (
    CoreV1Sources,
    WorkflowsV1WriteAction,
    WorkflowsV1WriteCoreV1Actions,
    WorkflowsV1WriteEventSource,
    WorkflowV1WriteWorkflowOnError,
)


class WorkflowsV1Create(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: constr(
        strip_whitespace=True, pattern="^[a-zA-Z0-9 ]+$", min_length=3, max_length=60
    )
    description: Optional[str] = None
    schema_version: Literal[1]
    enabled: bool = True
    timeout: Optional[conint(gt=0, lt=901)] = None
    on_error: Optional[WorkflowV1WriteWorkflowOnError] = None
    source: Optional[Union[CoreV1Sources, WorkflowsV1WriteEventSource]] = None
    actions: conlist(
        Union[WorkflowsV1WriteCoreV1Actions, WorkflowsV1WriteAction],
        min_length=1,
        max_length=100,
    )

    @field_validator("actions")
    def validate_actions_order_values(cls, v):
        # assert len(v) <= 100, "Cannot define more than 100 actions"
        assert len(order_ids := [i.order for i in v]) == len(
            set(order_ids)
        ), "Action order values must be unique"
        return v
