#!/usr/bin/env python3
"""
create_contact_sheet.py — Combines up to 4 images into a 2x2 grid with A, B, C, D labels.
Used by the Subagent to perform one-pass vision QC and correction.

Usage:
    python3 create_contact_sheet.py <img1> <img2> <img3> <img4> -o <output_path>
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def combine_images(img_paths: list[str], output_path: str):
    images = []
    for p in img_paths:
        if not Path(p).exists():
            print(f"WARNING: Image path not found: {p}", file=sys.stderr)
            continue
        try:
            images.append(Image.open(p))
        except Exception as e:
            print(f"WARNING: Failed to open {p}: {e}", file=sys.stderr)

    if not images:
        raise ValueError("No valid images provided to create contact sheet")

    # Resize all to match the first image's size
    target_w, target_h = images[0].size
    resized_images = []
    
    # We label them A, B, C, D
    labels = ["A", "B", "C", "D"]
    
    for idx, img in enumerate(images):
        if img.size != (target_w, target_h):
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Draw label on image copy
        img_copy = img.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Draw a solid background box for the label to ensure readability
        box_size = int(target_h * 0.1) # 10% of height
        box_size = max(40, min(120, box_size))
        
        draw.rectangle([10, 10, 10 + box_size, 10 + box_size], fill="black")
        
        # Attempt to load a default font or fallback
        font = None
        try:
            # Try loading standard sans font sizes
            font = ImageFont.load_default()
        except Exception:
            pass
            
        label_text = labels[idx] if idx < len(labels) else str(idx)
        
        # Draw white text
        # Since default font might be tiny, we draw a larger custom text if possible,
        # otherwise default text.
        try:
            # Draw a thick stroke text using default or custom
            draw.text((15, 12), label_text, fill="white", font=font)
        except Exception:
            draw.text((15, 12), label_text, fill="white")
            
        resized_images.append(img_copy)

    # Padding images if we have less than 4
    while len(resized_images) < 4:
        # Pad with black image
        resized_images.append(Image.new("RGB", (target_w, target_h), color="black"))

    # Create 2x2 grid canvas
    grid_w = target_w * 2
    grid_h = target_h * 2
    grid_img = Image.new("RGB", (grid_w, grid_h), color="black")

    # Paste images
    grid_img.paste(resized_images[0], (0, 0))
    grid_img.paste(resized_images[1], (target_w, 0))
    grid_img.paste(resized_images[2], (0, target_h))
    grid_img.paste(resized_images[3], (target_w, target_h))

    grid_img.save(output_path, "JPEG", quality=85)
    print(f"Contact sheet saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Create a 2x2 contact sheet from images.")
    parser.add_argument("images", nargs="+", help="Paths to 1-4 input images")
    parser.add_argument("-o", "--output", required=True, help="Output image path")

    args = parser.parse_args()
    
    if len(args.images) > 4:
        print("WARNING: More than 4 images provided, only using the first 4", file=sys.stderr)
        args.images = args.images[:4]

    try:
        combine_images(args.images, args.output)
    except Exception as e:
        print(f"ERROR: Failed to combine images: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
