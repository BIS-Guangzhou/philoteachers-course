# lpc_to_atlas.py   
# Usage example:
# python lpc_to_atlas.py --image "C:\path\to\your\lpc_spritesheet.png" --id new_character \
#   --front-row 10 --left-row 9 --right-row 11 --back-row 8 --out "C:\out\folder"
# Adjust rows to match your sheet layout; defaults assume 64x64, 13 columns.

import json
import math
import os
from pathlib import Path
from PIL import Image
import argparse

def slice_frames(sheet, frame_w, frame_h, row, start_col, count):
    frames = []
    for i in range(count):
        x = (start_col + i) * frame_w
        y = row * frame_h
        box = (x, y, x + frame_w, y + frame_h)
        frames.append(sheet.crop(box))
    return frames

def paste_frames_to_atlas(frames, frame_w, frame_h, cols):
    rows = math.ceil(len(frames) / cols)
    atlas_w = cols * frame_w
    atlas_h = rows * frame_h
    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    rects = []
    for idx, frame in enumerate(frames):
        cx = idx % cols
        cy = idx // cols
        x = cx * frame_w
        y = cy * frame_h
        atlas.paste(frame, (x, y))
        rects.append((x, y, frame_w, frame_h))
    return atlas, rects

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True, help="Path to LPC spritesheet PNG")
    p.add_argument("--id", required=True, help="Frame id/prefix (e.g., ada_lovelace)")
    p.add_argument("--frame-width", type=int, default=64)
    p.add_argument("--frame-height", type=int, default=64)
    p.add_argument("--cols", type=int, default=13, help="Columns in the LPC sheet")
    p.add_argument("--start-col", type=int, default=0, help="Start column for walk cycles")
    p.add_argument("--walk-frames", type=int, default=9, help="Frames per direction (use 8 if your sheet has 8; code may need end: 7)")
    p.add_argument("--front-row", type=int, required=True)
    p.add_argument("--left-row", type=int, required=True)
    p.add_argument("--right-row", type=int, required=True)
    p.add_argument("--back-row", type=int, required=True)
    p.add_argument("--static-col", type=int, default=0, help="Which column to use as static pose")
    p.add_argument("--atlas-cols", type=int, default=10, help="Columns to arrange in output atlas")
    p.add_argument("--out", required=True, help="Output directory for atlas.png and atlas.json")
    args = p.parse_args()

    sheet = Image.open(args.image).convert("RGBA")

    # Collect frames in final order and names
    name_order = []
    images = []

    # Static poses
    for dir_key, row in [("front", args.front_row), ("back", args.back_row),
                         ("left", args.left_row), ("right", args.right_row)]:
        x = args.static_col * args.frame_width
        y = row * args.frame_height
        static_img = sheet.crop((x, y, x + args.frame_width, y + args.frame_height))
        images.append(static_img)
        name_order.append(f"{args.id}-{dir_key}")

    # Walk cycles
    for dir_key, row in [("front", args.front_row), ("back", args.back_row),
                         ("left", args.left_row), ("right", args.right_row)]:
        frames = slice_frames(sheet, args.frame_width, args.frame_height, row, args.start_col, args.walk_frames)
        # If your LPC has only 8 frames, you can duplicate one to make 9
        if args.walk_frames == 9 and len(frames) == 8:
            frames.append(frames[-1])
        for i, img in enumerate(frames):
            images.append(img)
            name_order.append(f"{args.id}-{dir_key}-walk-{i:04d}")

    # Build atlas image and rects
    atlas, rects = paste_frames_to_atlas(images, args.frame_width, args.frame_height, args.atlas_cols)

    # Build JSON (TexturePacker JSON Hash-like)
    frames_json = {}
    for name, (x, y, w, h) in zip(name_order, rects):
        frames_json[name] = {
            "frame": {"x": x, "y": y, "w": w, "h": h},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
            "sourceSize": {"w": w, "h": h}
        }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    atlas_path = out_dir / "atlas.png"
    json_path = out_dir / "atlas.json"

    atlas.save(atlas_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"frames": frames_json, "meta": {"image": "atlas.png"}}, f, indent=2)

    print(f"Wrote {atlas_path}")
    print(f"Wrote {json_path}")

if __name__ == "__main__":
    main()