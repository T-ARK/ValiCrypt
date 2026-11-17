"""File download API endpoint."""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.core.errors import InvalidFileError
from app.services.job_service import JobService

router = APIRouter()


@router.get("/download/{job_id}/{filename:path}", tags=["Download"])
async def download_file(job_id: str, filename: str):
    """Securely downloads generated stego media or recovered decrypted files."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise InvalidFileError("Path traversal in filename is prohibited.")
    # Sanitize filename against path traversal
    safe_name = Path(filename).name
    file_path = JobService.get_output_file(job_id, safe_name)

    if not file_path or not file_path.exists():
        raise InvalidFileError(f"File '{filename}' for job '{job_id}' not found.")

    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/octet-stream",
    )
