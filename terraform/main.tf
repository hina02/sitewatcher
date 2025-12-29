terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}


# -------------------------------------------------------------------
# 1. ネットワーク (VPC)
# -------------------------------------------------------------------
resource "google_compute_network" "vpc" {
  name                    = "${var.cluster_name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "vpc" {
  name          = "${var.cluster_name}-subnet"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.0.0.0/24"
}

# -------------------------------------------------------------------
# 2. GKE クラスタ (親玉)
# -------------------------------------------------------------------
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = "${var.region}-a"

  # custom node pool
  remove_default_node_pool = true
  initial_node_count       = 1
  network                  = google_compute_network.vpc.name
  subnetwork               = google_compute_subnetwork.vpc.name

  deletion_protection = false # tarraform destroy OK
}

# -------------------------------------------------------------------
# 3. ノードプール (実際にアプリが動くマシンたち)
# -------------------------------------------------------------------
resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = "${var.region}-a"
  cluster    = google_container_cluster.primary.name
  node_count = 1

  node_config {
    machine_type = "e2-standard-2"
    spot         = true # SpotVM利用（コスト減）
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}