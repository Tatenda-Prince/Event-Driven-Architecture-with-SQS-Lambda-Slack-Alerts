import json
import os
import boto3
import urllib3

http = urllib3.PoolManager()
ssm = boto3.client('ssm')

# Get the parameter name from environment variable
PARAM_NAME = os.environ.get("SLACK_SSM_PARAM_NAME")

def get_slack_webhook_url():
    try:
        response = ssm.get_parameter(
            Name=PARAM_NAME,
            WithDecryption=True  # This is needed for SecureString
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"[ERROR] Failed to retrieve Slack webhook URL from SSM: {e}")
        return None

def lambda_handler(event, context):
    slack_webhook_url = get_slack_webhook_url()
    if not slack_webhook_url:
        return {
            "statusCode": 500,
            "body": "Failed to retrieve Slack webhook URL from SSM"
        }

    for record in event['Records']:
        message_body = record['body']
        print(f"[INFO] Received SQS message: {message_body}")

        try:
            message = json.loads(message_body)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            message = {"error": "Invalid JSON in SQS message", "raw": message_body}

        slack_message = {
            "text": f":rotating_light: *Deployment Alert!*\n```{json.dumps(message, indent=2)}```"
        }

        try:
            response = http.request(
                "POST",
                slack_webhook_url,
                body=json.dumps(slack_message).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            print(f"[INFO] Slack response status: {response.status}")
            print(f"[INFO] Slack response body: {response.data.decode('utf-8')}")
        except Exception as e:
            print(f"[ERROR] Failed to send message to Slack: {e}")

    return {"statusCode": 200}





