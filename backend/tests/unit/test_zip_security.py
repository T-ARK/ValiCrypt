"""Unit tests for ZIP validation and security protections (Zip Slip, Zip Bomb)."""

import io
import zipfile
import pytest
from app.archive.zip_handler import create_safe_zip, validate_zip_archive
from app.core.errors import InvalidFileError, SecurityViolationError


def test_valid_zip_validation():
    """Verify clean ZIP archives pass validation and file count/sizes are returned."""
    files = {
        "document.txt": b"Hello from inside safe zip!",
        "folder/data.json": b'{"key": "value"}',
    }
    zip_bytes = create_safe_zip(files)
    count, total_uncompressed, safe_names = validate_zip_archive(zip_bytes)
    assert count == 2
    assert total_uncompressed == len(b"Hello from inside safe zip!") + len(b'{"key": "value"}')
    assert "document.txt" in safe_names
    assert "folder/data.json" in safe_names


def test_zip_slip_path_traversal_relative_rejected():
    """ZIP containing relative path traversal (../evil.sh) must be rejected with SecurityViolationError."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../../etc/cron.d/evil.sh", b"malicious code")
    malicious_zip = buf.getvalue()

    with pytest.raises(SecurityViolationError) as exc_info:
        validate_zip_archive(malicious_zip)
    assert "Zip Slip" in str(exc_info.value)


def test_zip_slip_absolute_path_rejected():
    """ZIP containing absolute path (/etc/shadow) must be rejected with SecurityViolationError."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("/root/.ssh/authorized_keys", b"ssh-rsa AAAAB3...")
    malicious_zip = buf.getvalue()

    with pytest.raises(SecurityViolationError) as exc_info:
        validate_zip_archive(malicious_zip)
    assert "Zip Slip" in str(exc_info.value)


def test_corrupted_zip_fails():
    """Non-ZIP data or truncated ZIP must fail with InvalidFileError."""
    with pytest.raises(InvalidFileError):
        validate_zip_archive(b"NOT_A_ZIP_FILE_AT_ALL")

    # Truncated ZIP
    valid_zip = create_safe_zip({"file.txt": b"123"})
    with pytest.raises(InvalidFileError):
        validate_zip_archive(valid_zip[:20])


def test_zip_bomb_size_limit(monkeypatch):
    """ZIP exceeding MAX_UNCOMPRESSED_TOTAL_SIZE must trigger SecurityViolationError."""
    import app.archive.zip_handler as zh
    monkeypatch.setattr(zh, "MAX_UNCOMPRESSED_TOTAL_SIZE", 50)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("large.txt", b"A" * 100)  # 100 bytes > 50 bytes threshold

    bomb_zip = buf.getvalue()
    with pytest.raises(SecurityViolationError) as exc_info:
        validate_zip_archive(bomb_zip)
    assert "exceeds maximum safety threshold" in str(exc_info.value)
