# MediaVault Threat Model

This document outlines the formal threat analysis for MediaVault according to standard adversarial modeling.

---

## Attacker Profiles

### Attacker A: Inspects the Carrier File
* **Capability**: The adversary can intercept, view, and inspect the carrier image or video file.
* **Goal**: Discover whether secret information is hidden in the file and read the message.
* **Protections**:
  - The carrier remains completely viewable/playable normally without artifacts.
  - The embedded payload is AES-256-GCM ciphertext, which has uniform bit distribution and maximal entropy.
* **Limitations**:
  - Advanced statistical steganalysis (e.g. Chi-Square, sample pair analysis) on images may detect anomalies in LSB bit distributions if the carrier was previously clean. MediaVault does not guarantee mathematical unobservability against dedicated statistical steganalysis.

---

### Attacker B: Knows MediaVault Was Used
* **Capability**: The adversary knows the recipient is using MediaVault and can parse the carrier using MediaVault's format parser.
* **Goal**: Decrypt and extract the confidential payload.
* **Protections**:
  - Without the correct password, extracting the payload yields only AES-256-GCM ciphertext.
  - The 256-bit symmetric key cannot be derived without the user's password.
  - The attacker cannot read the plaintext or verify whether a guessed key is correct without computing Argon2id.
* **Limitations**:
  - The attacker can read non-sensitive structural envelope fields (e.g. payload type: Text/ZIP, KDF salt) from the 92-byte header.

---

### Attacker C: Modifies the Carrier
* **Capability**: Active adversary who tampers with bits in the carrier or attempts man-in-the-middle bit flips.
* **Goal**: Trick the recipient into executing altered data or cause buffer overflows.
* **Protections**:
  - AES-256-GCM provides authenticated encryption with a 128-bit authentication tag.
  - Associated Authenticated Data (AAD) binds the entire envelope header (parameters, salt, lengths) to the cryptographic tag.
  - Any single-bit alteration causes authentication verification to fail immediately.
  - Post-decryption SHA-256 checksum verification provides a secondary integrity layer.
* **Limitations**:
  - Modification corrupts the payload permanently; recovery from damaged carriers is not possible.

---

### Attacker D: Guesses the Password
* **Capability**: Adversary executes offline dictionary or brute-force attacks against the intercepted carrier.
* **Goal**: Find the user password.
* **Protections**:
  - Key derivation relies on Argon2id with 64 MiB memory cost and 2 time iterations per password trial.
  - GPU clusters and ASICs are bandwidth-constrained and cannot parallelize memory-hard operations cheaply.
  - Random 16-byte salts prevent rainbow table or precomputed dictionary attacks.
* **Limitations**:
  - Extremely short or weak passwords (e.g. "123456") remain vulnerable to targeted dictionary attacks if the attacker possesses high compute power. Users must select high-entropy passphrases.

---

### Attacker E: Uploads Malicious Files to MediaVault
* **Capability**: A malicious user uploads malicious payloads (e.g. path traversal ZIP archives, compression bombs, or exploit videos).
* **Goal**: Compromise the server, overwrite system files, or exhaust resources (DoS).
* **Protections**:
  - **Zip Slip Defense**: Archives containing `..`, absolute paths, or special characters are rejected.
  - **Decompression Bomb Protection**: Uncompressed size limits (default 100 MB) and ratio thresholds are enforced.
  - **No Shell Execution**: Subprocess arguments are passed as discrete token arrays.
  - **Ephemeral Lifecycle**: Temporary files are stored in isolated scratch directories and cleaned up.
  - **Upload Size Caps**: Enforced by server configuration (`MAX_UPLOAD_SIZE`, `MAX_PAYLOAD_SIZE`).
* **Limitations**:
  - Users are responsible for configuring appropriate reverse proxy rate limiting in public multi-tenant deployments.
