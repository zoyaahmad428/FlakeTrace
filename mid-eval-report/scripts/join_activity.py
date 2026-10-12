"""Joins the two halves of the run_steps activity diagram side by side into one figure.

Run from the repository root after rendering diagrams/m2/search_activity.puml:
    py mid-eval-report/scripts/join_activity.py
"""

from pathlib import Path

from PIL import Image

FIG = Path(__file__).resolve().parents[1] / "figures" / "m2"
GAP = 30

left, right = (Image.open(FIG / f"search_activity_{part}.png").convert("RGB") for part in "ab")
out = Image.new("RGB", (left.width + GAP + right.width, max(left.height, right.height)), "white")
out.paste(left, (0, 0))
out.paste(right, (left.width + GAP, 0))
out.save(FIG / "search_activity.png")
print(f"wrote {FIG / 'search_activity.png'} {out.size}")
