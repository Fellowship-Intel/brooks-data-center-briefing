"""
Save a generic file to both Firestore and Cloud Storage in default folders.
"""
import os
import json
from datetime import datetime

# Check credentials before importing
def check_credentials():
    """Check if GCP credentials are properly configured."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not creds_path:
        print("⚠ GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        print("  Please run: . .\\setup-gcp-env.ps1")
        print("  Or set manually:")
        print('  $env:GOOGLE_APPLICATION_CREDENTIALS="$PWD\\.secrets\\app-backend-sa.json"')
        print('  $env:GCP_PROJECT_ID="mikebrooks"')
        return False
    
    # Normalize path (handle both forward and backslashes)
    creds_path = os.path.normpath(creds_path)
    
    if not os.path.exists(creds_path):
        print(f"⚠ Credentials file not found: {creds_path}")
        print("  Please ensure the service account JSON file exists at this path.")
        print("  You can:")
        print("    1. Create the .secrets directory if it doesn't exist")
        print("    2. Place your service account JSON file at: .secrets\\app-backend-sa.json")
        print("    3. Or run: . .\\setup-gcp-env.ps1")
        return False
    
    # Verify it's actually a file (not a directory)
    if not os.path.isfile(creds_path):
        print(f"⚠ Path exists but is not a file: {creds_path}")
        return False
    
    return True

# Only import if credentials check passes (or attempt anyway for better error)
try:
    from gcp_clients import get_firestore_client, get_bucket
except Exception as e:
    print(f"⚠ Error importing GCP clients: {e}")
    print("  Make sure credentials are set up correctly.")


def save_to_firestore():
    """Save a generic document to Firestore in the 'default' collection."""
    db = get_firestore_client()
    
    # Create a generic document in the 'default' collection
    doc_ref = db.collection("default").document("generic")
    
    generic_data = {
        "name": "generic",
        "type": "test_file",
        "created_at": datetime.now().isoformat(),
        "content": "This is a generic test file saved to Firestore",
        "metadata": {
            "project": "mikebrooks",
            "service": "firestore"
        }
    }
    
    doc_ref.set(generic_data)
    print(f"✓ Saved generic document to Firestore: default/generic")
    print(f"  Data: {json.dumps(generic_data, indent=2)}")
    
    # Verify by reading it back
    doc = doc_ref.get()
    if doc.exists:
        print(f"✓ Verified: Document exists with ID: {doc.id}")
        return True
    return False


def save_to_storage(bucket_name: str):
    """Save a generic file to Cloud Storage in the 'default' folder."""
    bucket = get_bucket(bucket_name)
    
    # Save as a text file
    blob_text = bucket.blob("default/generic.txt")
    blob_text.upload_from_string("This is a generic test file saved to Cloud Storage\nCreated for mikebrooks project")
    print(f"✓ Saved generic.txt to Cloud Storage: default/generic.txt")
    
    # Also save as JSON
    generic_json = {
        "name": "generic",
        "type": "test_file",
        "created_at": datetime.now().isoformat(),
        "content": "This is a generic test file saved to Cloud Storage",
        "metadata": {
            "project": "mikebrooks",
            "service": "cloud_storage"
        }
    }
    blob_json = bucket.blob("default/generic.json")
    blob_json.upload_from_string(json.dumps(generic_json, indent=2), content_type="application/json")
    print(f"✓ Saved generic.json to Cloud Storage: default/generic.json")
    
    return True


if __name__ == "__main__":
    print("Saving generic files to default folders...")
    print("=" * 50)
    
    # Check credentials first
    print("Checking GCP credentials...")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        print(f"  GOOGLE_APPLICATION_CREDENTIALS is set to: {creds_path}")
    
    if not check_credentials():
        print("\n⚠ Cannot proceed without valid GCP credentials.")
        print("  Please set up credentials and try again.")
        print("=" * 50)
        exit(1)
    
    print("✓ Credentials file found and verified")
    print("✓ Proceeding with GCP operations...\n")
    
    # Save to Firestore
    try:
        save_to_firestore()
        print()
    except FileNotFoundError as e:
        error_msg = str(e)
        if "app-backend-sa.json" in error_msg or ".secrets" in error_msg:
            print(f"✗ Credentials file not found: {e}")
            print("  Please ensure .secrets/app-backend-sa.json exists")
            print("  Steps to fix:")
            print("    1. Create .secrets directory: mkdir .secrets")
            print("    2. Place your service account JSON file there")
            print("    3. Run: . .\\setup-gcp-env.ps1")
        else:
            print(f"✗ File not found error: {e}\n")
    except Exception as e:
        error_msg = str(e)
        if "File" in error_msg and "not found" in error_msg:
            print(f"✗ Credentials file not found: {e}")
            print("  Please ensure .secrets/app-backend-sa.json exists")
            print("  Or run: . .\\setup-gcp-env.ps1\n")
        else:
            print(f"✗ Error saving to Firestore: {e}")
            print(f"  Error type: {type(e).__name__}\n")
    
    # Save to Cloud Storage (replace with your bucket name)
    bucket_name = "YOUR_BUCKET_NAME"  # Replace with your actual bucket name
    
    if bucket_name == "YOUR_BUCKET_NAME":
        print("⚠ Skipping Cloud Storage - please set bucket_name in the script")
    else:
        try:
            save_to_storage(bucket_name)
        except FileNotFoundError as e:
            print(f"✗ Credentials file not found: {e}")
            print("  Please ensure .secrets/app-backend-sa.json exists")
        except Exception as e:
            print(f"✗ Error saving to Cloud Storage: {e}")
            print(f"  Error type: {type(e).__name__}")
    
    print("=" * 50)
    print("Done!")

