#!/usr/bin/env python3
import os
import glob
import fitz  # PyMuPDF
from pptx import Presentation
import docx
import openpyxl
import shutil
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

AGENT0_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(os.path.join(AGENT0_DIR, ".env")):
    load_dotenv(os.path.join(AGENT0_DIR, ".env"))
else:
    load_dotenv(os.path.expanduser("~/Agents/Agent 0/.env"))

PIPELINE_DIR = os.path.expanduser(os.environ.get("CLASS_FOLDERS_PATH", "~/Documents/Class Folders"))
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_FREE_API_KEY", "")
# 120s HTTP timeout: a hung API call must never block the ingestion daemon indefinitely
client = genai.Client(api_key=GEMINI_API_KEY, http_options={"timeout": 120000}) if (GEMINI_API_KEY and not GEMINI_API_KEY.startswith("YOUR_")) else None


def _is_decorative_image(image_bytes, min_size=100, max_solid_ratio=0.92):
    """Heuristic pre-filter: returns True if the image is likely decorative junk."""
    from PIL import Image
    import io
    import numpy as np
    try:
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size

        if w < min_size or h < min_size:
            print(f"  [Pre-filter] Skipping tiny image ({w}x{h})")
            return True

        thumb = img.convert("RGB").resize((64, 64))
        pixels = np.array(thumb, dtype=np.float32)

        std = pixels.std(axis=(0, 1))
        mean_std = std.mean()

        if mean_std < 15:
            print(f"  [Pre-filter] Skipping low-variance image (std={mean_std:.1f}, likely background/solid)")
            return True

        flat = pixels.reshape(-1, 3)
        mode_color = np.median(flat, axis=0)
        distances = np.sqrt(((flat - mode_color) ** 2).sum(axis=1))
        close_ratio = (distances < 30).mean()
        if close_ratio > max_solid_ratio:
            print(f"  [Pre-filter] Skipping near-uniform image ({close_ratio:.0%} pixels are same color)")
            return True

        return False
    except Exception as e:
        print(f"  [Pre-filter] Error analyzing image: {e}")
        return False


def _local_ocr_image(image_bytes):
    """Analyze image locally to determine if it needs the Vision API."""
    from PIL import Image
    import io
    try:
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size

        gray = img.convert("L")
        import numpy as np
        pixels = np.array(gray)

        light_pixels = (pixels > 200).mean()
        dark_pixels = (pixels < 55).mean()

        if light_pixels > 0.60 and dark_pixels > 0.05:
            return "TEXT_HEAVY"

        rgb = img.convert("RGB").resize((128, 128))
        rgb_arr = np.array(rgb)

        reshaped = rgb_arr.reshape(-1, 3)
        quantized = (reshaped // 8)
        unique_colors = len(np.unique(quantized, axis=0))

        gray_small = np.array(gray.resize((128, 128)), dtype=np.float32)
        dx = np.abs(np.diff(gray_small, axis=1))
        dy = np.abs(np.diff(gray_small, axis=0))
        edge_ratio = ((dx > 30).mean() + (dy > 30).mean()) / 2

        if unique_colors > 800 and edge_ratio < 0.15:
            print(f"  [Photo detector] Skipping photo (colors={unique_colors}, edges={edge_ratio:.1%})")
            return "PHOTO"

        if edge_ratio < 0.10:
            print(f"  [Photo detector] Skipping smooth image (colors={unique_colors}, edges={edge_ratio:.1%})")
            return "PHOTO"

        if w > 1000 and h > 1000 and edge_ratio < 0.17:
            print(f"  [Photo detector] Skipping large photo ({w}x{h}, edges={edge_ratio:.1%})")
            return "PHOTO"

        return None
    except Exception as e:
        print(f"  [Local OCR] Error: {e}")
        return None


def describe_image_blob(image_bytes, ext):
    import time
    if not client:
        return "*[Image/Media]*"
    try:
        ext = ext.lower().replace(".", "")

        if ext in ["emf", "wmf", "bmp", "tiff", "tif"]:
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_bytes))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                out = io.BytesIO()
                img.save(out, format="JPEG")
                image_bytes = out.getvalue()
                ext = "jpg"
            except Exception as e:
                print(f"  [Format Converter] Failed to convert {ext.upper()}: {e}")
                return f"*[Image/Media: Unsupported Format ({ext.upper()})]*"

        mime_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

        if _is_decorative_image(image_bytes):
            return ""

        local_result = _local_ocr_image(image_bytes)
        if local_result == "TEXT_HEAVY":
            print("  [Local OCR] Text-heavy image detected — skipping API call (text already extracted from slide XML)")
            return ""
        elif local_result == "PHOTO":
            return ""

        prompt = (
            "You are transcribing lecture slides into study notes. Describe this image, diagram, or chart in detail. "
            "Transcribe any text, formulas, or data accurately. "
            "CRITICAL EXCEPTION: If the image is purely decorative (e.g., abstract backgrounds, neon graphics, standard stock photography of nature/people, memes) and contains NO educational content, formulas, or data, you MUST return exactly the string '[SKIP]' and nothing else. "
            "CRITICAL LATEX RULES: 1. No multi-line math blocks. 2. NEVER put literal $ or escaped \\$ inside LaTeX math delimiters ($...$). Keep currency symbols outside math blocks. "
            "Only return the description."
        )

        models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]
        last_error = None
        for model_name in models_to_try:
            for attempt in range(3):
                try:
                    interaction = client.models.generate_content(
                        model=model_name,
                        contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
                    )
                    raw_text = interaction.text
                    if not raw_text:
                        try:
                            raw_text = " ".join([p.text for p in interaction.candidates[0].content.parts if p.text])
                        except Exception:
                            pass

                    if not raw_text:
                        return ""

                    desc = raw_text.strip()
                    if desc == "[SKIP]" or "[SKIP]" in desc:
                        return ""

                    desc = desc.replace("\n", "\n> ")
                    return f"\n> **[Visual/Diagram]**\n> {desc}\n"
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "429" in err_str:
                        print(f"  Vision API {model_name} hit 429 quota limit. Falling back to next model.")
                        break
                    elif "503" in err_str:
                        wait = 2 ** (attempt + 1)
                        print(f"  Vision API {model_name} attempt {attempt+1} got {err_str[:60]}... retrying in {wait}s")
                        time.sleep(wait)
                        continue
                    elif "404" in err_str:
                        break
                    else:
                        break
        print(f"Error calling Gemini Vision (All models failed): {last_error}")
        return f"*[Image/Media: Failed to transcribe - {str(last_error)}]*"
    except Exception as e:
        print(f"Error preparing Gemini Vision request: {e}")
        return f"*[Image/Media: Failed to transcribe - {str(e)}]*"


