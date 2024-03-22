from tests.models.run_history_v1.data import (
    TEST_RUN_HISTORY_LIST,
    TEST_RUN_HISTORY_DETAILS,
)

from src.workflows_api.run_history_v1.list.local import QueryStringParams, RunV1List
from src.workflows_api.run_history_v1.list_id.local import (
    QueryStringParams,
    RunHistoryV1List,
)


def test_run_list():
    RunV1List.model_validate({"items": [TEST_RUN_HISTORY_LIST]})


def test_run_history_list():
    RunHistoryV1List.model_validate(TEST_RUN_HISTORY_DETAILS)
