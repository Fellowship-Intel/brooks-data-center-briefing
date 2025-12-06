terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --------------------------------------------------------------------------------
# Variables
# --------------------------------------------------------------------------------

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "mikebrooks"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run Service Name"
  type        = string
  default     = "brooks-daily-briefing"
}

# --------------------------------------------------------------------------------
# APIs
# --------------------------------------------------------------------------------

resource "google_project_service" "services" {
  for_each = into([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "texttospeech.googleapis.com",
    "generativelanguage.googleapis.com", # Gemini
    "cloudbuild.googleapis.com"
  ])
  
  service            = each.key
  disable_on_destroy = false
}

# --------------------------------------------------------------------------------
# Cloud Run Service (Streamlit App)
# --------------------------------------------------------------------------------

resource "google_cloud_run_service" "default" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/${var.service_name}:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
        
        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }
        
        env {
           name = "ENVIRONMENT"
           value = "production"
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [google_project_service.services]
}

# Allow unauthenticated access (since we handle auth in-app)
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.default.name
  location = google_cloud_run_service.default.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# --------------------------------------------------------------------------------
# Firestore
# --------------------------------------------------------------------------------

# Note: Firestore database creation via Terraform is tricky as it's often created
# automatically or via App Engine. We'll skip specific resource creation here
# but assume the API is enabled.

# --------------------------------------------------------------------------------
# Storage Bucket for Reports/Audio
# --------------------------------------------------------------------------------

resource "google_storage_bucket" "reports_bucket" {
  name          = "${var.project_id}-reports"
  location      = "US"
  force_destroy = false
  
  uniform_bucket_level_access = true
}

# --------------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------------

output "service_url" {
  value = google_cloud_run_service.default.status[0].url
}
