from src.workflows_api.connectors_v1.list.local import ConnectorsV1List

from tests.models.connectors_v1.data import TEST_LIST_CONNECTOR


def test_list_connector():
    ConnectorsV1List(**{"items": [TEST_LIST_CONNECTOR]})
