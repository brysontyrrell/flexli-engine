#!/usr/bin/env python3
from inspect import isclass
from pathlib import Path
import json
import subprocess
import sys

# import pydantic
import pydantic.v1

sys.path.append("src/layers/layer")

from src.layers.layer.apis.models import ApiErrorResponse, CreatedResponse

from src.workflows_api.connectors_v1.create.local import ConnectorV1Create
from src.workflows_api.connectors_v1.read.local import ConnectorV1Read
from src.workflows_api.connectors_v1.list.local import ConnectorsV1List

from src.workflows_api.workflows_v1.create.local import WorkflowsV1Create
from src.workflows_api.workflows_v1.list.local import WorkflowsList

from src.workflows_api.workflow_versions_v1.read.local import WorkflowsV1Read

from src.workflows_api.run_history_v1.list.local import RunV1List
from src.workflows_api.run_history_v1.list_id.local import RunHistoryV1List

CURRENT_DIR = Path().absolute()
SCHEMAS_DIR = CURRENT_DIR / "docs" / "api" / "_schemas"

if not SCHEMAS_DIR.exists():
    SCHEMAS_DIR.mkdir(parents=True)


models_to_convert = [
    ApiErrorResponse,
    CreatedResponse,
    ConnectorV1Create,
    ConnectorV1Read,
    ConnectorsV1List,
    WorkflowsV1Create,
    WorkflowsList,
    WorkflowsV1Read,
    RunV1List,
    RunHistoryV1List,
]

for model in models_to_convert:
    if (
        isclass(model)
        and issubclass(model, pydantic.BaseModel | pydantic.v1.BaseModel)
        and (model_name := model.__name__) not in pydantic.__dict__.keys()
    ):
        print(f"Generating schema for {model_name}")
        with open(SCHEMAS_DIR / f"{model_name}.json", "w") as fobj:
            if issubclass(model, pydantic.BaseModel):
                fobj.write(json.dumps(model.model_json_schema(), indent=4))
            elif issubclass(model, pydantic.v1.BaseModel):
                fobj.write(model.schema_json(indent=4))


print("Pulling latest image for 'redocly/cli'...")
subprocess.call(["docker", "pull", "redocly/cli"])

print("Generating OpenAPI docs...")
subprocess.call(
    [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{CURRENT_DIR}:/spec",
        "redocly/cli",
        "build-docs",
        "docs/api/openapi.yaml",
        "--output",
        # "build/docs/api/index.html",
        "docs/api/index.html",
    ]
)
