import json
import os
import urllib3

http = urllib3.PoolManager()

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def lambda_handler(event, context):
    for record in event['Records']:
        message_body = record['body']
        print(f"[INFO] Received SQS message: {message_body}")

        # Try parsing the message body
        try:
            message = json.loads(message_body)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            message = {"error": "Invalid JSON in SQS message", "raw": message_body}

        # Create Slack message payload
        slack_message = {
            "text": f":rotating_light: *Deployment Alert!*\n```{json.dumps(message, indent=2)}```"
        }

        encoded_msg = json.dumps(slack_message).encode("utf-8")

        # Try sending the message to Slack
        try:
            response = http.request(
                "POST",
                SLACK_WEBHOOK_URL,
                body=encoded_msg,
                headers={"Content-Type": "application/json"}
            )
            print(f"[INFO] Slack response status: {response.status}")
            print(f"[INFO] Slack response body: {response.data.decode('utf-8')}")
        except Exception as e:
            print(f"[ERROR] Failed to send message to Slack: {e}")

    return {"statusCode": 200}




