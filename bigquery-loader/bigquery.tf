terraform {
  backend "gcs" {
    bucket = "nais-analyse-tfstate"
  }
}

provider "google" {
  version = "3.45.0"
  project = "nais-analyse-prod"
  region  = "europe-west1"
}

data "archive_file" "function_archive" {
  type        = "zip"
  source_dir  = "./cloud-function-src"
  output_path = "source.zip"
}

resource "google_storage_bucket" "bucket" {
  name     = "cloud-function-bigquery-deploy-loader-source"
  location = "EU"
}

resource "google_storage_bucket_object" "archive" {
  name                = format("%s-%s", data.archive_file.function_archive.output_md5, data.archive_file.function_archive.output_path)
  bucket              = google_storage_bucket.bucket.name
  source              = data.archive_file.function_archive.output_path
  content_disposition = "attachment"
  content_encoding    = "gzip"
  content_type        = "application/zip"
}

resource "google_project_service" "service" {
  for_each = toset([
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "bigquery.googleapis.com",
    "cloudfunctions.googleapis.com",
    "compute.googleapis.com"
  ])
  service                    = each.key
  disable_dependent_services = false
}

resource "google_cloudfunctions_function" "function" {
  name        = "bigquery-deploy-loader"
  description = "Loads deploy data to bigquery"
  runtime     = "python39"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.archive.name
  trigger_http          = true
  timeout               = 60
  entry_point           = "main"
  labels = {
    team = "nais"
  }
  service_account_email = data.google_service_account.projects-to-bigquery.email
}

# IAM entry for a single user to invoke the function
resource "google_service_account" "scheduler-bigquery-deploy-loader" {
  account_id = "scheduler-bigquery-deploy-loader"
}

resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = google_cloudfunctions_function.function.project
  region         = google_cloudfunctions_function.function.region
  cloud_function = google_cloudfunctions_function.function.name

  role   = "roles/cloudfunctions.invoker"
  member = "serviceAccount:${google_service_account.scheduler-bigquery-deploy-loader}"
}

data "google_service_account" "bigquery-deploy-loader" {
  account_id = "bigquery-deploy-loader"
}

resource "google_cloud_scheduler_job" "job" {
  name             = "bigquery-deploy-loader"
  description      = "Reads deploy data from bucket and loads to bigquery"
  schedule         = "0 4 * * *"
  time_zone        = "Europe/Oslo"
  attempt_deadline = "60s"
  region           = "europe-west3"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.function.https_trigger_url

    oidc_token {
      service_account_email = google_service_account.scheduler-bigquery-deploy-loader.email
    }
  }
}
