# Infrastructure as Code (Terraform)

This directory contains the Terraform configuration to deploy the Brooks Data Center Daily Briefing application to Google Cloud Platform.

## Prerequisites

1.  [Install Terraform](https://developer.hashicorp.com/terraform/install)
2.  [Install Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3.  Authenticate with GCP:
    ```bash
    gcloud auth application-default login
    ```

## Resources Deployed

-   **Cloud Run**: Hosts the Streamlit application.
-   **Cloud Storage**: `[project-id]-reports` bucket for storing audio reports.
-   **Enabled APIs**: Cloud Run, Firestore, Secret Manager, Text-to-Speech, Gemini (Generative Language).

## Usage

1.  Initialize Terraform:
    ```bash
    terraform init
    ```

2.  Preview changes:
    ```bash
    terraform plan -var="project_id=YOUR_PROJECT_ID"
    ```

3.  Deploy:
    ```bash
    terraform apply -var="project_id=YOUR_PROJECT_ID"
    ```

## Notes

-   **Firestore**: Ensure Firestore is initialized in Native mode in the GCP Console before running this.
-   **Secrets**: You must manually populate secrets (e.g., `GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`) in Secret Manager or pass them as environment variables to the Cloud Run service if not using the default authentication flow.
