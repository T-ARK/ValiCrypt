"""Utility script to generate sample image and video carriers and test payloads."""

import io
from pathlib import Path
import subprocess
import zipfile
from PIL import Image

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
CARRIERS_DIR = EXAMPLES_DIR / "carriers"
PAYLOADS_DIR = EXAMPLES_DIR / "payloads"
BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
FFMPEG = BIN_DIR / "ffmpeg" if (BIN_DIR / "ffmpeg").exists() else "ffmpeg"

CARRIERS_DIR.mkdir(parents=True, exist_ok=True)
PAYLOADS_DIR.mkdir(parents=True, exist_ok=True)


def generate_image_carrier():
    print("Generating sample image carrier: sample_carrier.png...")
    img = Image.new("RGB", (640, 480), color=(41, 128, 185))
    # Add subtle pattern
    for x in range(0, 640, 20):
        for y in range(0, 480, 20):
            img.putpixel((x, y), (52, 152, 219))
    img.save(CARRIERS_DIR / "sample_carrier.png", format="PNG")
    print(f"✓ Saved {CARRIERS_DIR / 'sample_carrier.png'}")


def generate_video_carrier():
    print("Generating sample video carrier: sample_carrier.mp4...")
    out_mp4 = CARRIERS_DIR / "sample_carrier.mp4"
    cmd = [
        str(FFMPEG),
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=3:size=640x360:rate=24",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=3",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(out_mp4),
        "-y",
    ]
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"✓ Saved {out_mp4}")
    except Exception as exc:
        print(f"Warning: Failed to generate video carrier: {exc}")


def generate_sample_payloads():
    print("Generating sample payloads...")
    # Text payload
    txt_path = PAYLOADS_DIR / "confidential_memo.txt"
    txt_content = (
        "CONFIDENTIAL MEDIAVAULT MEMORANDUM\n"
        "=================================\n"
        "Subject: Project Alpha Deployment & Operational Keys\n"
        "Date: 2026-11-17\n"
        "Classification: STRICTLY RESTRICTED\n\n"
        "Multilingual message:\n"
        "Malayalam: അതീവ രഹസ്യ വിവര ശേഖരണം സ്വാഗതം\n"
        "Hindi: गोपनीय डेटा सुरक्षित रूप से संग्रहीत है\n"
        "Symbols: π ≈ 3.14159, 🛡️, 🔑\n"
    )
    txt_path.write_text(txt_content, encoding="utf-8")
    print(f"✓ Saved {txt_path}")

    # ZIP payload
    zip_path = PAYLOADS_DIR / "confidential_archive.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("passwords.kdbx", b"KDBX_BINARY_SIMULATED_CONTENT_2026")
        zf.writestr("contacts.csv", b"name,email,clearance\nAlice,alice@vault.org,TopSecret\nBob,bob@vault.org,Secret\n")
        zf.writestr("keys/id_ed25519", b"-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAA...\n-----END OPENSSH PRIVATE KEY-----\n")
    zip_path.write_bytes(buf.getvalue())
    print(f"✓ Saved {zip_path}")


if __name__ == "__main__":
    generate_image_carrier()
    generate_video_carrier()
    generate_sample_payloads()
    print("\nSample media generated successfully in examples/ directory.")
