"""Screenshot the PDF's cover/divider sources (screen render of the print layout) for review."""
import subprocess
import sys
from pathlib import Path

from build import CHROME

T = Path(__file__).resolve().parent / "pdf_tmp"
for name, h in (("cover", 540 * 3), ("dividers", 540 * int(sys.argv[1] if len(sys.argv) > 1 else 4))):
    subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=1", "--virtual-time-budget=8000",
                    f"--window-size=960,{h}", f"--screenshot={T / (name + '.png')}", (T / f"{name}.html").as_uri()],
                   capture_output=True, timeout=120)
    print(T / (name + ".png"))
