import anthropic
import base64
import mimetypes
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()


def ingest_document(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _ingest_pdf(file_path)
    elif ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        return _ingest_image(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .jpg, .jpeg, .png, .gif, .webp, .txt")


def _ingest_image(file_path: str) -> str:
    mime_type = mimetypes.guess_type(file_path)[0] or "image/png"
    with open(file_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": "Extract ALL text from this scanned clinical document exactly as written. "
                            "Preserve the original structure, headings, line breaks, and formatting. "
                            "Include every detail — patient name, MRN, dates, lab values, medications, "
                            "dosages, and clinical observations. Do not summarize or omit anything. "
                            "Return only the extracted text, no commentary.",
                },
            ],
        }],
    )

    return next(b.text for b in response.content if b.type == "text")


def _ingest_pdf(file_path: str) -> str:
    with open(file_path, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    },
                },
                {
                    "type": "text",
                    "text": "Extract ALL text from this clinical document exactly as written. "
                            "Preserve the original structure, headings, line breaks, and formatting. "
                            "Include every detail — patient name, MRN, dates, lab values, medications, "
                            "dosages, and clinical observations. Do not summarize or omit anything. "
                            "Return only the extracted text, no commentary.",
                },
            ],
        }],
    )

    return next(b.text for b in response.content if b.type == "text")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python utils.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    print(f"Ingesting {file_path}...")
    text = ingest_document(file_path)
    print(f"\n--- Extracted Text ({len(text)} chars) ---\n")
    print(text)
