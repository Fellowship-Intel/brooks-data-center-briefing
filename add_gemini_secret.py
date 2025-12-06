"""
Script to add Gemini API Key to GCP Secret Manager.

This script creates or updates the GEMINI_API_KEY secret in Secret Manager.
"""

import os
from gcp_clients import get_secret_manager_client, get_project_id


def create_or_update_secret(secret_id: str, secret_value: str) -> None:
    """
    Create or update a secret in Secret Manager.
    
    Args:
        secret_id: The secret ID (e.g., "GEMINI_API_KEY")
        secret_value: The secret value to store
    """
    project_id = get_project_id()
    client = get_secret_manager_client()
    
    secret_name = f"projects/{project_id}/secrets/{secret_id}"
    
    try:
        # Try to access the secret to see if it exists
        try:
            client.access_secret_version(name=f"{secret_name}/versions/latest")
            print(f"Secret '{secret_id}' already exists. Updating with new version...")
        except Exception:
            # Secret doesn't exist, create it
            print(f"Secret '{secret_id}' does not exist. Creating...")
            parent = f"projects/{project_id}"
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}}
                    }
                }
            )
            print(f"✓ Secret '{secret_id}' created.")
        
        # Add a new version with the secret value
        parent = f"projects/{project_id}/secrets/{secret_id}"
        client.add_secret_version(
            request={
                "parent": parent,
                "payload": {
                    "data": secret_value.encode("utf-8")
                }
            }
        )
        print(f"✓ Secret version added for '{secret_id}'.")
        print(f"✓ Secret is now available in Secret Manager.")
        
    except Exception as e:
        print(f"✗ Error managing secret: {e}")
        raise


if __name__ == "__main__":
    # Gemini API Key
    gemini_api_key = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
    
    print("Adding Gemini API Key to Secret Manager...")
    print("=" * 60)
    
    try:
        create_or_update_secret("GEMINI_API_KEY", gemini_api_key)
        print("=" * 60)
        print("✓ Successfully added Gemini API Key to Secret Manager!")
    except Exception as e:
        print("=" * 60)
        print(f"✗ Failed to add secret: {e}")
        import traceback
        traceback.print_exc()

