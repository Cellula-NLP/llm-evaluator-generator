from urllib.parse import urlparse

from app.config.settings import get_settings
from app.shared.exceptions import UnsupportedFormatError, ValidationAppError

ALLOWED_SCHEMES = {"http", "https"}

FILE_SIGNATURES = {
    "pdf": [b"%PDF-"],
    "docx": [b"PK\x03\x04"],
    "pptx": [b"PK\x03\x04"],
    "audio": [b"RIFF"],
}


def validate_file_size(content: bytes, kind: str) -> None:
    s = get_settings()
    limit_mb = s.max_audio_size_mb if kind == "audio" else s.max_file_size_mb
    if not content:
        raise ValidationAppError("File is empty")
    if len(content) > limit_mb * 1024 * 1024:
        raise ValidationAppError(f"File exceeds {limit_mb} MB limit")


def sniff_and_verify(content: bytes, kind: str) -> None:
    sigs = FILE_SIGNATURES.get(kind)
    if sigs:
        if not any(content.startswith(sig) for sig in sigs):
            raise UnsupportedFormatError(f"File content does not match declared '{kind}' format")
    elif kind in ("txt", "code"):
        # Verify text files don't contain binary null bytes
        if b"\x00" in content[:1024]:
            raise UnsupportedFormatError(f"File does not appear to be a valid text/{kind} file")


def validate_url(url: str) -> None:
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValidationAppError("Invalid URL")
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValidationAppError(f"URL scheme must be http or https, got '{parsed.scheme}'")
    if not parsed.netloc:
        raise ValidationAppError("URL must have a host")