def ocr_image_blob(image_bytes, ext):
    """OCR a scanned document page — extracts text verbatim instead of describing a diagram."""
    import time
    if not client:
        return None
    try:
        ext = ext.lower().replace(".", "")
        mime_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

        prompt = (
            "Extract all text from this scanned document page verbatim. Preserve the structure using Markdown formatting (headings, lists, bold, tables). "
            "If there are multiple choice questions, format each with the question number and options. "
            "CRITICAL LATEX RULES: 1. No multi-line math blocks. 2. NEVER put literal $ or escaped \\$ inside LaTeX math delimiters ($...$). Keep currency symbols outside math blocks. "
            "Output only raw markdown, no code fences."
        )

        models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]
        last_error = None
        for model_name in models_to_try:
            for attempt in range(3):
                try:
                    interaction = client.models.generate_content(
                        model=model_name,
                        contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
                    )
                    if interaction.text:
                        return interaction.text.strip()
                    break
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "429" in err_str:
                        print(f"  OCR API {model_name} hit 429 quota limit. Falling back to next model.")
                        break
                    elif "503" in err_str:
                        wait = 2 ** (attempt + 1)
                        print(f"  OCR API {model_name} attempt {attempt+1} got {err_str[:60]}... retrying in {wait}s")
                        time.sleep(wait)
                        continue
                    elif "404" in err_str:
                        break
                    else:
                        break
        print(f"Error OCR-ing page (All models failed): {last_error}")
        return None
    except Exception as e:
        print(f"Error preparing OCR request: {e}")
        return None


