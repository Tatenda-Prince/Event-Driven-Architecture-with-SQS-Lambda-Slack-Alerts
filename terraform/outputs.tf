output "sqs_queue_arn" {
  value = aws_sqs_queue.ci_events_queue.arn
}

output "lambda_iam_role_name" {
  value = aws_iam_role.lambda_exec_role.name
}
