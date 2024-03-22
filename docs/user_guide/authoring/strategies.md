# Workflow Strategies

If you are designing a workflow with complex conditional branching or parallelism you may want to break it up into multiple workflows with appropriate triggers. A common nested workflow pattern is to have one workflow as the initiator that evaluates a data set and then emits events or directly invokes the child workflows as an action.

!!! info "Learn more about the available core actions in [Core Resources: Actions](core.md#actions)"

### Using custom events (`Flexli:CoreV1:CustomEvent`)

Using a custom event provides greater decoupling between your workflows and allows for multiple child workflows to trigger off the same event. This is a fully asynchronous mechanism and the parent workflow will need to continue on to the next action or end.

!!! note "The parent's run ID is not passed when using a custom event. This will change in a future update."

### Direct runs (`Flexli:CoreV1:RunWorkflow`)

A workflow can also run another workflow directly. This creates tighter coupling but reduces the latency between the parent action and start of the child run. A direct run can be synchronous, forcing the parent to wait until the child completes, or asynchronous (same behavior as using a custom event).

The run ID of the parent is passed into the child run when using this action. This links the workflow runs allows the complete end-to-end history to be retrieved from the _**Run History APIs**_.