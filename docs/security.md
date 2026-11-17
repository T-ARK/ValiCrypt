# MediaVault Security Architecture and Cryptographic Design

## 1. Overview: Encryption vs. Steganography

In computer security, **cryptography** and **steganography** solve two distinct problems:
- **Cryptography** ensures **confidentiality and integrity**: an observer can see that communication is occurring, but cannot read the content without the secret key.
- **Steganography** ensures **plausible deniability and concealment**: it obscures the fact that communication is occurring by embedding the data inside ordinary carrier media.

MediaVault integrates both principles in defense-in-depth:
1. Data is **never** embedded in plaintext.
2. The user's password derives a 256-bit symmetric key using **Argon2id**.
3. The payload is encrypted with **AES-256-GCM**, producing authenticated ciphertext and a 128-bit authentication tag.
4. The entire binary envelope header is bound as **Associated Authenticated Data (AAD)**.
5. The resulting ciphertext is embedded into image pixels or video container structures.

> **Important Scientific Principle**:
> MediaVault does not guarantee that a carrier is undetectable. Steganographic detection is an active research area, and media transformations can reveal or destroy hidden payloads.

---

## 2. Password Handling & Key Derivation (Argon2id)

MediaVault uses Argon2id (RFC 9106), the winner of the Password Hashing Competition (PHC), for key derivation.

### Parameters
- **Algorithm**: Argon2id (hybrid data-dependent and data-independent memory access)
- **Time Cost**: 2 iterations (configurable via `ARGON2_TIME_COST`)
- **Memory Cost**: 65,536 KiB (64 MiB) (configurable via `ARGON2_MEMORY_COST`)
- **Parallelism**: 4 lanes (configurable via `ARGON2_PARALLELISM`)
- **Derived Key Length**: 32 bytes (256 bits)
- **Salt**: 16 bytes generated using `os.urandom(16)` per encryption

Argon2id's memory-hardness makes ASIC and GPU password brute-forcing computationally prohibitive by requiring dedicated high-speed RAM for each derivation thread.

Passwords and derived keys are handled solely in memory for the duration of the cryptographic operation and are immediately garbage-collected and overwritten. Passwords are never written to disk, stored in databases, or included in logs.

---

## 3. Authenticated Symmetric Encryption (AES-256-GCM)

MediaVault uses AES-256-GCM (Galois/Counter Mode) via the audited `cryptography` Python library:
- **Key**: 256-bit symmetric key derived from Argon2id.
- **Nonce**: 96-bit (12 bytes) cryptographically random nonce generated via `os.urandom(12)`.
  - **No Nonce Reuse**: Every encryption generates a fresh random nonce.
- **Associated Authenticated Data (AAD)**: The entire 92-byte binary envelope header is supplied to AES-GCM as AAD.
  - If an attacker tampers with salt, KDF costs, or payload type, decryption fails immediately with `InvalidPasswordError` or `CorruptedPayloadError`.
- **Integrity Tag**: 16 bytes (128 bits) appended to the ciphertext.
- **Post-Decryption Checksum**: A SHA-256 hash of the original plaintext is stored inside the encrypted envelope and verified post-decryption.

---

## 4. Binary Envelope Specification

The MediaVault envelope is a 92-byte header followed by the ciphertext:

```text
Offset  Length  Field                  Description
0       4       Magic                  b"MV01"
4       1       Version                uint8 (1)
5       1       Algorithm ID           uint8 (1 = AES-256-GCM)
6       1       KDF ID                 uint8 (1 = Argon2id)
7       1       Payload Type           uint8 (1=Text, 2=ZIP, 3=Binary)
8       4       KDF Time Cost          uint32 big-endian
12      4       KDF Memory Cost        uint32 big-endian (KiB)
16      4       KDF Parallelism        uint32 big-endian
20      16      Salt                   16 bytes random
36      12      Nonce                  12 bytes random
48      8       Plaintext Length       uint64 big-endian
56      4       Ciphertext Length      uint32 big-endian (includes tag)
60      32      Plaintext SHA-256      32 bytes hash
92      N       Ciphertext + Tag       AES-GCM encrypted payload
```

---

## 5. Archive & Upload Hardening

### Zip Slip (Path Traversal) Prevention
When extracting or processing ZIP archives:
- Every filename entry is inspected.
- Relative paths containing `..` or absolute paths (e.g. `/etc/passwd`) are rejected with `SecurityViolationError`.
- Null bytes and drive-letter prefixes are blocked.

### Decompression Bomb Defense
- Archives are checked for maximum uncompressed file count (max 1,000 files).
- Total uncompressed size threshold is enforced (default 100 MB).
- Anomalous compression ratios (> 100:1) trigger rejection.

### Safe Subprocess Execution
FFmpeg and ffprobe are executed using structured argument arrays (`subprocess.run(["ffmpeg", ...])`). No shell interpreters (`shell=True`) are used, eliminating shell injection vectors.
