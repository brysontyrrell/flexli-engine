import logging
import os
import sys

# Suppress ALL X-Ray SDK output during testing
logging.getLogger("aws_xray_sdk").setLevel(logging.CRITICAL)
os.environ["AWS_XRAY_CONTEXT_MISSING"] = "LOG_ERROR"

os.environ["AWS_DEFAULT_REGION"] = "us-east-2"
os.environ["AWS_REGION"] = "us-east-2"

os.environ["RUN_QUEUE_URL"] = "RunQueueUrl"
os.environ["TABLE_NAME"] = "WorkflowsTable"
os.environ["MAIN_TABLE_NAME"] = "WorkflowsTable"

sys.path.append(".")
sys.path.append("src/layers/layer")
