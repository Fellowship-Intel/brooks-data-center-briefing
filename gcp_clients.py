"""
GCP client helpers for the 'mikebrooks' project.

This module centralizes Google Cloud Platform client creation and authentication.
It uses Application Default Credentials (ADC) for authentication, which works
both locally (via GOOGLE_APPLICATION_CREDENTIALS) and on Cloud Run (via bound service account).
"""

import os
from pathlib import Path

from google.cloud import firestore
from google.cloud import storage
from google.cloud import secretmanager
from google.auth.exceptions import DefaultCredentialsError

# Optional: load from .env in local/dev
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, we just skip .env loading
    pass


def _check_credentials() -> None:
    """
    Check if GCP credentials are available and provide helpful error messages.
    
    Raises:
        DefaultCredentialsError: If credentials are not found with helpful instructions.
    """
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Check if we're in a GCP environment (Cloud Run, etc.)
    # In GCP environments, metadata server provides credentials
    try:
        import google.auth
        google.auth.default()
        return  # Credentials found
    except DefaultCredentialsError:
        pass  # Continue to check local credentials
    
    # Check for local credentials file
    if creds_path:
        if Path(creds_path).exists():
            return  # Credentials file exists
        else:
            raise DefaultCredentialsError(
                f"GOOGLE_APPLICATION_CREDENTIALS is set to '{creds_path}' but the file does not exist.\n"
                f"Please ensure the service account JSON file exists at this path.\n"
                f"Or run: .\\setup-gcp-env.ps1 (on Windows) to set up credentials automatically."
            )
    else:
        # Try to find credentials in common location
        default_creds_path = Path.cwd() / ".secrets" / "app-backend-sa.json"
        if default_creds_path.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(default_creds_path)
            return
        
        # No credentials found
        raise DefaultCredentialsError(
            "GCP credentials not found. To set up Application Default Credentials:\n\n"
            "Option 1 (Recommended - Windows PowerShell):\n"
            "  .\\setup-gcp-env.ps1\n\n"
            "Option 2 (Manual - Windows PowerShell):\n"
            "  $env:GOOGLE_APPLICATION_CREDENTIALS=\"$PWD\\.secrets\\app-backend-sa.json\"\n\n"
            "Option 3 (Manual - Linux/Mac):\n"
            "  export GOOGLE_APPLICATION_CREDENTIALS=\"$PWD/.secrets/app-backend-sa.json\"\n\n"
            "Make sure you have a service account JSON file at:\n"
            f"  {default_creds_path}\n\n"
            "For more information, see: https://cloud.google.com/docs/authentication/external/set-up-adc"
        )


# ---------------------------------------------------------------------------
# Project / credentials resolution
# ---------------------------------------------------------------------------

def get_project_id() -> str:
    """
    Resolve the active GCP project ID.

    Priority:
    1. GCP_PROJECT_ID environment variable
    2. Default project ID "mikebrooks"

    Returns:
        The resolved project ID as a string.

    Raises:
        RuntimeError: If no project ID can be resolved.
    """
    # Avoid circular import - don't import config here
    # Use environment variable or default directly
    project_id = os.getenv("GCP_PROJECT_ID", "mikebrooks")
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
    
    Raises:
        DefaultCredentialsError: If credentials are not found (with helpful instructions).
    """
    _check_credentials()
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
    
    Raises:
        DefaultCredentialsError: If credentials are not found (with helpful instructions).
    """
    _check_credentials()
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
    
    Raises:
        DefaultCredentialsError: If credentials are not found (with helpful instructions).
    """
    _check_credentials()
    return secretmanager.SecretManagerServiceClient()


def access_eleven_labs_api_key(version: str = "latest") -> str:
    """
    Retrieve the Eleven Labs API key from Secret Manager.
    
    Falls back to ELEVEN_LABS_API_KEY environment variable if Secret Manager is unavailable.
    
    Args:
        version: Secret version to access (default: "latest").
        
    Returns:
        The Eleven Labs API key as a string.
        
    Raises:
        RuntimeError: If the key cannot be found in Secret Manager or environment.
    """
    # Try Secret Manager first
    try:
        return access_secret_value("ELEVEN_LABS_API_KEY", version)
    except Exception:
        # Fall back to environment variable
        api_key = os.getenv("ELEVEN_LABS_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Eleven Labs API key not found. Set ELEVEN_LABS_API_KEY in environment, "
                "or ensure ELEVEN_LABS_API_KEY exists in Secret Manager."
            )
        return api_key


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
