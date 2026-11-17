"""MediaVault Command Line Interface (CLI).

Provides commands for encoding, decoding, inspecting capacity, and verifying media carriers.
Passwords are prompted securely by default to prevent leaking into shell history.
"""

from getpass import getpass
import os
from pathlib import Path
import sys
import click
from app.archive.zip_handler import validate_zip_archive
from app.core.config import settings
from app.crypto.encryption import decrypt_payload, encrypt_payload
from app.crypto.models import PayloadType
from app.media.video import inspect_video
from app.services.decode_service import DecodeService
from app.services.verify_service import VerifyService
from app.steganography.image import (
    calculate_image_capacity,
    embed_payload_in_image,
    extract_payload_from_image,
    inspect_image_carrier,
)
from app.steganography.video import (
    calculate_video_capacity,
    embed_payload_in_video,
    extract_payload_from_video,
)


def prompt_password(password_opt: str | None) -> str:
    """Gets password from option, environment, or secure hidden prompt."""
    if password_opt:
        return password_opt
    env_pwd = os.getenv("VALICRYPT_PASSWORD") or os.getenv("MEDIAVAULT_PASSWORD")
    if env_pwd:
        return env_pwd
    pwd = click.prompt("Enter ValiCrypt Password", hide_input=True)
    if not pwd:
        click.echo("Error: Password cannot be empty.", err=True)
        sys.exit(1)
    return pwd


def is_video_file(path: Path) -> bool:
    return path.suffix.lower() in (".mp4", ".mkv", ".mov", ".webm", ".m4v")


@click.group()
@click.version_option(version=settings.VERSION, prog_name="ValiCrypt")
def cli():
    """ValiCrypt CLI: Steganographic payload hiding and recovery tool."""
    pass


@cli.command("capacity")
@click.option("--carrier", "-c", required=True, type=click.Path(exists=True, path_type=Path), help="Carrier file path.")
def capacity_cmd(carrier: Path):
    """Calculates available payload capacity in a carrier file."""
    if is_video_file(carrier):
        props = inspect_video(carrier)
        cap = calculate_video_capacity(carrier)
        click.echo(f"Carrier: Video ({props.container.upper()}, {props.width}x{props.height})")
        click.echo(f"Usable Payload Capacity: {cap / (1024*1024):.2f} MB ({cap} bytes)")
    else:
        w, h, c, fmt = inspect_image_carrier(carrier.read_bytes())
        cap = calculate_image_capacity(w, h, c)
        click.echo(f"Carrier: Image ({fmt}, {w}x{h}, {c} channels)")
        click.echo(f"Usable Payload Capacity: {cap / 1024:.2f} KB ({cap} bytes)")


@cli.command("encode-text")
@click.option("--carrier", "-c", required=True, type=click.Path(exists=True, path_type=Path), help="Input carrier image/video.")
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path), help="Output destination file.")
@click.option("--message", "-m", help="Secret message to hide (prompts if omitted).")
@click.option("--password", "-p", help="Encryption password (prompts securely if omitted).")
def encode_text_cmd(carrier: Path, output: Path, message: str | None, password: str | None):
    """Encrypts and hides a secret text message inside an image or video carrier."""
    if not message:
        message = click.prompt("Enter secret message")
    pwd = prompt_password(password)

    click.echo(f"Encrypting message with Argon2id + AES-256-GCM...")
    plaintext = message.encode("utf-8")
    envelope = encrypt_payload(plaintext, pwd, PayloadType.TEXT)

    if is_video_file(carrier):
        click.echo(f"Embedding into video carrier: {carrier.name}...")
        embed_payload_in_video(carrier, output, envelope)
    else:
        click.echo(f"Embedding into image carrier: {carrier.name}...")
        carrier_bytes = carrier.read_bytes()
        encoded = embed_payload_in_image(carrier_bytes, envelope)
        output.write_bytes(encoded)

    click.echo(f"✓ Success! Encrypted message embedded into: {output}")


