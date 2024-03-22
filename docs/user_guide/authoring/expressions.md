# Expressions

Workflow state is an in-memory object that holds all the data available to your run in a JSON compatible format. The state is accessible within workflows using _**expressions**_. State data never mutates unless you explicitly modify it within a [transform](workflows.md#transforms) at the end of an action.

## JMESPath

Flexli Engine uses [JMESPath](https://jmespath.org/) to provide a robust interface to managing your workflow's state. JMESPath is a JSON querying language that allows a great amount of flexibility and extensibility without having to write custom code. In Flexli Engine's documentation there are referred to simply as expressions.

!!! info "If you are new to JMESPath's syntax it is recommended you read through the [tutorial](https://jmespath.org/tutorial.html) on official website and explore the available playgrounds."

Where supported in definitions, expressions are strings prefixed by `::`. Expressions enable you to search and extract only the data relevant to the operation you are performing.

In the example below, the expression is filtering an array of objects where the value of `type` is `"user"`, selecting only the `id` values, and returning the first. Note the pipe `|` used to join two expressions together. You may chain as many expressions together in a single string as needed to achieve the desired output.

```json title="Input State"
[
  {"type": "user", "id": 1},
  {"type": "user", "id": 2},
  {"type": "user", "id": 3},
  {"type": "user", "id": 4}
]
```

```json title="Example Expression"
{
  "user_id": "::[?type=='user'].id | [0]"
}
```

```json title="Result"
{
  "user_id": 1
}
```

In many cases, the use of expressions will be simple dot-notation. The below example is the equivalent expression to the above if there is only a single `"user"` object and not an array.

```json title="Input State"
{
  "user": {
    "id": 1
  }
}
```

```json title="Example Expression"
{
  "user_id": "::user.id"
}
```

```json title="Result"
{
  "user_id": 1
}
```

!!! warning "An expression to a non-existent location or with no results will return a `null` value."

An empty expression returns the full source that is being referenced.

```json title="Input State"
{
  "foo": "bar"
}
```

```json title="Example Expression"
{
  "baz": "::"
}
```

```json title="Result"
{
  "baz": {
    "foo": "bar"
  }
}
```

!!! note "Using `::` alone is equivalent to a `::@` expression. If you need to pass the entire source into a filter or [function](#functions) you will need to use the `@` symbol."

## Expressions in Connectors

Connector definitions use expressions to apply workflow inputs to action attributes. The table below shows where expressions are supported and where they query data from.

| Attribute       | Expression Queries |
|-----------------|--------------------|
| actions.method  | actions.parameters |
| actions.path    | actions.parameters |
| actions.headers | actions.parameters |
| actions.query   | actions.parameters |
| actions.body    | actions.parameters |

## Expressions in Workflows

Workflow definitions use expressions to apply state data to action parameters, and response data back into the state. The table below shows which attributes support expressions and where they query data from within a workflow run.

| Attribute          | Expression Queries |
|--------------------|--------------------|
| source.condition   | State              |
| source.transform   | State              |
| actions.condition  | State              |
| actions.parameters | State              |
| actions.transform  | Action Response    |

Learn more in [Authoring Workflows](workflows.md).

## Functions

JMESPath supports a number of built-in [functions](https://jmespath.org/proposals/functions.html) that allow you to filter and transform data beyond the querying language.

For example, if you want the lowest user ID from an unordered array, you can introduce a `sort()` function into the expression.

```json title="Input State"
[
  {"type": "user", "id": 3},
  {"type": "user", "id": 2},
  {"type": "user", "id": 4},
  {"type": "user", "id": 1}
]
```

```json title="Example Expression"
{
  "user_id": "::[?type=='user'].id | sort@) | [0]"
}
```

```json title="Result"
{
  "user_id": 1
}
```

Flexli Engine provides additional functions that extend this. They are detailed in [Core: Expression Functions](core.md#expression-functions).
