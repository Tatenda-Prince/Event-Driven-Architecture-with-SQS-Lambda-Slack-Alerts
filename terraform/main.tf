# Create the SQS queue
resource "aws_sqs_queue" "ci_events_queue" {
  name                       = "ci-events-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 86400
}

# Create the Lambda function
resource "aws_lambda_function" "event_processor" {
  function_name = "sqs-event-processor"
  role          = aws_iam_role.lambda_exec_role.arn
  runtime       = "python3.11"
  handler       = "handler.lambda_handler"
  timeout       = 10
  memory_size   = 128

  filename         = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")

  # Instead of the value, just pass the parameter name
  environment {
    variables = {
      SLACK_WEBHOOK_PARAM_NAME = "/slack/webhook_url"
    }
  }

  tags = {
    Name        = "SQS Event Processor"
    Environment = "dev"
  }
}

# Map SQS queue to Lambda function
resource "aws_lambda_event_source_mapping" "sqs_to_lambda" {
  event_source_arn = aws_sqs_queue.ci_events_queue.arn
  function_name    = aws_lambda_function.event_processor.arn
  batch_size       = 5
  enabled          = true
}
