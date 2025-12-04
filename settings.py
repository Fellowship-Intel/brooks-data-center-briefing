import os


def get_reports_bucket_name() -> str:
    """
    Returns the GCS bucket name where report audio will be stored.

    Expects REPORTS_BUCKET_NAME in the environment or .env.
    """
    bucket = os.getenv("REPORTS_BUCKET_NAME")
    if not bucket:
        raise RuntimeError(
            "REPORTS_BUCKET_NAME is not set. "
            "Export it in your environment or add it to .env."
        )
    return bucket

