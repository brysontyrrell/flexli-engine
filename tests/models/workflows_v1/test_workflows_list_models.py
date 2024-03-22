import pytest

from pydantic import ValidationError

from src.workflows_api.workflows_v1.list.local import QueryStringParams, WorkflowsList

from tests.models.workflows_v1.data import TEST_LIST_WORKFLOW


def test_list_workflow_query_string_params():
    QueryStringParams.model_validate(
        {"id": "01HFB7GJ5SWS498E1KGRQB8E7Z", "is_release_version": ""}
    )

    QueryStringParams.model_validate({"id": "01HFB7GJ5SWS498E1KGRQB8E7Z"})

    QueryStringParams.model_validate({"is_release_version": "something"})

    with pytest.raises(ValidationError, match="Invalid resource ID"):
        QueryStringParams.model_validate({"id": "abc123"})


def test_list_workflow():
    WorkflowsList.model_validate({"items": [TEST_LIST_WORKFLOW]})
