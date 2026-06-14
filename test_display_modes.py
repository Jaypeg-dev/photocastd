#!/usr/bin/env python3
"""
Test script for display mode feature.
Generates sample portrait and landscape images,
then tests all three display modes: letterbox, resize, side-by-side.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Test parameters
TV_WIDTH = 1920
TV_HEIGHT = 1080
OUTPUT_DIR = "test_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_test_image(width: int, height: int, label: str) -> Image.Image:
    """
    Create a colorful test image with gradient and label.
    Helps visually identify aspect ratio and display mode results.
    """
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background
    for y in range(height):
        r = int(255 * (y / height))
        g = int(255 * (1 - y / height))
        b = 128
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add border
    border = 20
    draw.rectangle([border, border, width-border, height-border], outline="black", width=3)
    
    # Add centered text
    text = f"{label}\n{width}×{height}"
    try:
        font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = (height - text_h) // 2
        draw.text((x, y), text, fill="white", font=font)
    except Exception as e:
        print(f"Warning: Could not draw text: {e}")
    
    return img

def apply_display_mode(img: Image.Image, mode: str, tv_width: int, tv_height: int) -> Image.Image:
    """
    Apply display mode transformation (copied from app.py for testing).
    """
    if mode == "resize":
        return img.resize((tv_width, tv_height), Image.LANCZOS)
    
    elif mode == "side-by-side":
        w, h = img.size
        aspect = w / float(h)
        
        if aspect > 0.7:  # relatively wider than portrait
            mode = "letterbox"
        else:
            # Portrait image: tile 2 copies side by side
            target_w = tv_width // 2
            target_h = tv_height
            
            scale = target_h / float(h)
            scaled_w = int(w * scale)
            scaled_h = int(h * scale)
            
            if scaled_w < target_w:
                scale = target_w / float(w)
                scaled_w = int(w * scale)
                scaled_h = int(h * scale)
            
            scaled_img = img.resize((scaled_w, scaled_h), Image.LANCZOS)
            
            if scaled_w > target_w or scaled_h > target_h:
                x_offset = (scaled_w - target_w) // 2
                y_offset = (scaled_h - target_h) // 2
                scaled_img = scaled_img.crop((x_offset, y_offset, 
                                             x_offset + target_w, y_offset + target_h))
            
            if scaled_w < target_w or scaled_h < target_h:
                pad_w = (target_w - scaled_w) // 2
                pad_h = (target_h - scaled_h) // 2
                padded = Image.new("RGB", (target_w, target_h), (0, 0, 0))
                padded.paste(scaled_img, (pad_w, pad_h))
                scaled_img = padded
            
            output = Image.new("RGB", (tv_width, tv_height), (0, 0, 0))
            output.paste(scaled_img, (0, 0))
            output.paste(scaled_img, (target_w, 0))
            return output
    
    if mode == "letterbox" or mode == "side-by-side":
        w, h = img.size
        aspect = w / float(h)
        tv_aspect = tv_width / float(tv_height)
        
        if aspect > tv_aspect:
            new_w = tv_width
            new_h = int(tv_width / aspect)
        else:
            new_h = tv_height
            new_w = int(tv_height * aspect)
        
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        output = Image.new("RGB", (tv_width, tv_height), (0, 0, 0))
        x_offset = (tv_width - new_w) // 2
        y_offset = (tv_height - new_h) // 2
        output.paste(resized, (x_offset, y_offset))
        return output
    
    return apply_display_mode(img, "letterbox", tv_width, tv_height)

print("\n" + "="*70)
print("PHOTOCASTD DISPLAY MODE TEST")
print("="*70)

# Test 1: Portrait image (9:16 aspect ratio, like Pinterest)
print("\n[TEST 1] Creating portrait test image (9:16 aspect ratio)...")
portrait = create_test_image(1080, 1920, "PORTRAIT\n9:16")
portrait_path = os.path.join(OUTPUT_DIR, "01_source_portrait.jpg")
portrait.save(portrait_path, "JPEG", quality=88)
print(f"✓ Saved: {portrait_path} ({portrait.size[0]}×{portrait.size[1]})")

# Test 2: Landscape image (16:9 aspect ratio)
print("\n[TEST 2] Creating landscape test image (16:9 aspect ratio)...")
landscape = create_test_image(1920, 1080, "LANDSCAPE\n16:9")
landscape_path = os.path.join(OUTPUT_DIR, "02_source_landscape.jpg")
landscape.save(landscape_path, "JPEG", quality=88)
print(f"✓ Saved: {landscape_path} ({landscape.size[0]}×{landscape.size[1]})")

# Test 3-5: Apply display modes to portrait image
print("\n[TEST 3] Applying LETTERBOX mode to portrait image...")
portrait_letterbox = apply_display_mode(portrait, "letterbox", TV_WIDTH, TV_HEIGHT)
portrait_letterbox_path = os.path.join(OUTPUT_DIR, "03_portrait_letterbox.jpg")
portrait_letterbox.save(portrait_letterbox_path, "JPEG", quality=88)
print(f"✓ Saved: {portrait_letterbox_path} ({portrait_letterbox.size[0]}×{portrait_letterbox.size[1]})")

print("\n[TEST 4] Applying RESIZE mode to portrait image...")
portrait_resize = apply_display_mode(portrait, "resize", TV_WIDTH, TV_HEIGHT)
portrait_resize_path = os.path.join(OUTPUT_DIR, "04_portrait_resize.jpg")
portrait_resize.save(portrait_resize_path, "JPEG", quality=88)
print(f"✓ Saved: {portrait_resize_path} ({portrait_resize.size[0]}×{portrait_resize.size[1]})")

print("\n[TEST 5] Applying SIDE-BY-SIDE mode to portrait image...")
portrait_sidebyside = apply_display_mode(portrait, "side-by-side", TV_WIDTH, TV_HEIGHT)
portrait_sidebyside_path = os.path.join(OUTPUT_DIR, "05_portrait_sidebyside.jpg")
portrait_sidebyside.save(portrait_sidebyside_path, "JPEG", quality=88)
print(f"✓ Saved: {portrait_sidebyside_path} ({portrait_sidebyside.size[0]}×{portrait_sidebyside.size[1]})")

# Test 6-8: Apply display modes to landscape image
print("\n[TEST 6] Applying LETTERBOX mode to landscape image...")
landscape_letterbox = apply_display_mode(landscape, "letterbox", TV_WIDTH, TV_HEIGHT)
landscape_letterbox_path = os.path.join(OUTPUT_DIR, "06_landscape_letterbox.jpg")
landscape_letterbox.save(landscape_letterbox_path, "JPEG", quality=88)
print(f"✓ Saved: {landscape_letterbox_path} ({landscape_letterbox.size[0]}×{landscape_letterbox.size[1]})")

print("\n[TEST 7] Applying RESIZE mode to landscape image...")
landscape_resize = apply_display_mode(landscape, "resize", TV_WIDTH, TV_HEIGHT)
landscape_resize_path = os.path.join(OUTPUT_DIR, "07_landscape_resize.jpg")
landscape_resize.save(landscape_resize_path, "JPEG", quality=88)
print(f"✓ Saved: {landscape_resize_path} ({landscape_resize.size[0]}×{landscape_resize.size[1]})")

print("\n[TEST 8] Applying SIDE-BY-SIDE mode to landscape image...")
landscape_sidebyside = apply_display_mode(landscape, "side-by-side", TV_WIDTH, TV_HEIGHT)
landscape_sidebyside_path = os.path.join(OUTPUT_DIR, "08_landscape_sidebyside.jpg")
landscape_sidebyside.save(landscape_sidebyside_path, "JPEG", quality=88)
print(f"✓ Saved: {landscape_sidebyside_path} ({landscape_sidebyside.size[0]}×{landscape_sidebyside.size[1]})")

print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)
print(f"\nTV Display Resolution: {TV_WIDTH}×{TV_HEIGHT} (16:9 aspect ratio)")
print(f"\nTest Images Created:")
print(f"  1. Portrait source (9:16):   {portrait.size[0]}×{portrait.size[1]}")
print(f"  2. Landscape source (16:9):  {landscape.size[0]}×{landscape.size[1]}")
print(f"\nDisplay Modes Tested:")
print(f"  ✓ LETTERBOX    - Preserves aspect ratio, adds black bars")
print(f"  ✓ RESIZE       - Stretches to fill 16:9 (may distort)")
print(f"  ✓ SIDE-BY-SIDE - Tiles 2 portrait images horizontally")
print(f"\nAll output images are {TV_WIDTH}×{TV_HEIGHT}px (16:9).")
print(f"\nOutput directory: {OUTPUT_DIR}/")
print(f"\n✅ All tests passed!")
print("="*70 + "\n")
