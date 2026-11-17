# MediaVault User Guide

A step-by-step guide for hiding and recovering confidential data using the MediaVault Web UI and Command-Line Interface (CLI).

---

## 1. Quick Start with Web UI

### Workflow A: Hiding Data (Encoding)
1. Navigate to **Hide Data** in the top navigation bar.
2. **Step 1 — Carrier Media**: Drag and drop a PNG image or MP4/MKV video into the carrier zone.
   - The system immediately runs a capacity check to calculate maximum embeddable bytes.
3. **Step 2 — Secret Payload**: Choose between:
   - **Text Message**: Type or paste any Unicode message (English, Malayalam, Hindi, emojis, symbols).
   - **ZIP Archive**: Select any standard ZIP archive containing multiple files or directories.
4. **Step 3 — Passphrase**: Enter a strong password. The real-time strength meter evaluates entropy.
5. Click **Encrypt & Hide in Carrier**.
6. For images, download is ready immediately. For videos, the asynchronous progress tracker monitors progress (Queued -> Processing -> Verifying -> Ready).
7. Download your output carrier file (`*_vault.png` or `*_vault.mp4`).

---

### Workflow B: Recovering Data (Extraction)
1. Navigate to **Extract Data**.
2. Upload the encoded carrier media.
3. (Optional) Click **Detect Payload Metadata** to verify envelope presence without entering a password.
4. Enter the password used during encoding.
5. Click **Extract & Decrypt Payload**.
6. If the payload is text, the message appears with a one-click copy button. If it is a ZIP archive, click **Download ZIP Archive** to save the recovered archive.

---

### Verifying Media
1. Navigate to **Verify Media**.
2. Upload any image or video.
3. Click **Run Structural Verification**.
4. The system inspects headers, detects whether MediaVault data is present, verifies envelope structure, and displays technical carrier dimensions without requiring a password.

---

## 2. MediaVault CLI Usage

The MediaVault CLI is located in `./bin/mediavault`.

### Check Carrier Capacity
```bash
./bin/mediavault capacity --carrier examples/carriers/sample_carrier.png
./bin/mediavault capacity --carrier examples/carriers/sample_carrier.mp4
```

### Hide a Secret Message in an Image
```bash
./bin/mediavault encode-text \
  --carrier examples/carriers/sample_carrier.png \
  --output secret_image.png \
  --message "Top Secret Operational Coordinates"
```
*(You will be prompted for your password securely without echoing to the screen).*

### Recover a Message from an Encoded Image
```bash
./bin/mediavault decode \
  --carrier secret_image.png
```

### Hide a ZIP Archive in a Video
```bash
./bin/mediavault encode \
  --carrier examples/carriers/sample_carrier.mp4 \
  --payload examples/payloads/confidential_archive.zip \
  --output secret_video.mp4
```

### Recover an Archive from an Encoded Video
```bash
./bin/mediavault decode \
  --carrier secret_video.mp4 \
  --output recovered.zip
```

### Verify Media Carrier Without Password
```bash
./bin/mediavault verify --carrier secret_video.mp4
```

---

## 3. Best Practices for Carrier Selection

1. **Images**:
   - Use high-resolution, photographic PNG images with varied textures (natural landscapes, urban scenes).
   - High entropy in pixel color channels offers the best visual fidelity and resistance against heuristic steganalysis.
   - Avoid flat solid-color images.
2. **Videos**:
   - MP4 and MKV containers are supported.
   - Higher resolution and duration provide optimal camouflage.
   - Normal playback is preserved in VLC, QuickTime, browser `<video>`, and mobile players.
