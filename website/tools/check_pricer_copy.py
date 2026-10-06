"""Fail if the site's copy of the pricer differs from the project's tested one.

    python3 website/tools/check_pricer_copy.py

website/api/_dh/models.py exists only because a Vercel function ships just the deployed website/ folder;
it must stay a byte-for-byte copy of legacy_streamlit_site/models.py. After changing the original, copy it:
    cp legacy_streamlit_site/models.py website/api/_dh/models.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
original, copy = ROOT / "legacy_streamlit_site" / "models.py", ROOT / "website" / "api" / "_dh" / "models.py"
if original.read_bytes() != copy.read_bytes():
    sys.exit(f"{copy.relative_to(ROOT)} differs from {original.relative_to(ROOT)}: copy the original over it.")
print("pricer copy matches legacy_streamlit_site/models.py")
