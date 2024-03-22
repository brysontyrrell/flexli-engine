# Authoring Connectors

A connector provides the interface for a workflow to call an API. In addition to basic configuration details like the host and credentials, connectors define the source events and actions. Actions can be written to map 1:1 with an OpenAPI document, or be refined to curated interfaces that require only a few inputs when authoring workflows.

!!! note "All connectors must set their `schema_version` to `1`."

!!! info "Flexli Engine currently only supports APIs that accept and return JSON content over HTTPS."

## Configuration

The configuration of a workflow includes connection settings, default headers, and the credentials to use when workflows need to authenticate.

### Host and Base Path

The `host` should be the FQDN to the API. Connectors support _**only**_ HTTPS connections. There is no option to set or override the scheme.

The `base_path` can be used to provide a common starting path for all actions. For example, if the api you are writing a connector to starts all routes with `/api` you would add `api` as the base path value and then all actions would not have to include it.

### Default Headers

The default headers are key-value pairs that will be used in every action. This is usually the content types:

```json title="Example Default Headers"
{
  "config": {
    "default_headers": {
      "Accept": "application/json",
      "Content-Type": "application/json"
    }
  }
}
```

Any headers set in `default_headers` can be overridden by individual actions.

### Credentials

Flexli Engine supports three types of credentials for connectors:

#### Bearer Token

The bearer token represents a static, long-lived access token (like a JWT) that is used in a `Authorization: Bearer ...` header.

```json title="Bearer Token Credentials Example"
{
  "config": {
    "credentials": {
      "type": "BearerToken",
      "bearer_token": "<Token>"
    }
  }
}
```

#### API Key

The API key represents a static, long-lived secret that is used in a custom header location (e.g. `x-api-key`).

```json title="API Key Credentials Example"
{
  "config": {
    "credentials": {
      "type": "ApiKey",
      "api_key": "<Key>",
      "api_key_header": "<HeaderName>"
    }
  }
}
```

#### OAuth2 Client Credentials

When using OAuth2 client credentials, Flexli Engine will cache generated access tokens for the duration of the lifetime for use across all workflow runs to minimize authentication requests.

The `basic_auth` setting controls how the credentials are used when requesting access tokens. If `true` the client ID and secret are passed in a HTTP basic auth header. If `false` the request is form encoded.

```json title="OAuth2 Client Credentials Example"
{
  "config": {
    "credentials": {
      "type": "OAuth2Client",
      "client_id": "<ClientId>",
      "client_secret": "<ClientSecret>",
      "token_url": "<Oauth2TokenUrl>",
      "basic_auth": true
    }
  }
}
```

## Defining Events

!!! info "Flexli Engine Events are still in development and subject to change."

The _**Events API**_ allows for the ingest of events from external sources to automate workflow runs. To connect those events to your workflows they must be defined as part of a connector.

At a minimum you only need to define the `type` of the event. The event data can be optionally validated using the `schema` and a JSON Schema object. Validation prevents bad or incomplete data for an event type from reaching your workflows and causing failures.

```json title="Example Connector Event"
{
  "events": [
    {
      "type": "MyEvent",
      "schema": {
        "properties": {
          "type": "object"
        }
      }
    }
  ]
}
```

!!! note "The `schema` is only intended to validate incoming data. Filtering events based on criteria should be done using [_**Conditions**_](workflows.md#conditions). in the workflow definition"

### Signing Events

Events use HMAC 256 signatures for verification. The signing key can be retrieved using an API that generates a new signing key when called (invalidating the previous key).

!!! warning "You cannot retrieve the signing key again after it is created."

The Events API requires two custom headers for all requests. The `Flexli-Timestamp` will be the timestamp (seconds since epoch) when the event is sent (producer generated) and `Flexli-Signature` which will be the HMAC 256 signature of the request. The signature is a combination of the timestamp and request body signed using the signing key. All strings must be UTF-8 encoded.

```python title="Event Signing Example: Python"
import hashlib
import hmac

secret_key = '7930efb37ac4846f3df4c1a3522e8e27'
event_timestamp = '1688782099'
event_body = '{"type": "MyCustomEvent", "foo": "bar", "baz": true}'

signature = hmac.new(
    key=secret_key.encode('utf-8'),
    msg=(event_timestamp + ":" + event_body).encode('utf-8'),
    digestmod=hashlib.sha256
).hexdigest()
```

