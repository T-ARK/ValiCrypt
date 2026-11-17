# MediaVault REST API Documentation

Base URL: `/api/v1`

Interactive OpenAPI documentation is available locally at `http://localhost:8000/docs` and `http://localhost:8000/redoc`.

---

## 1. System Endpoints

### `GET /api/v1/health`
Returns system status, service version, and available external binaries.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "MediaVault",
  "version": "1.0.0",
  "environment": "development",
  "capabilities": {
    "image_steganography": true,
    "video_steganography": true,
    "ffmpeg_path": "/usr/bin/ffmpeg",
    "ffprobe_path": "/usr/bin/ffprobe",
    "encryption": "AES-256-GCM",
    "kdf": "Argon2id",
    "max_upload_size_mb": 100,
    "max_payload_size_mb": 50
  }
}
```

---

## 2. Steganography Endpoints

### `POST /api/v1/capacity`
Calculates available payload capacity in bytes for an uploaded carrier media file.

**Request**: `multipart/form-data`
- `carrier`: Binary media file (Image or Video)
- `payload_size`: Optional integer (desired payload size in bytes)

**Response `200 OK`**:
```json
{
  "carrier_type": "IMAGE",
  "carrier_size_bytes": 1048576,
  "available_capacity_bytes": 393208,
  "available_capacity_human": "384.0 KB",
  "sufficient": true,
  "carrier_info": {
    "width": 1024,
    "height": 1024,
    "channels": 3,
    "format": "PNG"
  }
}
```

---

### `POST /api/v1/encode/text`
Encrypts and embeds a confidential text message inside an image or video carrier.

**Request**: `multipart/form-data`
- `carrier`: Media file
- `message`: Text message string (Unicode UTF-8 supported)
- `password`: Encryption passphrase

**Response (Synchronous Image) `200 OK`**:
```json
{
  "success": true,
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "download_url": "/api/v1/download/3fa85f64.../carrier_vault.png",
  "filename": "carrier_vault.png",
  "mime_type": "image/png",
  "carrier_type": "IMAGE",
  "payload_type": "TEXT",
  "output_size_bytes": 1052000,
  "sha256_checksum": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
}
```

**Response (Asynchronous Video) `200 OK`**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "QUEUED",
  "operation": "ENCODE_TEXT",
  "carrier_type": "VIDEO",
  "payload_type": "TEXT",
  "progress": 0,
  "created_at": "2026-11-17T14:00:00Z"
}
```

---

### `POST /api/v1/encode/zip`
Encrypts and embeds a ZIP archive into an image or video carrier.

**Request**: `multipart/form-data`
- `carrier`: Media file
- `payload`: ZIP file (`application/zip`)
- `password`: Encryption passphrase

---

### `POST /api/v1/decode`
Extracts and decrypts a hidden payload from an encoded carrier.

**Request**: `multipart/form-data`
- `carrier`: Encoded media file
- `password`: Decryption passphrase

**Response (Text) `200 OK`**:
```json
{
  "success": true,
  "payload_type": "TEXT",
  "text_content": "Recovered secret message.",
  "sha256_checksum": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  "metadata": {
    "length_chars": 25
  }
}
```

**Response (ZIP) `200 OK`**:
```json
{
  "success": true,
  "payload_type": "ZIP",
  "download_url": "/api/v1/download/c89f81a1.../mediavault_recovered.zip",
  "filename": "mediavault_recovered.zip",
  "file_size_bytes": 45120,
  "sha256_checksum": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "metadata": {
    "file_count": 4,
    "uncompressed_bytes": 120400,
    "files": ["notes.txt", "data/keys.json"]
  }
}
```

---

### `POST /api/v1/verify`
Performs non-authenticated structural media inspection.

**Request**: `multipart/form-data`
- `carrier`: Media file

**Response `200 OK`**:
```json
{
  "carrier_type": "IMAGE",
  "media_format": "PNG",
  "mediavault_version": 1,
  "payload_present": true,
  "payload_type": "ZIP",
  "encryption_algorithm": "AES-256-GCM",
  "kdf_algorithm": "Argon2id",
  "payload_size_bytes": 45120,
  "integrity_status": "VALID",
  "carrier_properties": {
    "width": 800,
    "height": 600,
    "channels": 3,
    "format": "PNG"
  },
  "disclaimer": "Technical verification inspects structural MediaVault preambles..."
}
```

---

## 3. Asynchronous Jobs

### `GET /api/v1/jobs/{job_id}`
Retrieves job progress and download URL.

**Response `200 OK`**:
```json
{
  "id": "e6f47f63-...",
  "status": "COMPLETED",
  "operation": "ENCODE_ZIP",
  "carrier_type": "VIDEO",
  "payload_type": "ZIP",
  "progress": 100,
  "download_url": "/api/v1/download/e6f47f63-.../carrier_vault.mp4",
  "filename": "carrier_vault.mp4",
  "created_at": "2026-11-17T14:10:00Z",
  "completed_at": "2026-11-17T14:10:04Z"
}
```

---

## 4. Structured Error Responses

When an error occurs, MediaVault returns structured JSON:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PASSWORD",
    "message": "Decryption failed. The provided password is invalid or the data is corrupted.",
    "details": {}
  }
}
```

### Standard Error Codes
| Code | HTTP Status | Description |
| ---- | ----------- | ----------- |
| `INVALID_FILE` | 400 | File is unreadable or malformed. |
| `INSUFFICIENT_CAPACITY` | 400 | Payload exceeds carrier capacity. |
| `INVALID_PASSWORD` | 401 | Decryption failed; incorrect passphrase. |
| `OVERSIZED_UPLOAD` | 413 | Upload size exceeds configured safety limit. |
| `UNSUPPORTED_FORMAT` | 415 | Carrier container or codec unsupported. |
| `CORRUPTED_PAYLOAD` | 422 | Tampered data; authentication tag failed. |
| `JOB_NOT_FOUND` | 404 | Job ID not found in database. |
| `SECURITY_VIOLATION` | 400 | Zip Slip path traversal or zip bomb detected. |
