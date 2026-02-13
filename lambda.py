"""
Lambda functions for the Scones Unlimited image classification Step Function workflow.
Copy each handler block into its corresponding Lambda in the AWS console:
  1. serializeImageData  -> serialize_image_data_handler
  2. classifier Lambda  -> classifier_handler (package with sagemaker dependency)
  3. filter low-confidence -> filter_confidence_handler
"""

import json
import boto3
import base64

# ---------------------------------------------------------------------------
# Lambda 1: Serialize image data from S3 (name e.g. "serializeImageData")
# ---------------------------------------------------------------------------

s3 = boto3.client("s3")


def serialize_image_data_handler(event, context):
    """Copy an object from S3, base64 encode it, return as image_data in the event."""
    key = event["s3_key"]
    bucket = event["s3_bucket"]

    s3.download_file(bucket, key, "/tmp/image.png")

    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    print("Event:", list(event.keys()))
    return {
        "statusCode": 200,
        "body": {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": [],
        },
    }


# ---------------------------------------------------------------------------
# Lambda 2: Image classification (package with sagemaker + deps)
# Set ENDPOINT to your deployed SageMaker endpoint name.
# ---------------------------------------------------------------------------

def classifier_handler(event, context):
    """Decode image from event, call SageMaker endpoint, return inferences."""
    import boto3
    runtime = boto3.client("sagemaker-runtime")
    ENDPOINT = "image-classification-2026-02-12-12-42-58-663"


    # No json.loads needed
    image_b64 = event["body"]["image_data"]

    # Decode base64 → raw bytes
    image_bytes = base64.b64decode(image_b64)


    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT,
        ContentType="application/x-image",
        Body=image_bytes
    )

    

    result = response["Body"].read().decode("utf-8")

    return {
        "statusCode": 200,
        "body": result
    }


# ---------------------------------------------------------------------------
# Lambda 3: Filter low-confidence inferences (must "fail loudly" - no error handler)
# ---------------------------------------------------------------------------

THRESHOLD = 0.93


def filter_confidence_handler(event, context):
    """Raise if no inference meets THRESHOLD; otherwise return event."""
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body)

    print(body)
    # return(body)
    # inferences_raw = body.get("inferences", [])
    # if isinstance(inferences_raw, str):
    #     inferences = json.loads(inferences_raw)
    # else:
    #     inferences = inferences_raw

    meets_threshold = max(body) >= THRESHOLD

    if not meets_threshold:
        raise ValueError("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        "statusCode": 200,
        "body": json.dumps(body),
    }


# ---------------------------------------------------------------------------
# Aliases for Lambda console: set handler to lambda.lambda_handler and
# choose the correct handler name in the code, or use one of these as handler:
#   lambda.serialize_image_data_handler
#   lambda.classifier_handler
#   lambda.filter_confidence_handler
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    """Single entrypoint; dispatch by Lambda function name from env (optional)."""
    import os
    name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")
    if "serialize" in name.lower():
        return serialize_image_data_handler(event, context)
    if "classif" in name.lower():
        return classifier_handler(event, context)
    if "filter" in name.lower() or "confidence" in name.lower():
        return filter_confidence_handler(event, context)
    return {"body":"Not a valid function name was called", "status":401}
