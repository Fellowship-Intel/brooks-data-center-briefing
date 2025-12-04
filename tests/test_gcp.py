import pytest
from unittest.mock import MagicMock, patch

from gcp_clients import get_firestore_client, get_bucket


@pytest.fixture
def mock_firestore_client():
    """Mock Firestore client creation."""
    # Need to patch the firestore module import
    with patch("google.cloud.firestore.Client") as mock_client_class:
        client = MagicMock()
        mock_client_class.return_value = client
        
        # Mock document operations
        doc_ref = MagicMock()
        doc_data = {"hello": "world"}
        doc_ref.get.return_value.to_dict.return_value = doc_data
        doc_ref.set.return_value = None
        client.collection.return_value.document.return_value = doc_ref
        
        yield client


@pytest.fixture
def mock_storage_bucket():
    """Mock Cloud Storage bucket."""
    # Need to patch the storage module import
    with patch("google.cloud.storage.Client") as mock_client_class:
        storage_client = MagicMock()
        mock_client_class.return_value = storage_client
        
        bucket = MagicMock()
        blob = MagicMock()
        blob.upload_from_string.return_value = None
        bucket.blob.return_value = blob
        storage_client.bucket.return_value = bucket
        
        yield bucket


def test_firestore(mock_firestore_client):
    """Test Firestore client operations."""
    db = get_firestore_client()
    doc_ref = db.collection("test_collection").document("test_doc")
    doc_ref.set({"hello": "world"})
    assert doc_ref.set.called
    result = doc_ref.get().to_dict()
    assert result == {"hello": "world"}


def test_storage(mock_storage_bucket):
    """Test Cloud Storage operations."""
    bucket = get_bucket("test-bucket")
    blob = bucket.blob("test-folder/hello.txt")
    blob.upload_from_string("Hello from mikebrooks project!")
    assert blob.upload_from_string.called

