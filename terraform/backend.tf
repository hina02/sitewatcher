terraform {
  backend "gcs" {
    bucket = "fc5f0f56b6fc3adf-terraform-remote-backup"
    prefix = "terraform/state"
  }
}