def extract_text_from_shape(shape, slide_area=None):
    text = ""
    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
        for p in shape.text_frame.paragraphs:
            level = getattr(p, "level", 0) or 0
            indent = "  " * level
            p_text = p.text.strip()
            if p_text:
                text += f"{indent}- {p_text}\n"

    if hasattr(shape, "has_table") and shape.has_table:
        for i, row in enumerate(shape.table.rows):
            row_data = []
            for cell in row.cells:
                if cell.text_frame:
                    cell_text = " ".join([p.text.strip() for p in cell.text_frame.paragraphs if p.text.strip()])
                    row_data.append(cell_text)
                else:
                    row_data.append("")
            text += "| " + " | ".join(row_data) + " |\n"
            if i == 0:
                text += "|" + "|".join(["---"] * len(row_data)) + "|\n"

    if getattr(shape, "shape_type", None) == 13:
        try:
            if slide_area and shape.width and shape.height:
                shape_area = shape.width * shape.height
                coverage = shape_area / slide_area
                if coverage > 0.50:
                    print(f"  [Coverage filter] Skipping background image ({coverage:.0%} of slide)")
                else:
                    image = shape.image
                    text += describe_image_blob(image.blob, image.ext)
            else:
                image = shape.image
                text += describe_image_blob(image.blob, image.ext)
        except Exception:
            text += "*[Image/Media]*\n"

    if getattr(shape, "shape_type", None) == 6 and hasattr(shape, "shapes"):
        for child in shape.shapes:
            text += extract_text_from_shape(child, slide_area)

    return text


def extract_text_from_pptx(pptx_path):
    try:
        prs = Presentation(pptx_path)
        slide_area = None
        if prs.slide_width and prs.slide_height:
            slide_area = prs.slide_width * prs.slide_height
        text_content = []
        for i, slide in enumerate(prs.slides):
            text_content.append(f"## Slide {i+1}")
            for shape in slide.shapes:
                shape_text = extract_text_from_shape(shape, slide_area)
                if shape_text.strip():
                    text_content.append(shape_text.strip())

            try:
                for alt_content in slide._element.spTree.iter("{http://schemas.openxmlformats.org/markup-compatibility/2006}AlternateContent"):
                    for choice in alt_content.iter("{http://schemas.openxmlformats.org/markup-compatibility/2006}Choice"):
                        alt_texts = []
                        for node in choice.iter():
                            if node.tag in (
                                "{http://schemas.openxmlformats.org/drawingml/2006/main}t",
                                "{http://schemas.openxmlformats.org/officeDocument/2006/math}t"
                            ):
                                if node.text and node.text.strip():
                                    alt_texts.append(node.text.strip())
                        if alt_texts:
                            text_content.append("- " + " ".join(alt_texts))
            except Exception as e:
                print(f"Error parsing AlternateContent on slide {i+1}: {e}")

            try:
                for rel in slide.part.rels.values():
                    if rel.reltype.endswith("diagramData"):
                        p = rel.target_part
                        root = ET.fromstring(p.blob)
                        for elem in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}t"):
                            if elem.text and elem.text.strip():
                                text_content.append("- [SmartArt] " + elem.text.strip())
            except Exception as e:
                print(f"Error parsing SmartArt on slide {i+1}: {e}")

            if slide.has_notes_slide:
                notes_frame = slide.notes_slide.notes_text_frame
                if notes_frame and notes_frame.text.strip():
                    text_content.append(f"**Speaker Notes:**\n{notes_frame.text.strip()}")
        return "\n\n".join(text_content)
    except Exception as e:
        print(f"Error parsing {pptx_path}: {e}")
        return None


def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text_content = []
        for i, page in enumerate(doc):
            text_content.append(f"## Page {i+1}")
            page_text = page.get_text("text", sort=True).strip()
            if page_text:
                text_content.append(page_text)
            elif page.get_images():
                try:
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    ocr_result = ocr_image_blob(img_bytes, "png")
                    if ocr_result:
                        text_content.append(ocr_result)
                    else:
                        text_content.append("*[Scanned page: Failed to OCR]*")
                except Exception as e:
                    print(f"Error OCR-ing scanned page {i+1} of {pdf_path}: {e}")
                    text_content.append("*[Scanned page: OCR error]*")
        return "\n\n".join(text_content)
    except Exception as e:
        print(f"Error parsing {pdf_path}: {e}")
        return None


def extract_text_from_docx(docx_path):
    try:
        from docx.oxml.table import CT_Tbl
        from docx.oxml.text.paragraph import CT_P
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        doc = docx.Document(docx_path)
        text_content = []

        for block in doc.element.body:
            if isinstance(block, CT_P):
                para = Paragraph(block, doc._body)
                if para.text.strip():
                    text_content.append(para.text.strip())
            elif isinstance(block, CT_Tbl):
                table = Table(block, doc._body)
                table_lines = []
                for i, row in enumerate(table.rows):
                    row_data = [cell.text.replace("\n", " ").strip() for cell in row.cells]
                    table_lines.append("| " + " | ".join(row_data) + " |")
                    if i == 0:
                        table_lines.append("|" + "|".join(["---"] * len(row.cells)) + "|")
                text_content.append("\n".join(table_lines))
        return "\n\n".join(text_content)
    except Exception as e:
        print(f"Error parsing {docx_path}: {e}")
        return None


