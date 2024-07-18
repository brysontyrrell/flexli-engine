# Flexli Engine

> [!IMPORTANT]
> July 2024 - This version of the workflow engine is designed for AWS as a hosted service.
> 
> This codebase is being ported to an agnostic format that can run in any cloud or on your own hosts. Stay tuned for more details. 

Flexli Engine is a flexible, extensible, event-driven workflow engine that allows users to connect APIs from different providers into meaningful integrations without writing, deploying, and maintaining their own code.

If you want to jump into "What is this?" and "How does it work?" you should explore either:

* **User Guide**: https://brysontyrrell.github.io/flexli-engine
* **API Docs**: https://brysontyrrell.github.io/flexli-engine/api

## How to deploy

I'll update this document with more detailed instructions in the future, but this project works with the vanilla AWS SAM tooling. You should be able to fire it up with:

```shell
sam build --use-container
sam deploy --guided
```

## What's with the name "Flexli?"

I had a domain I wasn't using and it was _close enough in spirit._
