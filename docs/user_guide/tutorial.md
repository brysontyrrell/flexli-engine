# Tutorial

This document is a guided walkthrough of using the Flexli Engine API to create a _**Connector**_ and a _**Workflow**_ that uses the actions defined in that connector. We will create a basic [Slack incoming webhook](https://api.slack.com/messaging/webhooks#posting_with_webhooks) connector and a workflow that sends a message to a channel.

## Creating the Connector

Every connector starts off with a `type`, `name`, and `description`. The type is a string of letters without spaces that acts as a descriptive identifier for the connector. Note that this is not a unique identifier. The name and description can be long-form and are intended for users of your connectors.

??? info "The `schema_version` is required and must be set to `1`."

    As Flexli Engine adopts new features that are not backwards compatible they will be exposed through a new schema version that you will need to migrate to."

```json title="Connector Description"
{
  "type": "SlackWebhook",
  "name": "Slack Incoming Webhook",
  "description": "A basic connector for sending messages to Slack Incoming Webhook URLs.",
  "schema_version": 1
}
```

### Configuration

The `config` contains the host and base path that are used for all _**Actions**_ that will be defined.

The `host` must be a fully qualified domain name without a scheme or path. HTTPS is enforced by the engine for all outbound connections. The `base_path` will be prepended to the `path` of every action defined in this connector. This base path value may be the API version (e.g. `v1`) or the API's path off the service host (e.g. `api`).

!!! note "The `base_path` is an optional value. Many of the properties described in this walkthrough are. Refer to then [API docs](https://brysontyrrell.github.io/flexli-engine/api) for a complete reference on required and optional properties."

The `default_headers` will also apply to every action, cutting down on the need to write repetitive definitions, but they may also be overridden in the action. A header of the same key name in an action will take precedence over the default.

This Slack webhook connector will be reusable across multiple webhooks. The common base path for all webhooks is `services`, and our requests must be JSON content.

```json title="Connector Configuration"
{
  "config": {
    "host": "hooks.slack.com",
    "base_path": "services",
    "default_headers": {
      "Accept": "application/json",
      "Content-Type": "application/json"
    }
  }
}
```

!!! question "What if?"

    What if you did not want this connector to be reusable, and instead only wanted it to be for a single channel? In that case the full path of the webhook could be hardcoded into the connector's configuration.

    Engine users still use the connector when authoring, but if they only have permissions to reading the connector's actions and events they would not have access to the configuration data. These single-purpose connectors can be used to simplify the workflow authoring experience in your account."

Slack's webhook integration is unauthenticated and credentials are not needed as a part of the connector. For APIs that require authentication you will need to add a `credentials` object conforming to one of the supported types. See [Authoring Connectors: Credentials](authoring/connectors.md#credentials) for more details.

### Adding an Action

A Slack webhook only allows for posting messages. This will be the only action included in our connector.

Actions are a description of an API operation. They are very similar in nature to OpenAPI's schema but without the hierarchical structure.

Like the connector, the action must have a `type` value that workflow authors will use to identify which actions they are using. For posting a message to a Slack channel only the `method`, `path`, and `body` properties need to be set for the action (remember, the `default_headers` are already setting the content type to JSON).

The [Slack documentation](https://api.slack.com/messaging/webhooks#posting_with_webhooks) shows the minimum requirement for a message is a JSON object with a single `text` key. This action is constructing that object as a part of the `body` so workflow authors only have to pass a string of text when they use it.

The `path` and inner `text` properties are both dynamically populated by inputs which are defined in the `parameters`. You can see they are using [_**Expressions**_](authoring/expressions.md) to make these references.

The parameters object uses JSON schema to create the workflow author's interface to this action. The `webhook` must be a string limited to 44 characters, and the `text` must also be a string with a limit of 2000 characters (conforming to Slack's API).

The schema defines the user interface when using connector actions. Users know exactly what data is required, what is optional, what types are allowed, and what their limitations are. The Workflows API enforces action schemas and will return detailed error messages to users.

!!! tip "A well-defined action schema results in a better user experience."

```json  
{
  "actions": [
    {
      "type": "PostMessage",
      "method": "post",
      "path": "::webhook",
      "body": {
        "text": "::text"
      },
      "parameters": {
        "properties": {
          "webhook": {
            "title": "Webhook Path",
            "type": "string",
            "maxLength": 44
          },
          "text": {
            "title": "Message Text",
            "maxLength": 2000,
            "type": "string"
          }
        },
        "required": [
          "webhook",
          "text"
        ]
      }
    }
  ]
}
```

When this action is used in a workflow, the values that the author sets for `webhook` and `text` will be passed into the `path` and `body`. Workflow authors do not see any of the implementation details beyond parameters. Connector actions can be as simple or complex as is required for the operation they expose.

### Create the Connector

The JSON definition of this connector will be passed to the [**_Create a Connector_**](https://brysontyrrell.github.io/flexli-engine/api/#tag/Connectors/paths/~1v1~1connectors/post) API. A success response will include the unique ID of the connector that will be used in workflows.

```json title="Connector Created Response"
{
  "id": "01HP21BX1MCA5T8EDBGBZ3JTSR",
  "href": "/v1/connectors/01HP21BX1MCA5T8EDBGBZ3JTSR"
}
```

A connector definition should be reusable within the same account as many times as needed. While multiple instances will share the same `type` they will all have different IDs.

??? example "View the complete Slack Incoming Webhook Connector"

    ```json
    {
      "type": "SlackWebhook",
      "name": "Slack Incoming Webhook",
      "description": "A basic connector for sending messages to Slack Incoming Webhook URLs.",
      "schema_version": 1,
      "config": {
        "host": "hooks.slack.com",
        "base_path": "services",
        "default_headers": {
          "Accept": "application/json",
          "Content-Type": "application/json"
        }
      },
      "actions": [
        {
          "type": "PostMessage",
          "method": "post",
          "path": "::webhook",
          "body": {
            "text": "::text"
          },
          "parameters": {
            "properties": {
              "webhook": {
                "title": "Webhook Path",
                "type": "string",
                "maxLength": 44
              },
              "text": {
                "title": "Message Text",
                "maxLength": 2000,
                "type": "string"
              }
            },
            "required": [
              "webhook",
              "text"
            ]
          }
        }
      ]
    }
    ```

## Creating the Workflow

Now that we have a connector we can use its actions within a workflow.

Workflows can be described with their `name` and an optional `description` similar to connectors. These values can be long-form and are intended for operators.

??? info "The `schema_version` is required and must be set to `1`."

    As Flexli Engine adopts new features that are not backwards compatible they will be exposed through a new schema version that you will need to migrate to."

```json
{
  "name": "Hello Slack",
  "description": "A \"hello world\" example workflow.",
  "schema_version": 1
}
```

### Using an Action

Workflows must contain at least 1 action (but con contain up to 100). Each action is defined as an object within the `actions` array.

The `connector_id` will be the ID value of the connector this action references. Then the `type` states which action in that connector will be used.

!!! note "Note that the connector's `type` value is not used here. It will be inferred on creation when the Workflows API validates the definition."

The `order` is a numeric value that determines the sequence that actions in the workflow are executed. This value can be any integer, and while the values across all your actions must be unique they do not need to be contiguous. You could have three actions defined and their orders are 10, 20, and 30 respectively.

```json
{
  "actions": [
    {
      "connector_id": "<ConnectorId>",
      "type": "PostMessage",
      "order": 1,
      "parameters": {
        "webhook": "T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
        "text": "Hello from Flexli!"
      }
    }
  ]
}
```

The `pqrameters` are determined entirely by the schema of the connector action's definition. Remember in our example Slack connector the `PostMessage` action requires two parameters: a `webhook` string limited to 44 characters, and a `text` string limited to 2000 characters. If the parameters here do not pass validation by the Workflows API it will be rejected.

??? example "View the complete Hello Slack Workflow"

    ```json
    {
      "name": "Hello Slack",
      "description": "A \"hello world\" example workflow.",
      "schema_version": 1,
      "actions": [
        {
          "connector_id": "<ConnectorId>",
          "type": "PostMessage",
          "order": 1,
          "parameters": {
            "webhook": "T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
            "text": "Hello from Flexli!"
          }
        }
      ]
    }
    ```

### Create the Workflow

The JSON definition of this connector will be passed to the [**_Create a Workflow_**](https://brysontyrrell.github.io/flexli-engine/api/#tag/Workflows/paths/~1v1~1workflows/post) API. A success response will include the unique ID of the workflow that can be used to run it with the Run API (and other methods as well!).

```json title="Workflow Created Response"
{
  "id": "01HP22FG2C15KF3EKB92VH8WFQ",
  "href": "/v1/workflows/01HP22FG2C15KF3EKB92VH8WFQ"
}
```