def extract_text_from_xlsx(xlsx_path):
    try:
        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        text_content = []
        for sheetname in wb.sheetnames:
            sheet = wb[sheetname]
            text_content.append(f"## Sheet: {sheetname}")
            sheet_has_rows = False
            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                row_data = [str(cell).replace("\n", " ").strip() if cell is not None else "" for cell in row]
                if any(row_data):
                    text_content.append("| " + " | ".join(row_data) + " |")
                    if not sheet_has_rows:
                        text_content.append("|" + "|".join(["---"] * len(row_data)) + "|")
                        sheet_has_rows = True
        return "\n\n".join(text_content)
    except Exception as e:
        print(f"Error parsing {xlsx_path}: {e}")
        return None


def extract_text_from_image(image_path):
    import time
    if not client:
        print(f"Error: Gemini client not initialized. Cannot parse image {image_path}")
        return None
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ext = image_path.lower().split(".")[-1]
        mime_type = f"image/{'jpeg' if ext == 'jpg' else ext}"

        prompt = (
            "Extract all text from this image verbatim. Do NOT summarize. Preserve the visual structure using Markdown formatting (headings, lists, bold, tables). "
            "Output only raw markdown, no code fences. "
            "CRITICAL LATEX RULES: 1. No multi-line math blocks. 2. NEVER put literal $ or escaped \\$ inside LaTeX math delimiters ($...$). Keep currency symbols outside math blocks."
        )
        # Fallback for photos of copyrighted textbook pages: Gemini's RECITATION filter blocks
        # verbatim reproduction on every model, so request faithful structured notes instead.
        fallback_prompt = (
            "Convert the content of this image into structured study notes in Markdown. Capture every heading, definition, key term, number, formula, and table row. "
            "Long prose may be condensed into faithful bullet points; keep all numbers, labels, and formulas exact. Output only markdown, no code fences. "
            "CRITICAL LATEX RULES: 1. No multi-line math blocks. 2. NEVER put literal $ or escaped \\$ inside LaTeX math delimiters ($...$). Keep currency symbols outside math blocks."
        )

        def _response_text(interaction):
            txt = interaction.text
            if not txt:
                try:
                    txt = "".join(p.text for p in interaction.candidates[0].content.parts
                                  if getattr(p, "text", None) and not getattr(p, "thought", False))
                except Exception:
                    txt = ""
            return (txt or "").strip()

        def _finish_reason(interaction):
            try:
                return str(interaction.candidates[0].finish_reason)
            except Exception:
                return "UNKNOWN"

        models_to_try = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.8-flash"]
        last_error = None
        for model_name in models_to_try:
            for attempt in range(3):
                try:
                    interaction = client.models.generate_content(
                        model=model_name,
                        contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
                    )
                    text = _response_text(interaction)
                    if text:
                        return text
                    reason = _finish_reason(interaction)
                    print(f"  Image API {model_name} returned no text (finish_reason={reason}). Retrying with study-notes prompt.")
                    interaction = client.models.generate_content(
                        model=model_name,
                        contents=[fallback_prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
                    )
                    text = _response_text(interaction)
                    if text:
                        return "> [!NOTE] Converted to study notes (verbatim transcription was blocked by the model's copyright filter).\n\n" + text
                    last_error = f"Empty response from {model_name} (finish_reason={_finish_reason(interaction)})"
                    break
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "429" in err_str:
                        print(f"  Image API {model_name} hit 429 quota limit. Falling back to next model.")
                        break
                    elif "503" in err_str:
                        wait = 2 ** (attempt + 1)
                        print(f"  Image API {model_name} attempt {attempt+1} got {err_str[:60]}... retrying in {wait}s")
                        time.sleep(wait)
                        continue
                    elif "404" in err_str:
                        break
                    else:
                        break
        print(f"Error parsing image {image_path} (All models failed): {last_error}")
        return None
    except Exception as e:
        print(f"Error preparing image {image_path}: {e}")
        return None


MAX_PARSE_FAILURES = 3
FAILURE_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".parse_failures.json")


