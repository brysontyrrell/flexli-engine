import copy

TEST_CREATE_WORKFLOW = {
    "name": "Test Workflow",
    "schema_version": 1,
    "actions": [
        {
            "connector_id": "01HFB7GJ5SWS498E1KGRQB8E7Z",
            "order": 1,
            "type": "PostOperation",
            "description": "Use the PostOperation action",
            "parameters": {"resource_name": "notes"},
        }
    ],
}

TEST_READ_WORKFLOW = copy.deepcopy(TEST_CREATE_WORKFLOW)
TEST_READ_WORKFLOW.update(
    {
        "id": "01HC5YRPEXKXTDH64JWCD4QMY2",
        "version": 1,
        "is_release_version": True,
        "enabled": True,
    }
)
TEST_READ_WORKFLOW["actions"][0].update({"connector_type": "MyTestApi"})

TEST_LIST_WORKFLOW = {
    "id": "01HFB7GJ5SWS498E1KGRQB8E7Z",
    "schema_version": 1,
    "version": 1,
    "is_release_version": True,
    "name": "Test Workflow",
}
