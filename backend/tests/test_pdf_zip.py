import io
import sys
import zipfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pdf import build_pdf_zip_bytes


def test_build_pdf_zip_bytes_contains_pdf():
    pdf_data = b"%PDF-1.4\nmock pdf bytes\n%%EOF"

    zip_data = build_pdf_zip_bytes(pdf_data)

    assert zip_data.startswith(b"PK")
    with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zip_file:
        assert zip_file.namelist() == ["images.pdf"]
        assert zip_file.read("images.pdf") == pdf_data