def _load_failures():
    import json
    try:
        with open(FAILURE_LOG, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_failures(data):
    import json
    try:
        with open(FAILURE_LOG, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"  [Failure log] Could not write {FAILURE_LOG}: {e}")


def _record_failure(file_path):
    data = _load_failures()
    data[file_path] = data.get(file_path, 0) + 1
    _save_failures(data)
    return data[file_path]


def _clear_failure(file_path):
    data = _load_failures()
    if file_path in data:
        del data[file_path]
        _save_failures(data)


def process_pipeline():
    if not os.path.exists(PIPELINE_DIR):
        print(f"Pipeline directory not found: {PIPELINE_DIR}")
        return

    print("Scanning Big Context Class Folders for raw lecture files in 1_ folders...")

    all_files = []
    for root, dirs, files in os.walk(PIPELINE_DIR):
        basename = os.path.basename(root)
        if basename.startswith("1_"):
            for file in files:
                if not file.startswith(".") and file.lower().endswith((".pptx", ".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".jpg", ".jpeg", ".png")):
                    all_files.append(os.path.join(root, file))

    # Process fast local documents (.pdf, .docx, .xlsx, .csv, .txt, .md, .pptx) BEFORE slow image OCR (.jpg/.png)
    all_files.sort(key=lambda p: (1 if p.lower().endswith((".jpg", ".jpeg", ".png")) else 0, p))

    new_conversions = 0

    for file_path in all_files:
        filename = os.path.basename(file_path)
        class_folder = os.path.dirname(os.path.dirname(file_path))
        course_name = os.path.basename(class_folder)

        # Support either 2_Parsed_MD or existing 2_Parsed_Markdown
        parsed_dir = os.path.join(class_folder, "2_Parsed_MD")
        if not os.path.exists(parsed_dir) and os.path.exists(os.path.join(class_folder, "2_Parsed_Markdown")):
            parsed_dir = os.path.join(class_folder, "2_Parsed_Markdown")
        archive_dir = os.path.join(class_folder, "3_Archive")

        os.makedirs(parsed_dir, exist_ok=True)
        os.makedirs(archive_dir, exist_ok=True)

        md_path = os.path.join(parsed_dir, filename.rsplit(".", 1)[0] + ".md")
        archive_path = os.path.join(archive_dir, filename)

        if not os.path.exists(md_path):
            print(f"Extracting raw text from: {filename}")

            content = None
            if file_path.lower().endswith(".pptx"):
                content = extract_text_from_pptx(file_path)
            elif file_path.lower().endswith(".pdf"):
                content = extract_text_from_pdf(file_path)
            elif file_path.lower().endswith(".docx"):
                content = extract_text_from_docx(file_path)
            elif file_path.lower().endswith(".xlsx"):
                content = extract_text_from_xlsx(file_path)
            elif file_path.lower().endswith(".csv"):
                import csv
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        reader = csv.reader(f)
                        table_lines = []
                        for i, row in enumerate(reader):
                            row_data = [cell.replace("\n", " ").strip() for cell in row]
                            table_lines.append("| " + " | ".join(row_data) + " |")
                            if i == 0:
                                table_lines.append("|" + "|".join(["---"] * len(row_data)) + "|")
                        content = "\n".join(table_lines)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
            elif file_path.lower().endswith((".jpg", ".jpeg", ".png")):
                content = extract_text_from_image(file_path)
            elif file_path.lower().endswith((".txt", ".md")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading text file {file_path}: {e}")

            if content:
                final_content = content

                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(final_content)
                new_conversions += 1
                _clear_failure(file_path)
                print(f" -> Saved raw extraction to: {os.path.basename(parsed_dir)}/{os.path.basename(md_path)}")

                try:
                    shutil.move(file_path, archive_path)
                    print(f" -> Archived original file to: 3_Archive/{filename}")
                except Exception as e:
                    print(f" -> Failed to archive {file_path}: {e}")
            else:
                fails = _record_failure(file_path)
                if fails >= MAX_PARSE_FAILURES:
                    review_dir = os.path.join(class_folder, "4_Needs_Review")
                    os.makedirs(review_dir, exist_ok=True)
                    try:
                        shutil.move(file_path, os.path.join(review_dir, filename))
                        _clear_failure(file_path)
                        print(f" -> QUARANTINED after {fails} failed attempts: {course_name}/4_Needs_Review/{filename}")
                    except Exception as e:
                        print(f" -> Failed to quarantine {file_path}: {e}")
                else:
                    print(f" -> WARNING: Extraction failed or returned empty for {filename} (attempt {fails}/{MAX_PARSE_FAILURES}). Retaining in raw directory.")
        else:
            try:
                shutil.move(file_path, archive_path)
                print(f" -> Archived already-parsed file to: 3_Archive/{filename}")
            except Exception as e:
                print(f" -> Failed to archive {file_path}: {e}")

    print(f"Pipeline parsing complete. Generated {new_conversions} new raw text files.")


if __name__ == "__main__":
    process_pipeline()
