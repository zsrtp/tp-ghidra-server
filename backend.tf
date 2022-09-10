terraform {
  backend "s3" {
    bucket = "pheenoh-terraform-tfstate"
    key    = "ghidra-server.tfstate"
    region = "us-east-2"
  }
}