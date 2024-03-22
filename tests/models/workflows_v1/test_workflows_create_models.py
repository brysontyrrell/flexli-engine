from src.workflows_api.workflows_v1.create.local import WorkflowsV1Create

from tests.models.workflows_v1.data import TEST_CREATE_WORKFLOW


def test_create_workflow():
    WorkflowsV1Create.model_validate(TEST_CREATE_WORKFLOW)