@cli.command("encode")
@click.option("--carrier", "-c", required=True, type=click.Path(exists=True, path_type=Path), help="Input carrier image/video.")
@click.option("--payload", "-f", required=True, type=click.Path(exists=True, path_type=Path), help="Input ZIP archive payload.")
@click.option("--output", "-o", required=True, type=click.Path(path_type=Path), help="Output destination file.")
@click.option("--password", "-p", help="Encryption password (prompts securely if omitted).")
def encode_zip_cmd(carrier: Path, payload: Path, output: Path, password: str | None):
    """Encrypts and hides a ZIP archive inside an image or video carrier."""
    zip_bytes = payload.read_bytes()
    click.echo("Validating ZIP archive...")
    validate_zip_archive(zip_bytes)

    pwd = prompt_password(password)
    click.echo(f"Encrypting ZIP payload with Argon2id + AES-256-GCM...")
    envelope = encrypt_payload(zip_bytes, pwd, PayloadType.ZIP)

    if is_video_file(carrier):
        click.echo(f"Embedding into video carrier: {carrier.name}...")
        embed_payload_in_video(carrier, output, envelope)
    else:
        click.echo(f"Embedding into image carrier: {carrier.name}...")
        carrier_bytes = carrier.read_bytes()
        encoded = embed_payload_in_image(carrier_bytes, envelope)
        output.write_bytes(encoded)

    click.echo(f"✓ Success! Encrypted ZIP archive embedded into: {output}")


@cli.command("decode")
@click.option("--carrier", "-c", required=True, type=click.Path(exists=True, path_type=Path), help="Input encoded carrier file.")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output destination for recovered file/message.")
@click.option("--password", "-p", help="Decryption password (prompts securely if omitted).")
def decode_cmd(carrier: Path, output: Path | None, password: str | None):
    """Extracts and decrypts hidden payload from an image or video carrier."""
    pwd = prompt_password(password)

    click.echo(f"Extracting and decrypting from {carrier.name}...")
    if is_video_file(carrier):
        result = DecodeService.decode_from_video(carrier, pwd)
    else:
        result = DecodeService.decode_from_image(carrier.read_bytes(), pwd)

    click.echo(f"✓ Payload Type: {result.payload_type}")
    click.echo(f"✓ Checksum SHA-256: {result.sha256_checksum}")

    if result.payload_type == "TEXT":
        click.echo("\n--- RECOVERED MESSAGE ---")
        click.echo(result.text_content)
        click.echo("-------------------------\n")
        if output:
            output.write_text(result.text_content or "", encoding="utf-8")
            click.echo(f"Saved message to: {output}")
    else:
        # ZIP or Binary
        if not output:
            output = Path(result.filename or "recovered.zip")
        # Read the file saved by DecodeService
        saved_file = settings.TEMP_DIRECTORY / "outputs" / result.download_url.split("/")[-2] / result.download_url.split("/")[-1]
        output.write_bytes(saved_file.read_bytes())
        click.echo(f"✓ Recovered archive written to: {output}")


@cli.command("verify")
@click.option("--carrier", "-c", required=True, type=click.Path(exists=True, path_type=Path), help="Carrier file path.")
def verify_cmd(carrier: Path):
    """Inspects carrier file and verifies MediaVault payload presence without password."""
    if is_video_file(carrier):
        res = VerifyService.verify_video(carrier)
    else:
        res = VerifyService.verify_image(carrier.read_bytes())

    click.echo(f"Media Type: {res.carrier_type} ({res.media_format})")
    click.echo(f"Payload Present: {'Yes' if res.payload_present else 'No'}")
    if res.payload_present:
        click.echo(f"MediaVault Version: {res.mediavault_version}")
        click.echo(f"Payload Type: {res.payload_type}")
        click.echo(f"Encryption: {res.encryption_algorithm}")
        click.echo(f"KDF: {res.kdf_algorithm}")
        click.echo(f"Payload Size: {res.payload_size_bytes} bytes")
        click.echo(f"Integrity Status: {res.integrity_status}")


if __name__ == "__main__":
    cli()
