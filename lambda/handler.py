import json
import os
import urllib3

http = urllib3.PoolManager()

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def lambda_handler(event, context):
    for record in event['Records']:
        message_body = record['body']
        
        # For example, we assume the body is a JSON string
        try:
            message = json.loads(message_body)
        except Exception as e:
            message = {"error": "Invalid JSON in SQS message", "raw": message_body}

        slack_message = {
            "text": f":rotating_light: *Deployment Alert!*\n```{json.dumps(message, indent=2)}```"
        }

        encoded_msg = json.dumps(slack_message).encode("utf-8")

        response = http.request(
            "POST",
            SLACK_WEBHOOK_URL,
            body=encoded_msg,
            headers={"Content-Type": "application/json"}
        )

    return {"statusCode": 200}

