# SAMPLE_EVENT
# {
#     "version": "1",
#     "region": "us-east-2",
#     "userPoolId": "us-east-2_ws9hYCIxk",
#     "userName": "bryson",
#     "callerContext": {
#         "awsSdkVersion": "aws-sdk-unknown-unknown",
#         "clientId": "2aogor9phkt7dsd9ual2fscn1",
#     },
#     "triggerSource": "PreAuthentication_Authentication",
#     "request": {
#         "userAttributes": {
#             "sub": "977feba5-2310-4c7b-bf99-5221e6d2a4e9",
#             "cognito:user_status": "CONFIRMED",
#             "name": "Bryson Tyrrell",
#             "email": "bryson.tyrrell@gmail.com",
#             "custom:tenant-id": "abc123",
#         },
#         "validationData": None,
#     },
#     "response": {},
# }


def lookup_allowed_app_clients_for_user(user_id: str) -> list[str]:
    """Lookup user's allowed app clients from DynamoDB"""
    pass


def lambda_handler(event, context):
    # https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-authentication.html
    # user_id = event["request"]["userAttributes"]["sub"]
    # requested_client_id = event["callerContext"]["clientId"]
    # allowed_app_clients = lookup_allowed_app_clients_for_user(user_id)

    # Check if the user is allowed to use this app client
    # if requested_client_id not in allowed_app_clients:
    #     raise Exception("Cannot authenticate users from this user pool app client")

    return event
