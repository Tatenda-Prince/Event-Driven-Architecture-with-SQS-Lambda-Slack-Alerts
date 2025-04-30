terraform {
  backend "s3" {
    bucket         = "terraform-state-tatenda"
    key            = "event-driven/state.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

