from PIL import Image, ImageDraw, ImageFont
import random

def text_to_scanned_image(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    margin_left = 80
    margin_top = 70
    margin_right = 80
    margin_bottom = 70
    line_height = 18
    page_width = 1200

    try:
        font = ImageFont.truetype("consola.ttf", 13)
    except OSError:
        try:
            font = ImageFont.truetype("cour.ttf", 13)
        except OSError:
            font = ImageFont.load_default()

    lines = []
    for raw_line in text.split("\n"):
        if not raw_line:
            lines.append("")
            continue
        words = raw_line.split()
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = font.getbbox(test)
            if bbox[2] > page_width - margin_left - margin_right:
                lines.append(current)
                current = word
            else:
                current = test
        if current:
            lines.append(current)

    img_height = margin_top + len(lines) * line_height + margin_bottom
    img = Image.new("RGB", (page_width, img_height), (255, 255, 255))
    pixels = img.load()

    random.seed(42)
    for y in range(img_height):
        for x in range(page_width):
            noise = random.randint(-12, 12)
            base = 245 + random.randint(-6, 6)
            val = max(0, min(255, base + noise))
            pixels[x, y] = (val, val, val)

    for x in range(page_width):
        for y in range(3):
            shade = random.randint(180, 210)
            pixels[x, y] = (shade, shade, shade)
            pixels[x, img_height - 1 - y] = (shade, shade, shade)

    draw = ImageDraw.Draw(img)

    for i, line in enumerate(lines):
        x = margin_left + random.randint(-1, 1)
        y = margin_top + i * line_height + random.randint(-1, 0)
        gray = random.randint(15, 40)
        draw.text((x, y), line, fill=(gray, gray, gray), font=font)

    skew_offset = random.randint(2, 5)
    img = img.transform(
        img.size,
        Image.AFFINE,
        (1, 0.005, -skew_offset, 0, 1, 0),
        resample=Image.BILINEAR,
        fillcolor=(240, 240, 240),
    )

    img = img.convert("L").convert("RGB")
    img.save(output_path, "PNG", quality=92)
    print(f"Saved scanned image: {output_path} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    text_to_scanned_image("patient_success.txt", "patient_success_scanned.png")
    text_to_scanned_image("patient_rejection.txt", "patient_rejection_scanned.png")
    text_to_scanned_image("patient_missing.txt", "patient_missing_scanned.png")
