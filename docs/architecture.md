# MediaVault System Architecture

MediaVault is designed as a modular, secure steganography and cryptography platform.

---

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Client Tier"]
        UI["React + TypeScript SPA"]
        CLI["MediaVault CLI"]
    end

    subgraph API["Backend API (FastAPI)"]
        Router["REST API Router /api/v1"]
        AuthMiddleware["Security & Sanitization Middleware"]
        AsyncWorker["Asynchronous Job Worker"]
    end

    subgraph CoreServices["Core Domain Services"]
        EncodeSvc["Encode Service"]
        DecodeSvc["Decode Service"]
        VerifySvc["Verify Service"]
        JobSvc["Job Service"]
    end

    subgraph SecurityEngines["Security & Cryptographic Engines"]
        Argon2["Argon2id KDF"]
        AESGCM["AES-256-GCM AEAD"]
        ZipSec["ZipSlip & Bomb Validator"]
    end

    subgraph StegoEngines["Steganography Engines"]
        ImageStego["NumPy Vectorized LSB Engine"]
        VideoStego["ISO-BMFF UUID / FFmpeg MKV Engine"]
    end

    subgraph Storage["Storage Tier"]
        DB[(SQLite Metadata DB)]
        Scratch["Ephemeral Temp Scratch"]
    end

    UI --> Router
    CLI --> CoreServices
    Router --> AuthMiddleware
    AuthMiddleware --> CoreServices
    CoreServices --> SecurityEngines
    CoreServices --> StegoEngines
    CoreServices --> JobSvc
    JobSvc --> DB
    JobSvc --> AsyncWorker
    AsyncWorker --> StegoEngines
    StegoEngines --> Scratch
```

---

## Core Workflows

### Workflow A: Hiding Data (Encoding)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant App as MediaVault Frontend / API
    participant Crypto as Argon2id + AES-256-GCM
    participant Stego as Steganography Engine
    participant Media as Output Media Carrier

    User->>App: Upload Carrier + Payload (Text/ZIP) + Password
    App->>App: Inspect carrier capacity and validate payload
    App->>Crypto: Derive 256-bit Key via Argon2id (Salt, Nonce)
    Crypto->>Crypto: Encrypt payload with AES-256-GCM + Header AAD
    Crypto-->>App: Return Encrypted Envelope (92B Header + Ciphertext)
    App->>Stego: Embed Envelope into Carrier Media
    Stego->>Stego: Immediate In-Memory Roundtrip Validation
    Stego->>Media: Produce Playable/Viewable Output Carrier
    Media-->>User: Verified Output Download
```

### Workflow B: Recovering Data (Extraction)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant App as MediaVault Frontend / API
    participant Stego as Steganography Engine
    participant Crypto as Argon2id + AES-256-GCM
    participant ZipHandler as Safe Archive Handler

    User->>App: Upload Carrier + Password
    App->>Stego: Scan & extract MediaVault Envelope
    Stego-->>App: Raw Encrypted Envelope Bytes
    App->>Crypto: Derive Key via Argon2id using Envelope Salt
    Crypto->>Crypto: Verify AES-GCM Tag and AAD Header
    alt Authentication Valid
        Crypto->>Crypto: Check SHA-256 Plaintext Hash
        alt Text Mode
            Crypto-->>User: Return Plaintext UTF-8 Message
        else ZIP Mode
            Crypto->>ZipHandler: Scan for ZipSlip & Decompression Bomb
            ZipHandler-->>User: Download Safe Recovered Archive
        end
    else Authentication Failed
        Crypto-->>User: Safe 401 Invalid Password Error (No Plaintext)
    end
```

---

## Subsystem Details

### 1. Image Steganography Engine
- Lossless format support: PNG (primary), BMP, TIFF.
- NumPy vectorized bit-plane modification on RGB channels (channels 0, 1, 2).
- Alpha channel (channel 3) left untouched to guarantee zero transparency distortion.
- Preamble marker: 8 bytes (`b"MVLT"` + 4-byte uint32 payload length).

### 2. Video Steganography Engine
- Container support:
  - **MP4 / MOV**: ISO/IEC 14496-12 standard `uuid` User-defined Extension Box. Preserves 100% video and audio streams via `-c copy` without re-encoding.
  - **MKV / WebM**: Native FFmpeg attachment stream (`-attach`).
- Every embedding operation executes an automated playback test via `ffmpeg -v error -i <file> -f null -` to verify normal playback before releasing output.

### 3. Archive Security Subsystem
- In-memory ZIP inspection before encryption and after extraction.
- Rejects directory traversal paths (`../`) and absolute paths (`/etc/`).
- Decompression bomb threshold: maximum 100 MB uncompressed and maximum 1,000 files.
