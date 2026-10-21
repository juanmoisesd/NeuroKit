import fitz  # PyMuPDF
import os

try:
    import pytesseract
    from PIL import Image
    import io
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

class PDFExtractor:
    def __init__(self):
        self.filepath = None
        self.doc = None
        self.num_pages = 0

        # Check if tesseract is installed by trying to get its version
        self.tesseract_ready = False
        if TESSERACT_AVAILABLE:
            try:
                pytesseract.get_tesseract_version()
                self.tesseract_ready = True
            except Exception:
                self.tesseract_ready = False

    def load_document(self, filepath):
        """Loads a PDF document."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"El archivo {filepath} no existe.")

        self.close_document()
        self.filepath = filepath
        self.doc = fitz.open(filepath)
        self.num_pages = len(self.doc)
        return self.num_pages

    def close_document(self):
        """Closes the current document."""
        if self.doc:
            self.doc.close()
            self.doc = None
            self.filepath = None
            self.num_pages = 0

    def extract_page(self, page_num, use_ocr_if_empty=True, ocr_lang='spa'):
        """
        Extracts text from a specific page.
        Returns a list of paragraph blocks: [{"text": "...", "bbox": ...}, ...]
        """
        if not self.doc or page_num < 0 or page_num >= self.num_pages:
            return []

        page = self.doc.load_page(page_num)

        # Try to extract text blocks (maintains reading order and paragraphs somewhat)
        # block format: (x0, y0, x1, y1, "lines in block", block_no, block_type)
        # block_type == 0 means text
        blocks = page.get_text("blocks")

        paragraphs = []
        has_text = False

        for b in blocks:
            if b[6] == 0:  # text block
                text = b[4].strip()
                if text:
                    # Clean up some common PDF extraction artifacts like mid-sentence newlines
                    text = text.replace('\n', ' ').replace('  ', ' ')
                    paragraphs.append({
                        "text": text,
                        "bbox": (b[0], b[1], b[2], b[3])
                    })
                    has_text = True

        # If no text was found, it might be a scanned PDF or images
        if not has_text and use_ocr_if_empty and self.tesseract_ready:
            paragraphs = self._perform_ocr_on_page(page, ocr_lang)

        return paragraphs

    def _perform_ocr_on_page(self, page, lang='spa'):
        """Extracts text using OCR on images within the page or rendering the page."""
        paragraphs = []

        # Approach: Render the whole page to an image and run OCR on it
        # This handles cases where text is part of a large image or scanned page
        try:
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            # Use tesseract to get data including bounding boxes (to somewhat keep block structure)
            # data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
            # Simpler approach: just extract text string and split by double newline to approximate paragraphs

            text = pytesseract.image_to_string(image, lang=lang)
            if text.strip():
                # Rough splitting into paragraphs
                raw_paragraphs = text.split('\n\n')
                for p in raw_paragraphs:
                    p = p.strip().replace('\n', ' ')
                    if p:
                        # We don't have accurate bboxes this way, so provide None or dummy
                        paragraphs.append({
                            "text": p,
                            "bbox": None
                        })

        except Exception as e:
            print(f"Error durante OCR: {e}")

        return paragraphs
