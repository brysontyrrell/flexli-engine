import copy

TEST_CREATE_CONNECTOR = {
    "type": "MyTestApi",
    "name": "Test API Connector",
    "description": "A connector for PyTest.",
    "schema_version": 1,
    "config": {
        "host": "test.service.com",
        "base_path": "api",
        "credentials": {
            "type": "ApiKey",
            "api_key": "my-api-key",
            "api_key_header": "x-api-key",
        },
        "default_headers": {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    },
    "actions": [
        {
            "type": "PostOperation",
            "name": "Get a resource",
            "method": "post",
            "path": "{resource_name}",
            "parameters": {"properties": {"resource_name": {"type": "string"}}},
        },
        {
            "type": "GetOperation",
            "name": "Get a resource",
            "method": "get",
            "path": "{resource_name}/{resource_id}",
            "parameters": {
                "properties": {
                    "resource_name": {"type": "string"},
                    "resource_id": {"type": "number"},
                }
            },
        },
    ],
}

TEST_READ_CONNECTOR = copy.deepcopy(TEST_CREATE_CONNECTOR)
TEST_READ_CONNECTOR.update({"id": "01HFB7GJ5SWS498E1KGRQB8E7Z", "version": 1})

TEST_LIST_CONNECTOR = {
    "id": "01HFB7GJ5SWS498E1KGRQB8E7Z",
    "type": "MyTestApi",
    "schema_version": 1,
    "version": 1,
    "name": "Test API Connector",
    "description": "A connector for PyTest.",
    "events": [],
    "actions": [a["type"] for a in TEST_CREATE_CONNECTOR["actions"]],
}
