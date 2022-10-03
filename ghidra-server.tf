module "ghidra" {
  source                     = "git::https://github.com/pheenoh/ghidra-terraform-module.git?ref=1.1.0"
  aws_region                 = "us-east-2"
  aws_create_networking      = false
  aws_subnet_id              = "subnet-0936e10d4096f910b"
  aws_create_dns_record      = true
  aws_dns_zone_name          = "tpgz.io"
  aws_dns_record_name        = "newghidra"
  ghidra_uri_override        = "https://pheenoh-tp-community.s3.us-east-2.amazonaws.com/ghidra_10.2_DEV_20221002_linux_x86_64.zip"
  ghidra_zip_file_name       = "ghidra_10.2_DEV_20221002_linux_x86_64.zip"
  ghidra_extract_folder_name = "ghidra_10.2_DEV"
  java_download_uri          = "wget https://corretto.aws/downloads/latest/amazon-corretto-17-x64-linux-jdk.tar.gz"
}