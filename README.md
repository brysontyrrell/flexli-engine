# Flexli Engine

Flexli Engine is a flexible, extensible, event-driven workflow engine that allows users to connect APIs from different providers into meaningful integrations without writing, deploying, and maintaining their own code.

If you want to jump into "What is this?" and "How does it work?" you should explore either:

* **User Guide**: https://brysontyrrell.github.io/flexli-engine
* **API Docs**: https://brysontyrrell.github.io/flexli-engine/api

## Backstory

This is a project born of many smaller projects started and shelved over the years. That in itself is an interesting story to tell as there are so many of us who do little things on the side that may actually add up to a greater whole if we start piecing them together.

The original commit of the original repository is just notes about an idea from a hallway conversation I had at Jamf back in 2020. The person I was talking to said, "If a mobile device joins a group I want to be able to run an MDM command in response." My response to this was, "You're not going far enough," and suggested instead that the product should allow any sequence of MDM commands to run. Agent-less workflows is the core of what I had in mind, but I never had a chance at Jamf to really explore it.

A year later in my free time I decided to experiment with a new group calculation engine based on the JSON representation of the objects being grouped. I ended up with a pretty powerful condition evaluation system that worked really well, but I didn't go the next step of building a prototype service to demo.

Another year after that I felt the need to brush on up non-AWS technical skills. I don't remember the reason, but I wanted to have the ability to perform transforms on JSON for something. It's always *for something*. Mostly I think I was inspired by reading about [JMESPath](https://jmespath.org/) and playing around it. I chose some new tech (FastAPI and MongoDB) and I wrote an API that can store transform templates and then process requests for them. This one I actually did finish and publish as the [data-mapper](https://github.com/brysontyrrell/data-mapper).

Finally, in 2023 I had the itch again and wanted to work on something to occupy my free time. Workflow systems and API-to-API automation without code has always been an exciting area. I stumbled across my `SmartCommands` repo and decided to build it around Step Functions and see how far I could push it. Over the course of the year that original goal morphed into a full-blown service and I ended up which a huge, functional codebase that I wasn't sure what to do with.

If you're diving into this you're going to find hints all over the place that I was thinking about running this as a side business (I'll gradually get around to cleaning that all up). The low/no-code automation and workflow space is very competitive, and there are a lot of options out there, and I just didn't have it in me to seriously go after it while trying to keep my current job.

So, it's going public. There are a lot of rough corners, and there are some features in the user guide that aren't implemented yet. I was also changing a lot of the structure to something more long term sustainable (echoes of hexagonal architecture within). You may notice this is in fact a serverless monorepo pattern! I usually start all my projects this way (along with a fat shared Lambda Layer) and then break the components up into individual repos later.

I think this is something I will continue to come back to over time and tinker with. If you've come across it feel free to explore, comment, maybe even critique (but do so gently).

## What's left undone?

There are a lot of things not related to code organization and project structure that I haven't gotten to at the time of publishing this project in its current form.

* **Events API**: This is the ingest point for external custom events. There is a fully functioning internal events system that this would have been built on top of, but the portions of the Connectors API needed to configure that aren't there.
* **Templating**: One of the original goals of this project was to follow what I called the "Autopkg pattern." Autopkg is an IT tool for discovering and packaging software updates for deployment to Macs. It took off with the Mac Admins community because of the open nature of its "recipes" - the definitions that tell Autopkg what to do. If someone wrote an Autopkg recipe you could take a copy and use it without having to do the work yourself. Flexli Engine was to support templating all of its resources (namely Connectors and Workflows) and allow easy sharing and discovery via git repos. Some of that code is in the original codebase, but not ready.
* **CI/CD Support**: This was dependent on finishing the templating work. The natural extension of templates would be to have easy CI/CD flows where your connectors and workflows are maintained in source control and validated before going into your tenant.
* **Workflow Testing**: Testing low/no-code solutions as a user always poses challenges. A planned extension of the Run API was to allow users to pass mock response payloads for actions. It would be flexible in allowing any number of actions to be mocked, and the un-mocked ones would perform the live request.
* **Versioning**: This is a key piece of the engine's design. When you update your workflows they automatically increment in version, and you have to explicitly promote a version to "release" for it to take over triggering on events. Any workflow can be run directly via the Run API, but the event-based triggers only run against the release version.
* **Role-Based Access Controls**: [Cedar policies](https://www.cedarpolicy.com/) were going to work their way into this API at some point to allow users within a tenant to assign permissions. Don't want a particular group to see certain Connectors or Workflows? Long term, that was to be a supported feature.
* **Concurrency Controls**: This is hinted at in a few places, but not implemented. When working with third party APIs with rate limits (or other limits) and having a highly scalable system hammering them you can end up with mass failures with timeouts or exhausted retries. The concurrency control's implementation might have been assigning the workflows of that type off to a FIFO queue, or using an atomic counter in a table, or _something_, but it's not there.
* **Backoff/Retry**: Another item that's in the API schemas and in the docs but not implemented in the codebase. This was one of the latest additions to the API I had finished designing and just didn't get around to writing the rest.
* **OAuth2 Auth Code Flow**: Connector authentication only supports some basic static key options at the moment. Additional APIs to enable an auth code flow, with background tasks handling token refreshing, were planned.
* **Queue Groups**: This is an architectural thing. Right now there is only a single SQS queue and workflow runner when the stacks get created. For early dev that's just fine, but the queue and the runner are meant to be their own stack, and the runner actually attached to _multiple queues_. The idea was to adopt a shuffle-sharding-esque pattern where tenants are assigned multiple queues they can publish to (across different queue groups) and the system could block off those with high contention or being flooded by a single tenant. These are all just notes for now. 
* **Namespacing**: This one is a bigger picture item. Going back to sharable Connector and Workflow templates and the discovery of those, it's more than possible that many people will build their own versions of connectors of a service's API and that could lead to confusion trying to sort out which one you're supposed to use for a workflow. Namespacing would be a part of discoverability where an organization could claim a domainn namespace (`myorg.com`) and that would become a part of the `Type` for these objects. An API would then be available to list all the published connectors and workflows, ensure the correct namespaces types and versions were within your tenant when adding a workflow, and pull in their changes over time. This exists only in a design doc.

And of course there are bugs and inefficiencies **everywhere**. You can easily infinite loop workflows! I have **todos** littered all over the codebase, and other external notes where I've tracked all the places where I should be caching returns, cutting down service calls, or just haven't ensured longer-running tasks can gracefully stop and recurse.

If you're playing around with this, you are given notice: there be dragons.

## How to deploy

I'll update this document with more detailed instructions in the future, but this project works with the vanilla AWS SAM tooling. You should be able to fire it up with:

```shell
sam build --use-container
sam deploy --guided
```

## What's with the name "Flexli?"

I had a domain I wasn't using and it was _close enough in spirit._
