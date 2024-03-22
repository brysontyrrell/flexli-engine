from src.workflows_api.workflow_versions_v1.read.local import WorkflowsV1Read

from tests.models.workflows_v1.data import TEST_READ_WORKFLOW


def test_read_workflow():
    WorkflowsV1Read(**TEST_READ_WORKFLOW)
