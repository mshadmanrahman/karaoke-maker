#!/usr/bin/env python3
"""Test Bengali font rendering"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Test text
bengali_text = "আমরাল তের ছায়ার কন্যা জুলাই তের বাড়ি কুশ লহরা তের চাল-সুরকল লায়িক কাওয়ালিত রে লায়িক"

# Font paths to test
font_paths = [
    str(Path.home() / "Library/Fonts/NotoSansBengali-Bold.ttf"),
    str(Path.home() / "Library/Fonts/NotoSansBengali-ExtraBold.ttf"),
    "/System/Library/Fonts/KohinoorBangla.ttc",
    "/System/Library/Fonts/Supplemental/Bangla Sangam MN.ttc",
]

print("Testing Bengali font rendering...\n")

for font_path in font_paths:
    try:
        # Load font
        font = ImageFont.truetype(font_path, 72)
        print(f"✓ Successfully loaded: {font_path}")

        # Create test image
        img = Image.new('RGB', (1920, 200), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw text
        draw.text((50, 50), bengali_text, font=font, fill=(255, 255, 255))

        # Save test image
        output_name = Path(font_path).stem + "_test.png"
        output_path = Path("/tmp") / output_name
        img.save(output_path)

        print(f"  → Test image saved: {output_path}")
        print()

        # Use first successful font
        break

    except Exception as e:
        print(f"✗ Failed to load: {font_path}")
        print(f"  Error: {e}")
        print()

print("Test complete! Check /tmp for test images.")
