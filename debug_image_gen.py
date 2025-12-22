#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug image generation with detailed info"""

from PIL import Image, ImageDraw, ImageFont
import os

# Load test image
img_path = 'C:/Users/user/Downloads/574476495_1553252792497370_8800427246995539259_n.jpg'
img = Image.open(img_path)
print(f'Original image size: {img.width}x{img.height}')

# Resize logic from result_generator.py
max_size = 500
if img.width > max_size or img.height > max_size:
    if img.width > img.height:
        new_width = max_size
        new_height = int(img.height * (max_size / img.width))
    else:
        new_height = max_size
        new_width = int(img.width * (max_size / img.height))
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(f'Resized to: {img.width}x{img.height}')

canvas_width = img.width
print(f'Canvas width: {canvas_width}px')

# Test comment
comment = '츤데레같은 느낌! 수려한 외모에 도도하게 있을 것 같지만 반려자님께 항상 의지하고 있을 것 같아요!'
max_chars_per_line = 25
actual_comment_lines = (len(comment) + max_chars_per_line - 1) // max_chars_per_line
print(f'\nComment: {len(comment)} chars')
print(f'Lines needed: {actual_comment_lines}')

# Split into lines
lines = []
for i in range(0, len(comment), max_chars_per_line):
    lines.append(comment[i:i + max_chars_per_line])

print(f'\nActual lines: {len(lines)}')
for i, line in enumerate(lines):
    print(f'  Line {i}: "{line}" ({len(line)} chars)')

# Load font
font_paths = [
    'C:\\Windows\\Fonts\\malgun.ttf',
    'C:\\Windows\\Fonts\\gulim.ttc',
]

text_font = None
for font_path in font_paths:
    if os.path.exists(font_path):
        text_font = ImageFont.truetype(font_path, 18)
        print(f'\nUsing font: {font_path}')
        break

if text_font is None:
    text_font = ImageFont.load_default()
    print('\nUsing default font')

# Create a small test canvas
test_canvas = Image.new('RGB', (canvas_width, 200), '#FFE5D9')
draw = ImageDraw.Draw(test_canvas)

# Test text width for first line
first_line = lines[0]
try:
    bbox = draw.textbbox((0, 0), first_line, font=text_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    print(f'\nFirst line text dimensions:')
    print(f'  Text: "{first_line}"')
    print(f'  Width: {text_width}px')
    print(f'  Height: {text_height}px')
    print(f'  Canvas width: {canvas_width}px')

    if text_width > canvas_width:
        print(f'  ⚠️  TEXT TOO WIDE! Exceeds canvas by {text_width - canvas_width}px')
    else:
        print(f'  ✓ Text fits (margin: {canvas_width - text_width}px)')

    # Calculate center position
    center_x = (canvas_width - text_width) // 2
    print(f'  Center X position: {center_x}px')

    if center_x < 0:
        print(f'  ⚠️  CENTER X IS NEGATIVE! Text will be clipped on left side.')
        print(f'  Clipped pixels: {abs(center_x)}px')
        print(f'  Estimated clipped chars: {abs(center_x) // (text_width // len(first_line))}')

except Exception as e:
    print(f'Error getting text bbox: {e}')
