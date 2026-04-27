"""
Generates the ClipboardAI icon programmatically.
Run once: python generate_icon.py
"""
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageDraw

def make_icon(size=256):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Purple-to-indigo gradient circle (approximated)
    for r in range(size // 2, 0, -1):
        t = r / (size // 2)
        red   = int(124 * t + 79 * (1 - t))
        green = int(58  * t + 70 * (1 - t))
        blue  = int(237 * t + 229 * (1 - t))
        draw.ellipse(
            [size//2 - r, size//2 - r, size//2 + r, size//2 + r],
            fill=(red, green, blue, 255)
        )

    # Rounded rect for clipboard body
    cx, cy = size // 2, size // 2 + size // 16
    w, h   = int(size * 0.36), int(size * 0.44)
    draw.rounded_rectangle(
        [cx - w//2, cy - h//2, cx + w//2, cy + h//2],
        radius=size // 20, fill=(255, 255, 255, 230)
    )

    # Clip at top
    cw = int(size * 0.22)
    clip_y1 = cy - h//2 - size // 18
    clip_y2 = cy - h//2 + size // 16
    draw.rounded_rectangle(
        [cx - cw//2, clip_y1, cx + cw//2, clip_y2],
        radius=size // 28, fill=(210, 190, 255, 255)
    )

    # Text lines on clipboard
    line_x1 = cx - w//2 + size // 18
    line_x2 = cx + w//2 - size // 18
    for i, frac in enumerate([0.35, 0.48, 0.61]):
        ly = int(cy - h//2 + h * frac)
        lx2 = line_x2 if i % 2 == 0 else cx + int(w * 0.1)
        draw.rounded_rectangle(
            [line_x1, ly, lx2, ly + size//36],
            radius=2, fill=(124, 58, 237, 180)
        )

    # Lightning bolt (top-right accent)
    s = size // 8
    bx = cx + w//2 - s // 2
    by = cy - h//2 - s // 2
    bolt = [
        (bx + s,       by),
        (bx + s//3,    by + s*0.55),
        (bx + s*0.65,  by + s*0.55),
        (bx,           by + s),
        (bx + s*0.7,   by + s*0.45),
        (bx + s*0.35,  by + s*0.45),
    ]
    draw.polygon(bolt, fill=(255, 220, 50, 240))

    return img

if __name__ == "__main__":
    assets = os.path.join(SCRIPT_DIR, "assets")
    os.makedirs(assets, exist_ok=True)
    img = make_icon(256)
    img.save(os.path.join(assets, "icon.png"))

    # Also create ICO with multiple sizes
    sizes = [256, 128, 64, 48, 32, 16]
    icons = [make_icon(s) for s in sizes]
    icons[0].save(os.path.join(assets, "icon.ico"), format="ICO",
                  sizes=[(s, s) for s in sizes],
                  append_images=icons[1:])
    print("OK - Generated assets/icon.png and assets/icon.ico")