Here is an example of the headers for the content above. The signature must be prefixed with the version of the signing method used (`sha256v1`).

```text
Flexli-Timestamp: 1688782099
Flexli-Signature: sha256v1:65ef9ab3c247e83b1aaab2f963e791552ff63a58e3d67ff189efa58d6b1e4433
```

## Defining Actions

In a connector, the actions define and limit what operations can be used in a workflow. Actions can be loosely defined allowing a lot of flexibility by workflow authors, but requiring greater knowledge of underlying API operation. Actions can also be tightly defined with strict interfaces that take away guesswork but create a very narrow interface to the operation. Consider the target audience for the connector when defining actions.

!!! info "In a future update a utility for converting OpenAPI documents to a connector definitions will be released."

### Parameters

The _**Parameters**_ section is a JSON schema object where you define the user interface to the action when used in a workflow. This schema can act as a form or a validator (even using the same OpenAPI schema as the corresponding API operation) preventing a workflow from being saved that doesn't conform to the requirements of the action. The API response will contain a detailed error message that lists all the validation errors.

Take this example action that retrieve a system by an ID:

```json title="Example Connector Action"
{
  "actions": [
    {
      "type": "GetSystemById",
      "name": "Get a System record by ID",
      "method": "get",
      "path": "systems/{system_id}",
      "parameters": {
        "properties": {
          "system_id": {
            "type": "string"
          }
        }
      }
    }
  ]
}
```

The `path` uses the `system_id` as a string variable. In the connector definition the variable substitution and expressions are defined but only take effect when used in a workflow.

Here is that action being used in a workflow:

```json title="Example Action Use in a Workflow"
{
  "actions": [
    {
      "connector_id": "<ConnectorId>",
      "type": "GetSystemById",
      "order": 1,
      "parameters": {
        "system_id": "::system_id"
      }
    }
  ]
}
```

Note that the only data required is the unique ID of the connector, the action's type, and the parameter defined by the action. The `system_id` is being reference by expression from the workflow state.

Let's look at another more complex example:

```json title="Example Connector Action"
{
  "actions": [
    {
      "type": "ManageSystemGroupMembership",
      "name": "Add or remove a System from a System Group",
      "method": "post",
      "path": "v2/systemgroups/{group_id}/members",
      "body": {
        "id": "::system_id",
        "op": "::operation",
        "type": "system"
      },
      "parameters": {
        "properties": {
          "group_id": {
            "type": "string"
          },
          "operation": {
            "type": "string",
            "enum": ["add", "remove"]
          },
          "system_id": {
            "type": "string"
          }
        }
      }
    }
  ]
}
```

These parameters include an `enum` to restrict the valid options, and two of them are being references as expressions in the `body` which is a JSON object itself.

Here is the action being used in a workflow:

```json title="Example Action Use in a Workflow"
{
  "actions": [
    {
      "connector_id": "<ConnectorId>",
      "order": 1,
      "type": "ManageSystemGroupMembership",
      "parameters": {
        "group_id": "<GroupId>",
        "operation": "add",
        "system_id": "::system_id"
      }
    }
  ]
}
```

Again, the use of this operation is simplified for the workflow author as only the key values are required for input. The `system_id` is again being reference by expression from the workflow state, but the `group_id` and `operation` are hardcoded as a part of the action.

!!! note "There may be API operations that can be represented by multiple actions where certain attribute values are fixed. While this makes for a more verbose connector definition it can also yield a more positive experience for workflow authors as they can determine what to use solely by the `type` and `description`."

It may be desirable to have connectors that can perform any operation outside what is defined. You can surface all the underlying action attributes in your parameter schema to achieve this:

```json title="Wildcard Connector Action"
{
  "actions": [
    {
      "type": "Request",
      "name": "Any Request",
      "description": "Any request.",
      "method": "::method",
      "path": "::path",
      "headers": "::headers",
      "query": "::query",
      "body": "::body",
      "parameters": {
        "properties": {
          "method": {
            "type": "string",
            "enum": ["post", "get", "put", "delete"]
          },
          "path": {
            "type": "string"
          },
          "headers": {
            "type": "object"
          },
          "query": {
            "type": "object"
          },
          "body": {
            "type": "object"
          }
        }
      }
    }
  ]
}
```

## Versioning

Not yet implemented for connectors.
