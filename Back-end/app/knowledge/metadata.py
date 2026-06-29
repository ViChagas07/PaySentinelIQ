"""Document metadata extraction and hashing."""

import hashlib
from pathlib import Path


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for change detection."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def extract_metadata(file_path: Path, category: str = "") -> dict:
    """Extract basic metadata from a knowledge PDF file."""
    stat = file_path.stat()
    return {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_size": stat.st_size,
        "modified_at": stat.st_mtime,
        "category": category,
        "hash_sha256": compute_file_hash(file_path),
    }
