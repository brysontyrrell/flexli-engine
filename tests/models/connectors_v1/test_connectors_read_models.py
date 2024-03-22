from src.workflows_api.connectors_v1.read.local import ConnectorV1Read

from tests.models.connectors_v1.data import TEST_READ_CONNECTOR


def test_read_connector():
    ConnectorV1Read(**TEST_READ_CONNECTOR)
