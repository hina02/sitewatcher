output "cluster_name" {
  value = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  value = google_container_cluster.primary.endpoint
}

output "get_credentials_command" {
  value = "gcloud container clusters get_credentials ${google_container_cluster.primary.name} --region ${var.region}"
  description = "kubectlを接続するためのコマンド"
}