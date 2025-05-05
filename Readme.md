# Event-Driven-Architecture-with-SQS-Lambda-Slack-Alerts

![image_alt](https://github.com/Tatenda-Prince/Event-Driven-Architecture-with-SQS-Lambda-Slack-Alerts/blob/d74c2a510b24e6f5561a4058f49d5263cf96167f/screenshots/Screenshot%202025-05-05%20124235.png)


## Background
Modern DevOps teams need to move fast, but also be immediately aware when infrastructure issues arise. Traditional logs and delayed alerts make it hard to detect problems in real-time. To solve this, I  built an event-driven system on AWS that uses SQS and Lambda to instantly notify the DevOps team when things go wrong like CI/CD pipeline failures.

##  Project Overview
This project is an end-to-end, event-driven alerting system that leverages AWS services such as SQS, Lambda, IAM, and CloudWatch fully automated with Terraform and GitHub Actions. Whenever a CI/CD event (e.g., Terraform failure) occurs, it sends a structured message to SQS, which triggers a Lambda function to process and notify the team via logs or external tools like Slack.

## Project Objectives
1.Build an asynchronous, decoupled alerting system using SQS and Lambda

2.Automate infrastructure provisioning with Terraform

3.Set up a secure and scalable CI/CD pipeline using GitHub Actions

4.Deliver real-time visibility into infrastructure issues

## Features
1.Event-driven processing using SQS + Lambda

2.Slack-ready Lambda for team notifications (extendable)

3.CI/CD notifications when Terraform fails

4.IAM-secured roles for GitHub OIDC and Lambda execution

5.Fully automated deployment via GitHub Actions

## Technologies Used
1.AWS SQS

2.AWS Lambda

3.AWS IAM

4.AWS CloudWatch

5.Terraform

6.GitHub Actions (with OIDC authentication)

## Use Case
This system solves the real-world challenge of delayed error detection in cloud environments. For instance:
1.**CI/CD Build Notifications**
Problem: CI/CD pipeline fails during `terraform plan` or `apply`, but no one notices immediately.

Solution: Send structured error messages to SQS. Lambda reads these and pushes alerts (e.g., to Slack), so teams are aware instantly.

2.**Application Error Alerting**
Problem: Lambda functions fail silently in production.

Solution: Errors get sent to SQS. Lambda processes them and alerts engineers with logs or summaries before users even notice.

## Prerequisites
1.AWS Account

2.GitHub repository

3.Terraform CLI installed

4.AWS CLI configured (for testing)

5.Slack Webhook URL (optional, if extending for Slack alerts)


Before we start please git clone the repository below to access access to terraform file

```language
git clone https://github.com/Tatenda-Prince/Event-Driven-Architecture-with-SQS-Lambda-Slack-Alerts.git
```

**Create SSM Parameter Store to store the Slack Webhook URL**

Run the following commands

```language
aws ssm put-parameter \
  --name "/webhooks/slack_url" \
  --value "https://hooks.slack.com/services/your/webhook/url" \
  --type "SecureString" \
  --description "Slack Webhook URL for Lambda notifications" \
  --overwrite
```

## Step 1: Copy and paste the following terraform files & lambda functions
1.1.The Terraform file will create:
1.AWS SQS Queue

2.Lambda Function

3.IAM Roles and Policies

1.2.Copy and paste this **main.tf**
```language
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
```
1.3.Copy and paste this **iam.tf**
```language
# IAM Role for Lambda Execution
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda-sqs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# IAM Policy with SQS, CloudWatch, and SSM Access
resource "aws_iam_policy" "lambda_policy" {
  name = "lambda-sqs-cw-ssm-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      # CloudWatch Logs
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
      # SQS permissions
      {
        Effect = "Allow",
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ],
        Resource = aws_sqs_queue.ci_events_queue.arn
      },
      # SSM Parameter Store access
      {
        Effect = "Allow",
        Action = [
          "ssm:GetParameter"
        ],
        Resource = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/slack/webhook_url"
      }
    ]
  })
}

# Get AWS Account ID
data "aws_caller_identity" "current" {}

# Attach IAM Policy to Role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Permission for SQS to invoke Lambda
resource "aws_lambda_permission" "allow_sqs" {
  statement_id  = "AllowExecutionFromSQS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.event_processor.function_name
  principal     = "sqs.amazonaws.com"
  source_arn    = aws_sqs_queue.ci_events_queue.arn
}

```
1.4.Copy and paste this **outputs.tf**
```language
output "sqs_queue_arn" {
  value = aws_sqs_queue.ci_events_queue.arn
}

output "lambda_iam_role_name" {
  value = aws_iam_role.lambda_exec_role.name
}

```

1.5.Copy and paste this **variables.tf**
```language
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

```

## Step 2 : Create OIDC Identity Provider in AWS IAM
2.1.Go to `IAM` → `Identity providers`

2.2.Click `Add provider`

1.`Provider type`: OpenID Connect

2.`Provider URL`:
```language
https://token.actions.githubusercontent.com
```

3.`Audience`:
```language
sts.amazonaws.com
```
2.3.Click Add provider


2.5.**Create an IAM Role for GitHub Actions**

1.Go to IAM → Roles → Create Role

2.Trusted entity type:
Select `Web identity`

3.Identity provider:
Choose the `OIDC provider` you just created

4.Audience: sts.amazonaws.com

5.Conditions (optional but recommended):
Add a condition to restrict the GitHub repo that can assume the role:
```language
{
  "StringEquals": {
    "token.actions.githubusercontent.com:sub": "repo:<GITHUB_USERNAME>/<REPO_NAME>:ref:refs/heads/main"
  }
}

```

2.6.Create a policy and attach the policy to your role : copy the policy below 

```language
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:*",
                "dynamodb:*",
                "lambda:*",
                "sqs:*",
                "logs:*",
                "cloudwatch:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:GetPolicy",
                "iam:PassRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:CreatePolicy",
                "iam:DeletePolicy",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:ListRolePolicies",
                "iam:GetPolicyVersion",
                "iam:ListAttachedRolePolicies"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:PutParameter",
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:us-east-1:<your account id>:parameter/slack/webhook_url"
        }
    ]
}
```

2.7.Role name:
Name it something like:
```language
GitHubActionsOIDCRole
```

## Step 3: GitHub Actions: CI/CD Setup
`.github/workflows/terraform.yml`

```language
name: Terraform CI/CD

on:
  push:
    branches:
      - main
  pull_request:

permissions:
  id-token: write
  contents: read

jobs:
  terraform:
    name: Deploy Infrastructure with Terraform
    runs-on: ubuntu-latest

    env:
      AWS_REGION: us-east-1
      TF_WORKING_DIR: ./terraform

    steps:
      - name: 📥 Checkout repository
        uses: actions/checkout@v3

      - name: 🔐 Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::970547345579:role/GitHubTerraformRole
          aws-region: ${{ env.AWS_REGION }}

      - name: 🐍 Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: 📦 Cache Python dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('lambda/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: 🗜️ Package Lambda deployment
        working-directory: ./lambda
        run: |
          echo "📁 Validating Lambda build directory"
          test -f handler.py || { echo "❌ handler.py not found!"; exit 1; }
          test -f requirements.txt || { echo "❌ requirements.txt not found!"; exit 1; }

          echo "⬆️ Upgrading pip"
          pip install --upgrade pip

          echo "📦 Installing dependencies to current directory"
          pip install -r requirements.txt -t .

          echo "🗃 Zipping Lambda function and dependencies"
          zip -r ../terraform/lambda.zip . -x "*.pyc" "__pycache__/*"

      - name: 🔧 Set up Terraform CLI
        uses: hashicorp/setup-terraform@v3

      - name: 🌱 Terraform Init
        run: terraform init
        working-directory: ${{ env.TF_WORKING_DIR }}

      - name: 📐 Terraform Format Check
        run: terraform fmt -check -recursive
        working-directory: ${{ env.TF_WORKING_DIR }}

      - name: ✅ Terraform Validate
        run: terraform validate
        working-directory: ${{ env.TF_WORKING_DIR }}

      - name: 📋 Terraform Plan
        run: terraform plan -input=false
        working-directory: ${{ env.TF_WORKING_DIR }}

      - name: 🚀 Terraform Apply (main branch only)
        if: github.ref == 'refs/heads/main'
        run: terraform apply -auto-approve -input=false
        working-directory: ${{ env.TF_WORKING_DIR }}

```

## Step 5: Testing the CI/CD System
5.1.Push a change to the `main` branch on GitHub

5.2.GitHub Actions will run, authenticate using OIDC, and apply Terraform

1.Github Actions workflow successfully provisions resources

![image_alt](https://github.com/Tatenda-Prince/Event-Driven-Architecture-with-SQS-Lambda-Slack-Alerts/blob/ddf119b826ab4840379d206029daeea58dec2cc8/screenshots/Screenshot%202025-05-05%20191746.png)


2.Verify if SQS & Lambda is succesfully created

![image_alt](https://github.com/Tatenda-Prince/Event-Driven-Architecture-with-SQS-Lambda-Slack-Alerts/blob/222f982188bd1c18c7f5a4a3c73977faf3676b32/screenshots/Screenshot%202025-05-05%20191838.png)

5.3.Send a test message to SQS:

```language
aws sqs send-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/123456789012/ci-events-queue \
  --message-body '{"status":"error","message":"Terraform Apply Failed"}'
```

5.4.Check CloudWatch logs for Lambda output:

![image_alt](https://github.com/Tatenda-Prince/Event-Driven-Architecture-with-SQS-Lambda-Slack-Alerts/blob/da7ce3ed6ef5ae04ba6a8733ace0f17aaf189e91/screenshots/Screenshot%202025-05-05%20201050.png)


5.5.Check for Slack notifications: 

![image_alt](https://github.com/Tatenda-Prince/Event-Driven-Architecture-with-SQS-Lambda-Slack-Alerts/blob/1eb9122095fdc595e3557421789dcd7aaf11ac94/screenshots/Screenshot%202025-05-05%20201122.png)


## What I’ve Learned

1.How to build asynchronous event-driven architectures

2.Automating infra with Terraform and GitHub Actions

3.Configuring OIDC trust between GitHub and AWS

4.Decoupling failure detection using SQS and Lambda

5.Real-time alerting strategies for modern cloud ops
