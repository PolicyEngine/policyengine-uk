import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional, Union

from policyengine_core.tools.google_cloud import parse_gs_url


def materialize_gcs_dataset_url(
    dataset_url: str,
    *,
    cache_dir: Optional[Union[str, os.PathLike]] = None,
) -> str:
    """Download a GCS dataset URL to a local H5 path and return that path."""
    bucket_name, file_path, revision = parse_gs_url(dataset_url)
    storage_client = _get_storage_client()
    blob = _resolve_gcs_blob(storage_client, bucket_name, file_path, revision)
    generation = _blob_generation(blob)

    local_path = _cached_dataset_path(
        bucket_name=bucket_name,
        file_path=file_path,
        generation=generation,
        cache_dir=cache_dir,
    )
    if not local_path.exists():
        _download_blob(blob, local_path)
    return str(local_path)


def _get_storage_client():
    try:
        import google.auth
        from google.auth import exceptions as auth_exceptions
        from google.cloud import storage
    except ImportError as exc:
        raise ImportError(
            "google-cloud-storage is required for gs:// dataset URLs. "
            "Install it with: pip install google-cloud-storage"
        ) from exc

    try:
        credentials, project_id = google.auth.default()
    except auth_exceptions.DefaultCredentialsError as exc:
        raise RuntimeError(
            "Google Cloud credentials are required for gs:// dataset URLs. "
            "Set application default credentials or GOOGLE_APPLICATION_CREDENTIALS."
        ) from exc

    return storage.Client(credentials=credentials, project=project_id)


def _resolve_gcs_blob(
    storage_client,
    bucket_name: str,
    file_path: str,
    revision: Optional[str],
):
    bucket = storage_client.bucket(bucket_name)

    if revision is not None and revision.isdigit():
        blob = bucket.blob(file_path, generation=int(revision))
        blob.reload()
        return blob

    current_blob = bucket.blob(file_path)
    current_blob.reload()
    if revision is None or _blob_metadata_version(current_blob) == revision:
        return current_blob

    matching_blobs = []
    for blob in storage_client.list_blobs(
        bucket_name,
        prefix=file_path,
        versions=True,
    ):
        if blob.name != file_path:
            continue
        if _blob_metadata_version(blob) == revision:
            matching_blobs.append(blob)

    if not matching_blobs:
        raise ValueError(
            f"No GCS object version for gs://{bucket_name}/{file_path} has "
            f"metadata version {revision!r}."
        )

    return max(matching_blobs, key=lambda blob: int(_blob_generation(blob)))


def _blob_metadata_version(blob) -> Optional[str]:
    if getattr(blob, "metadata", None) is None:
        blob.reload()
    metadata = getattr(blob, "metadata", None) or {}
    return metadata.get("version")


def _blob_generation(blob) -> str:
    generation = getattr(blob, "generation", None)
    if generation is None:
        blob.reload()
        generation = getattr(blob, "generation", None)
    if generation is None:
        raise ValueError(f"GCS object {blob.name!r} does not expose a generation.")
    return str(generation)


def _cached_dataset_path(
    *,
    bucket_name: str,
    file_path: str,
    generation: str,
    cache_dir: Optional[Union[str, os.PathLike]],
) -> Path:
    if cache_dir is None:
        cache_dir = Path(tempfile.gettempdir()) / "policyengine-uk-datasets"
    else:
        cache_dir = Path(cache_dir)

    cache_key = hashlib.sha256(
        f"{bucket_name}\0{file_path}\0{generation}".encode()
    ).hexdigest()
    return cache_dir / cache_key / Path(file_path).name


def _download_blob(blob, local_path: Path) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = local_path.with_name(f"{local_path.name}.tmp")
    try:
        blob.download_to_filename(str(temporary_path))
        os.replace(temporary_path, local_path)
    finally:
        temporary_path.unlink(missing_ok=True)
