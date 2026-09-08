"""Read-only input probe and deliberately constructed identity counterexamples.

All created files stay beside this script. Run with Python 3.12 + Pillow 12.3.
This is experimental evidence, not a production duplicate-removal utility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import PIL
from PIL import Image, ImageOps


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def input_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha256(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()}


def pixel_identity(im: Image.Image) -> str:
    # Explicit, versioned normalization: RGB8 with size; no ICC color conversion.
    rgb = im.convert("RGB")
    descriptor = f"RGB8:{rgb.width}x{rgb.height}:".encode("ascii")
    return sha256(descriptor + rgb.tobytes())


def ahash_demo(im: Image.Image) -> str:
    # Independent tiny demonstrator of average-luminance hashing, not ImageHash.
    values = list(im.convert("L").resize((8, 8), Image.Resampling.LANCZOS).get_flattened_data())
    average = sum(values) / len(values)
    bits = "".join("1" if value > average else "0" for value in values)
    return f"{int(bits, 2):016x}"


def inspect(path: Path, root: Path) -> dict:
    data = path.read_bytes()
    result = {"path": path.relative_to(root).as_posix(), "bytes": len(data),
              "sha256": sha256(data), "suffix": path.suffix.lower(),
              "header_hex": data[:12].hex()}
    try:
        with Image.open(path) as im:
            result.update(detected_format=im.format, encoded_size=list(im.size))
            im.verify()
        # PNG getexif() may load the stream; verify must have its own open.
        with Image.open(path) as im:
            exif = im.getexif()
            # TIFF load consumes its orientation; preserve raw tags first.
            if im.format == "TIFF":
                result["encoded_size"] = [int(im.tag_v2[256]), int(im.tag_v2[257])]
            nested = exif.get_ifd(34665) if 34665 in exif else {}
            result["orientation"] = exif.get(274)
            result["date_time_original"] = nested.get(36867, exif.get(36867))
            result["offset_time_original"] = nested.get(36881, exif.get(36881))
            result["date_time_ifd0"] = exif.get(306)
            im.load()
            result["raw_pixel_sha256"] = pixel_identity(im)
            shown = ImageOps.exif_transpose(im)
            result["display_size"] = list(shown.size)
            result["display_pixel_sha256"] = pixel_identity(shown)
            result["display_ahash_demo"] = ahash_demo(shown)
            result["orientation_after_transpose"] = shown.getexif().get(274)
        result["decode"] = "ok"
    except Exception as exc:
        result["decode"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True, type=Path)
    args = parser.parse_args()
    inputs = args.inputs.resolve(strict=True)
    lab = Path(__file__).resolve().parent
    assert not lab.is_relative_to(inputs), "Output directory must be outside inputs"
    fixture_dir = lab / "fixtures"
    fixture_dir.mkdir(exist_ok=True)
    before = input_hashes(inputs)

    # Variants are explicitly synthesized, not claimed as defects in the inputs.
    dated = (inputs / "session A" / "dated.jpg").read_bytes()
    (fixture_dir / "jpeg_with_png_extension.png").write_bytes(dated)
    comment = b"identity experiment: metadata-only COM segment"
    assert dated[:2] == b"\xff\xd8"
    com = b"\xff\xfe" + (len(comment) + 2).to_bytes(2, "big") + comment
    (fixture_dir / "jpeg_with_comment.jpg").write_bytes(dated[:2] + com + dated[2:])
    with Image.open(inputs / "회전" / "rotated.jpg") as im:
        shown = ImageOps.exif_transpose(im)
        shown.save(fixture_dir / "normalized_rotated.png")
    Image.new("RGB", (16, 12), (255, 0, 0)).save(fixture_dir / "solid_red.png")
    Image.new("RGB", (16, 12), (0, 0, 255)).save(fixture_dir / "solid_blue.png")

    original = [inspect(p, inputs) for p in sorted(inputs.rglob("*")) if p.is_file()]
    variants = [inspect(p, fixture_dir) for p in sorted(fixture_dir.iterdir()) if p.is_file()]
    original_by_path = {r["path"]: r for r in original}
    variant_by_path = {r["path"]: r for r in variants}
    buckets = defaultdict(list)
    for item in original:
        buckets[(item["bytes"], item["sha256"])].append(item["path"])
    groups = []
    for (_, digest), paths in sorted(buckets.items()):
        if len(paths) > 1:
            anchor = (inputs / paths[0]).read_bytes()
            groups.append({"sha256": digest, "paths": paths,
                           "byte_comparison_equal": all((inputs / p).read_bytes() == anchor for p in paths)})

    d = original_by_path["session A/dated.jpg"]
    r = original_by_path["회전/rotated.jpg"]
    renamed = variant_by_path["jpeg_with_png_extension.png"]
    comment_record = variant_by_path["jpeg_with_comment.jpg"]
    normalized = variant_by_path["normalized_rotated.png"]
    red, blue = (variant_by_path[n] for n in ("solid_red.png", "solid_blue.png"))
    wrong_order = {}
    try:
        with Image.open(inputs / "plain.png") as im:
            im.getexif()
            im.verify()
        wrong_order["status"] = "no_failure_in_this_runtime"
    except Exception as exc:
        wrong_order = {"status": "reproduced", "error": f"{type(exc).__name__}: {exc}"}
    checks = {
        "exact_original_group_count_one": len(groups) == 1,
        "original_group_has_byte_confirmation": all(g["byte_comparison_equal"] for g in groups),
        "renamed_still_exact_bytes": d["sha256"] == renamed["sha256"],
        "renamed_detects_jpeg_despite_png_suffix": renamed.get("detected_format") == "JPEG" and renamed["suffix"] == ".png",
        "comment_changes_bytes": d["sha256"] != comment_record["sha256"],
        "comment_keeps_decoded_display_pixels": d.get("display_pixel_sha256") is not None and d["display_pixel_sha256"] == comment_record.get("display_pixel_sha256"),
        "orientation_normalization_changes_bytes": r["sha256"] != normalized["sha256"],
        "orientation_normalization_keeps_display_pixels": r.get("display_pixel_sha256") is not None and r["display_pixel_sha256"] == normalized.get("display_pixel_sha256"),
        "different_colors_different_pixels": red.get("display_pixel_sha256") != blue.get("display_pixel_sha256"),
        "different_colors_same_average_hash": red.get("display_ahash_demo") is not None and red["display_ahash_demo"] == blue.get("display_ahash_demo"),
        "truncated_jpeg_does_not_decode": original_by_path["broken/truncated.jpg"]["decode"] == "error",
        "plain_png_decodes_after_order_fix": original_by_path["plain.png"]["decode"] == "ok",
        "inputs_unchanged": before == input_hashes(inputs),
    }
    report = {"runtime": {"pillow": PIL.__version__}, "pixel_normalization": "RGB8 + width/height + EXIF transpose; ICC not applied",
              "input_files": original, "original_exact_groups": groups,
              "synthesized_variants": variants, "checks": checks, "input_hashes": before,
              "wrong_order_png_failure": wrong_order}
    output = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    (lab / "observations.json").write_text(output, encoding="utf-8")
    print(json.dumps({"checks": checks, "groups": groups}, ensure_ascii=False, indent=2))
    assert all(checks.values()), "A probe expectation failed; examine observations.json"


if __name__ == "__main__":
    main()
