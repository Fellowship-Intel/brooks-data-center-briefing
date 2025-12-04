"""
GCP client helpers for the 'mikebrooks' project.

This module centralizes Google Cloud Platform client creation and authentication.
It uses Application Default Credentials (ADC) for authentication, which works
both locally (via GOOGLE_APPLICATION_CREDENTIALS) and on Cloud Run (via bound service account).
"""

import os

from google.cloud import firestore
from google.cloud import storage
from google.cloud import secretmanager

# Optional: load from .env in local/dev
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, we just skip .env loading
    pass


# ---------------------------------------------------------------------------
# Project / credentials resolution
# ---------------------------------------------------------------------------

DEFAULT_PROJECT_ID = "mikebrooks"


def get_project_id() -> str:
    """
    Resolve the active GCP project ID.

    Priority:
    1. GCP_PROJECT_ID environment variable
    2. A default project id constant set to "mikebrooks"

    Returns:
        The resolved project ID as a string.

    Raises:
        RuntimeError: If no project ID can be resolved.
    """
    project_id = os.getenv("GCP_PROJECT_ID", DEFAULT_PROJECT_ID)
    if not project_id:
        raise RuntimeError(
            "GCP_PROJECT_ID is not set and no default project ID is defined."
        )
    return project_id


# ---------------------------------------------------------------------------
# Firestore client
# ---------------------------------------------------------------------------

def get_firestore_client() -> firestore.Client:
    """
    Returns an authenticated Firestore client using Application Default Credentials.

    Requirements:
    - GOOGLE_APPLICATION_CREDENTIALS points to a valid service account key (local)
      OR the code is running on GCP (Cloud Run, etc.) with a bound service account.
    - Service account has roles/datastore.user on the project.

    Returns:
        An authenticated google.cloud.firestore.Client instance.
    """
    project_id = get_project_id()
    return firestore.Client(project=project_id)


# ---------------------------------------------------------------------------
# Cloud Storage client
# ---------------------------------------------------------------------------

def get_storage_client() -> storage.Client:
    """
    Returns an authenticated Cloud Storage client.

    Requirements:
    - Same auth expectations as Firestore.
    - Service account should have at least roles/storage.objectAdmin for now.

    Returns:
        An authenticated google.cloud.storage.Client instance.
    """
    project_id = get_project_id()
    return storage.Client(project=project_id)


def get_bucket(bucket_name: str) -> storage.Bucket:
    """
    Returns a Bucket object for the given bucket_name.

    Uses get_storage_client() internally.

    Args:
        bucket_name: The name of the Cloud Storage bucket.

    Returns:
        A google.cloud.storage.Bucket instance.
    """
    client = get_storage_client()
    return client.bucket(bucket_name)


# ---------------------------------------------------------------------------
# Secret Manager client
# ---------------------------------------------------------------------------

def get_secret_manager_client() -> secretmanager.SecretManagerServiceClient:
    """
    Returns a Secret Manager client.

    Requirements:
    - Service account has roles/secretmanager.secretAccessor.

    Returns:
        An authenticated google.cloud.secretmanager.SecretManagerServiceClient instance.
    """
    return secretmanager.SecretManagerServiceClient()


def access_secret_value(secret_id: str, version: str = "latest") -> str:
    """
    Fetches the value of a secret from Secret Manager as a UTF-8 string.

    Args:
        secret_id: Secret name only (e.g. "GEMINI_API_KEY"), not the full resource path.
        version: Secret version to access (default: "latest").

    Returns:
        The secret payload decoded as UTF-8 text.

    Implementation details:
    - Build the resource name as:
      f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    - Call client.access_secret_version(...)
    - Return response.payload.data decoded with .decode("utf-8")
    """
    project_id = get_project_id()
    client = get_secret_manager_client()

    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("utf-8")


# ---------------------------------------------------------------------------
# Optional smoke tests (for manual testing only)
# ---------------------------------------------------------------------------

def _smoke_test_firestore() -> None:
    """
    Smoke test for Firestore: writes a test document and reads it back.
    For manual testing only.
    """
    db = get_firestore_client()
    doc_ref = db.collection("test_collection").document("test_doc")
    doc_ref.set({"hello": "world"})
    snapshot = doc_ref.get()
    print("Firestore test OK:", snapshot.to_dict())


def _smoke_test_storage(bucket_name: str) -> None:
    """
    Smoke test for Cloud Storage: uploads a test file.
    For manual testing only.

    Args:
        bucket_name: The name of the bucket to test with.
    """
    bucket = get_bucket(bucket_name)
    blob = bucket.blob("test-folder/hello.txt")
    blob.upload_from_string("Hello from the mikebrooks app.")
    print("Storage test OK: uploaded", blob.name)


if __name__ == "__main__":
    # Optional: run quick tests manually
    print("Project ID:", get_project_id())
    # Uncomment and set your bucket name to test:
    # _smoke_test_firestore()
    # _smoke_test_storage("YOUR_BUCKET_NAME")
