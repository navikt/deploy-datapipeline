terraform {
  backend "gcs" {
    bucket = "nais-analyse-tfstate"
  }
}

provider "google" {
  version = "3.45.0"
  project = "nais-analyse-prod-2dcc"
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

resource "google_bigquery_dataset" "default" {
  dataset_id                  = "deploys"
  friendly_name               = "deploys"
  description                 = "Data about nais deploys"
  location                    = "europe-north1"
}

resource "google_bigquery_table" "vera_deploys" {
  dataset_id = google_bigquery_dataset.default.dataset_id
  table_id = "vera_deploys"

  schema = <<EOF
[
  {
    "name": "environment",
    "type": "STRING"
  },
  {
    "name": "application",
    "type": "STRING"
  },
  {
    "name": "version",
    "type": "STRING"
  },
  {
    "name": "deployer",
    "type": "STRING"
  },
  {
    "name": "deployed_timestamp",
    "type": "TIMESTAMP"
  },
  {
    "name": "replaced_timestamp",
    "type": "TIMESTAMP"
  },
  {
    "name": "environmentClass",
    "type": "STRING"
  },
  {
    "name": "id",
    "type": "STRING"
  }
]
EOF
}

resource "google_service_account" "function-load-vera-deploys" {
  account_id = "function-load-vera-deploys"
}