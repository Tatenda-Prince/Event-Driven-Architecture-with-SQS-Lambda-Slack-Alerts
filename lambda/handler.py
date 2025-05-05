import json
import os
import boto3
import urllib3

# Initialize clients
http = urllib3.PoolManager()
ssm = boto3.client('ssm')

# Correct environment variable name
PARAM_NAME = os.environ.get("SLACK_WEBHOOK_PARAM_NAME")

def get_slack_webhook_url():
    if not PARAM_NAME:
        print("[ERROR] Environment variable 'SLACK_WEBHOOK_PARAM_NAME' is not set.")
        return None

    try:
        response = ssm.get_parameter(
            Name=PARAM_NAME,
            WithDecryption=True  # Needed if SecureString is used
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

    for record in event.get('Records', []):
        message_body = record.get('body', '')
        print(f"[INFO] Received SQS message: {message_body}")

        try:
            message = json.loads(message_body)
        except json.JSONDecodeError:
            print("[ERROR] Failed to parse JSON from SQS message.")
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
            if response.status >= 400:
                print(f"[ERROR] Slack returned error: {response.data.decode('utf-8')}")
        except Exception as e:
            print(f"[ERROR] Failed to send message to Slack: {e}")

    return {"statusCode": 200, "body": "Processed all SQS messages successfully"}
