"""Secure ZIP Archive Handler for MediaVault.

Provides:
  - Strict ZIP signature and structure validation.
  - Zip Slip (Path Traversal) prevention: rejects archives containing '../', absolute paths, or escaping target paths.
  - Decompression Bomb (Zip Bomb) protection: limits maximum uncompressed size and file count.
  - Safe in-memory and temporary directory inspection without extracting dangerous files onto the host.
"""

import io
from pathlib import Path
from typing import List, Tuple
import zipfile
from app.core.config import settings
from app.core.errors import InvalidFileError, SecurityViolationError

MAX_FILES_IN_ZIP = 1000
MAX_UNCOMPRESSED_TOTAL_SIZE = settings.MAX_ZIP_EXTRACTED_SIZE  # Default 100 MB
MAX_COMPRESSION_RATIO = 100  # Max uncompressed / compressed ratio to detect recursive bombs


def validate_zip_archive(zip_bytes: bytes) -> Tuple[int, int, List[str]]:
    """Validates ZIP integrity and scans for security violations.

    Args:
        zip_bytes: Raw bytes of the ZIP archive.

    Returns:
        Tuple of (file_count, total_uncompressed_bytes, list_of_safe_relative_paths).

    Raises:
        InvalidFileError: If the data is not a valid ZIP archive.
        SecurityViolationError: If path traversal or zip bomb characteristics are detected.
    """
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise InvalidFileError("Uploaded file is not a valid ZIP archive.")

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            infolist = zf.infolist()
            if len(infolist) > MAX_FILES_IN_ZIP:
                raise SecurityViolationError(
                    f"ZIP contains {len(infolist)} files, exceeding safety limit of {MAX_FILES_IN_ZIP}."
                )

            total_uncompressed = 0
            safe_filenames = []

            for info in infolist:
                # 1. Zip Slip / Path Traversal Check
                filename = info.filename
                # Normalized path check
                p = Path(filename)
                if p.is_absolute() or ".." in p.parts:
                    raise SecurityViolationError(
                        f"Zip Slip path traversal attempt detected in entry: '{filename}'."
                    )
                # Check for null bytes or windows drive letters
                if "\x00" in filename or (len(filename) >= 2 and filename[1] == ":"):
                    raise SecurityViolationError(
                        f"Malicious filename character in ZIP entry: '{filename}'."
                    )

                # 2. Size & Decompression Bomb Check
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_UNCOMPRESSED_TOTAL_SIZE:
                    raise SecurityViolationError(
                        f"ZIP uncompressed content exceeds maximum safety threshold ({MAX_UNCOMPRESSED_TOTAL_SIZE} bytes)."
                    )

                safe_filenames.append(filename)

            # Check overall compression ratio if archive is non-empty
            compressed_size = len(zip_bytes)
            if compressed_size > 0 and (total_uncompressed / compressed_size) > MAX_COMPRESSION_RATIO:
                raise SecurityViolationError("Suspicious compression ratio detected (potential decompression bomb).")

            # Test archive integrity
            first_bad = zf.testzip()
            if first_bad is not None:
                raise InvalidFileError(f"Corrupted file detected inside ZIP archive: '{first_bad}'.")

            return len(infolist), total_uncompressed, safe_filenames

    except SecurityViolationError:
        raise
    except InvalidFileError:
        raise
    except Exception as exc:
        raise InvalidFileError(f"Failed to inspect ZIP archive: {exc}") from exc


def create_safe_zip(files: dict[str, bytes]) -> bytes:
    """Creates an in-memory ZIP archive from a dictionary of filename -> content bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            zf.writestr(fname, content)
    return buf.getvalue()
