module "ghidra" {
  source            = "git::https://github.com/pheenoh/ghidra-terraform-module.git?ref=1.0.0"
  aws_region        = "us-east-2"
  create_networking = false
  subnet_id         = "subnet-0936e10d4096f910b"
  create_dns_record = true
  dns_zone_name     = "tpgz.io"
  dns_record_name   = "newghidra"
  ghidra_version    = "10.0"
}