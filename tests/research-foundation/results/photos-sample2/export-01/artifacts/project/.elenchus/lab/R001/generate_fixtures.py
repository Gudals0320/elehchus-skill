"""Create named, synthetic failure cases only inside this lab. Never edit input."""
from pathlib import Path
import hashlib
import json
from PIL import Image, PngImagePlugin

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)]


def build(root=None):
    root = root or HERE / "fixtures"
    root = Path(root).resolve()
    if not root.is_relative_to(HERE):
        raise ValueError("fixtures must remain in R001 lab")
    if root.exists():
        raise FileExistsError("fixtures already exist; use their manifest or a new lab directory")
    root.mkdir(parents=True)
    inputs = PROJECT / "inputs"
    (root / "tail_truncated.jpg").write_bytes((inputs / "session A" / "dated.jpg").read_bytes()[:-20])
    (root / "disguised.jpg").write_bytes((inputs / "plain.png").read_bytes())
    (root / "empty.jpg").write_bytes(b"")
    base = Image.new("RGB", (3, 2))
    base.putdata(COLORS)
    base.save(root / "base.png")
    comment = PngImagePlugin.PngInfo()
    comment.add_text("Comment", "Synthetic metadata-only variant; no personal data")
    base.save(root / "metadata_changed.png", pnginfo=comment)
    for orientation in range(1, 9):
        exif = Image.Exif()
        exif[274] = orientation
        base.save(root / f"orientation_{orientation}.png", exif=exif)
        base.save(root / f"orientation_{orientation}.tiff", exif=exif)
    cases = {
        "invalid_date.jpg": {34665: {36867: "2024:02:30 10:20:30", 36881: "+09:00"}},
        "naive_date.jpg": {34665: {36867: "2024:07:15 10:20:30"}},
        "offset_subsecond.jpg": {34665: {36867: "2024:01:01 00:15:00", 36881: "+09:00", 37521: "125"}},
        "invalid_offset.jpg": {34665: {36867: "2024:07:15 10:20:30", 36881: "+25:00"}},
        "conflicting_dates.jpg": {36867: "2023:01:01 00:00:00", 34665: {36867: "2024:01:01 00:00:00"}},
        "modify_date.jpg": {306: "2024:01:01 00:15:00", 34665: {36880: "+09:00"}},
        "invalid_orientation.jpg": {274: 9},
    }
    for name, tags in cases.items():
        exif = Image.Exif()
        for tag, value in tags.items():
            exif[tag] = value
        base.save(root / name, exif=exif, quality=95)
    base.save(root / "multi.tiff", save_all=True, append_images=[Image.new("RGB", (2, 3), (10, 20, 30))])
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir())}
    (root / "manifest.json").write_text(json.dumps({"origin": "programmatic synthetic variants; input originals untouched",
                                                     "derived_inputs": ["session A/dated.jpg", "plain.png"],
                                                     "sha256": manifest}, indent=2), encoding="utf-8")
    return root


if __name__ == "__main__":
    print(build())
