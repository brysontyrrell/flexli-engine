from src.resources.events_processor_v1.local import Event


def test_event_model_connector():
    event_data = {
        "specversion": "1.0",
        "type": "MyConnector:MyEventType",
        "source": "flexli.events-api",
        "id": "01HEXYPRM99QFXBY4W9622CE6Y",
        "tenantid": "01HBCG5JPKYV1XQ1J2TPJNY94M",
        "connectorid": "01HEQWYRRB2TBA9HMB52ZN85BD",
        "time": "2023-11-11T05:20:05.251Z",
        "datacontenttype": "application/json",
        "data": '{"foo": "bar"}',
    }

    event_model = Event(**event_data)

    assert event_model.data == {"foo": "bar"}
    assert event_model.connector_type == "MyConnector"
    assert event_model.event_type == "MyEventType"


def test_event_model_core():
    event_data = {
        "specversion": "1.0",
        "type": "Flexli:CoreV1:MyCustomEvent",
        "source": "flexli.workflow",
        "id": "01HEYDEWGEGSBQSJFT2JB2XCZR",
        "tenantid": "01HBCG5JPKYV1XQ1J2TPJNY94M",
        "connectorid": "Flexli",
        "time": "2023-11-11T05:24:38.524Z",
        "datacontenttype": "application/json",
        "data": "{}",
    }

    event_model = Event(**event_data)

    assert event_model.data == {}
    assert event_model.connector_type == "Flexli:CoreV1"
    assert event_model.event_type == "MyCustomEvent"
