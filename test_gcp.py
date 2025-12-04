from gcp_clients import get_firestore_client, get_bucket


def test_firestore():
    db = get_firestore_client()
    doc_ref = db.collection("test_collection").document("test_doc")
    doc_ref.set({"hello": "world"})
    print("Firestore write OK")
    print("Firestore read:", doc_ref.get().to_dict())


def test_storage():
    bucket = get_bucket("YOUR_BUCKET_NAME")  # replace with your actual bucket name
    blob = bucket.blob("test-folder/hello.txt")
    blob.upload_from_string("Hello from mikebrooks project!")
    print("Uploaded:", blob.name)


if __name__ == "__main__":
    test_firestore()
    test_storage()

