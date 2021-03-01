terraform {
  backend "gcs" {
    bucket = "nais-analyse-tfstate"
  }
}

provider "google" {
  version = "3.45.0"
  project = "nais-analyse-prod"
  region  = "europe-north1"
}


resource "google_project_service" "service" {
  for_each = toset([
    "cloudscheduler.googleapis.com",
    "bigquery.googleapis.com",
    "cloudfunctions.googleapis.com",
    "compute.googleapis.com"
  ])
  service                    = each.key
  disable_dependent_services = false 
}
