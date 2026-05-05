"""
Project media helpers (covers, uploads).
Keeps file and image logic out of view code.
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - runtime optional
    Image = None
    ImageDraw = None
    ImageFont = None


def pillow_available():
    return Image is not None and ImageDraw is not None


def resolve_image_path(value, app_dir):
    path = str(value or "").strip()
    if not path:
        return None
    if os.path.isabs(path) and os.path.exists(path):
        return path
    local = os.path.join(app_dir, path)
    if os.path.exists(local):
        return local
    return path if os.path.exists(path) else None


def store_project_image(source_path, app_dir):
    target_dir = os.path.join(app_dir, "media", "project_covers")
    os.makedirs(target_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_name = os.path.basename(source_path)
    target_path = os.path.join(target_dir, f"{stamp}_{base_name}")
    shutil.copy2(source_path, target_path)
    return os.path.relpath(target_path, app_dir).replace("\\", "/")


def create_dummy_cover(project, app_dir):
    if not pillow_available():
        return None

    try:
        pid = int(project.get("id") or 0)
    except Exception:
        pid = 0

    title = str(project.get("name") or "Project").strip() or "Project"
    subtitle = str(project.get("location") or "").strip()
    tag = str(project.get("property_type") or "").strip().upper()

    out_dir = os.path.join(app_dir, "media", "project_covers")
    os.makedirs(out_dir, exist_ok=True)
    abs_path = os.path.join(out_dir, f"auto_cover_{pid or 'x'}.png")
    if os.path.exists(abs_path):
        return os.path.relpath(abs_path, app_dir).replace("\\", "/")

    palette = [
        ((9, 28, 65), (79, 140, 255)),
        ((17, 24, 39), (16, 185, 129)),
        ((15, 23, 42), (245, 158, 11)),
        ((12, 18, 34), (236, 72, 153)),
        ((7, 17, 31), (99, 102, 241)),
        ((9, 14, 27), (34, 211, 238)),
    ]
    start, end = palette[pid % len(palette)]

    width, height = 1400, 760
    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(start[0] + (end[0] - start[0]) * t)
        g = int(start[1] + (end[1] - start[1]) * t)
        b = int(start[2] + (end[2] - start[2]) * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    try:
        font_title = ImageFont.truetype("arial.ttf", 58) if ImageFont else None
        font_sub = ImageFont.truetype("arial.ttf", 28) if ImageFont else None
        font_chip = ImageFont.truetype("arial.ttf", 22) if ImageFont else None
    except Exception:
        font_title = font_sub = font_chip = ImageFont.load_default() if ImageFont else None

    draw.rounded_rectangle([44, 44, 300, 120], radius=22, fill=(255, 255, 255, 22))
    if tag and font_chip:
        draw.text((70, 70), tag[:24], font=font_chip, fill=(255, 255, 255, 215))

    draw.ellipse([width - 430, -90, width + 120, 460], fill=(255, 255, 255, 18))
    draw.ellipse([width - 700, height - 480, width - 240, height - 20], fill=(0, 0, 0, 35))

    draw.rounded_rectangle([60, height - 220, width - 60, height - 60], radius=28, fill=(0, 0, 0, 95))
    if font_title:
        draw.text((96, height - 198), title, font=font_title, fill=(248, 250, 252, 245))
    if subtitle and font_sub:
        draw.text((96, height - 118), subtitle, font=font_sub, fill=(203, 213, 225, 220))

    try:
        img.save(abs_path, format="PNG", optimize=True)
    except Exception:
        try:
            img.convert("RGB").save(abs_path, format="PNG")
        except Exception:
            return None

    return os.path.relpath(abs_path, app_dir).replace("\\", "/")
