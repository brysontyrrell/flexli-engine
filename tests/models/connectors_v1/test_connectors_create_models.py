from src.workflows_api.connectors_v1.create.local import ConnectorV1Create

from tests.models.connectors_v1.data import TEST_CREATE_CONNECTOR


def test_create_connector():
    ConnectorV1Create(**TEST_CREATE_CONNECTOR)
