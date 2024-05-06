# User Guide

Flexli Engine is a flexible, extensible, event-driven workflow engine that allows users to connect APIs from different providers into meaningful integrations without writing, deploying, and maintaining their own code.

## Getting Started

For a walkthrough on creating your first connector and workflow head to the [Tutorial](tutorial.md).

## Connectors

Connectors represent any API you will use a workflow to. The connector definition contains configuration, credentials, and the _**Events**_ and _**Actions**_ available when authoring workflows. Connectors are reusable across different workflows. You can also create multiple connectors for the same API with changes in configuration/auth to support use cases like account data syncing or migrations.

Learn more in [Authoring Connectors](authoring/connectors.md).

## Workflows

Workflows are automations that define a sequence of actions. Workflows can run automatically from events or manually via an API call. Workflows can even call other workflows for complex automations.

Learn more in [Authoring Workflows](authoring/workflows.md).

Whenever a workflow runs there is an object that holds all the data available during the run. This is known as the _**State**_ object. When an action executes, inputs (parameters) can be dynamically populated from the state using _**Expressions**_. If the action has response from the API it is discarded unless you tell the workflow where to store the data you want back into the state in a _**Transform**_.

These concepts are explored in detail in [Expressions](authoring/expressions.md) and [Authoring Workflows: State](authoring/workflows.md#state).

## Working with Events

There are multiple type of events that can be used to automatically run your workflows. A workflow can only be triggered by an event if it is _**enabled**_, and only the promoted _**release version**_ will run in response to an event.

Learn more in [Authoring Connectors: Defining Events](authoring/connectors.md#defining-events) and [Authoring Workflows: Using Events](authoring/workflows.md#using-events).

## API Documentation

The OpenAPI documentation can be viewed at [API Docs](https://brysontyrrell.github.io/flexli-engine/api).

You can learn more about other resources for exploring the API in the [API Quickstart](api_quickstart.md) section.
