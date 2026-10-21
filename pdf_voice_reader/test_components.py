import os
import json
import pytest
from config import ConfigManager
from tts_engine import TTSEngine

def test_config_manager(tmpdir):
    config_file = os.path.join(tmpdir, "test_config.json")
    cm = ConfigManager(config_file=config_file)

    assert cm.get("rate") == 150
    assert cm.get("recent_files") == []

    cm.set("rate", 200)
    assert cm.get("rate") == 200

    cm.save_last_position("dummy.pdf", 2, 5)
    page, block = cm.get_last_position("dummy.pdf")
    assert page == 2
    assert block == 5

    cm.add_recent_file("file1.pdf")
    cm.add_recent_file("file2.pdf")
    assert cm.get_recent_files() == ["file2.pdf", "file1.pdf"]

    assert os.path.exists(config_file)
    with open(config_file, "r") as f:
        data = json.load(f)
        assert data["rate"] == 200

def test_tts_chunking():
    # Instantiate without initializing pyttsx3 by mocking it or using a dummy TTSEngine method directly
    # Since we need to test the pure logic of chunking, we can temporarily patch pyttsx3.init
    import unittest.mock as mock
    with mock.patch('pyttsx3.init'):
        tts = TTSEngine()

        text = "Hola. ¿Cómo estás? Bien, gracias."
        chunks = tts._chunk_text(text)
        assert chunks == ["Hola.", "¿Cómo estás?", "Bien, gracias."]

        long_text = "a " * 300
        chunks = tts._chunk_text(long_text)
        assert len(chunks) > 1
        assert len(chunks[0]) <= 250

def test_pdf_extraction(tmpdir):
    from pdf_extractor import PDFExtractor
    import fitz

    pdf_path = os.path.join(tmpdir, "dummy.pdf")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Este es el primer párrafo.")
    page.insert_text((50, 100), "Y este es el segundo párrafo.")
    doc.save(pdf_path)
    doc.close()

    extractor = PDFExtractor()
    extractor.load_document(pdf_path)
    assert extractor.num_pages == 1

    blocks = extractor.extract_page(0)
    assert len(blocks) >= 2
    assert "primer párrafo" in blocks[0]['text'] or "primer párrafo" in blocks[1]['text']
