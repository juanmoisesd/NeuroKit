# -*- coding: utf-8 -*-

"""
Unit tests for image_finder.py
"""

import unittest
from unittest.mock import patch, MagicMock
import image_finder


class TestImageFinder(unittest.TestCase):

    def test_clean_html(self):
        # Basic tags removal
        self.assertEqual(image_finder.clean_html("<p>Hello <b>World</b></p>"), "Hello World")
        # Simple plain text or URL returning untouched
        self.assertEqual(image_finder.clean_html("https://example.com"), "https://example.com")
        self.assertEqual(image_finder.clean_html("Just standard text"), "Just standard text")

    def test_detect_language(self):
        self.assertEqual(image_finder.detect_language("Un caballero en un caballo"), "es")
        self.assertEqual(image_finder.detect_language("A fast red car racing"), "en")

    def test_analyze_phrase_spanish(self):
        phrase = "Un valiente caballero con armadura dorada lucha contra un dragón gigante"
        analysis = image_finder.analyze_phrase(phrase, lang="es")

        self.assertIn("caballero", analysis["characters"])
        self.assertIn("valiente", analysis["attributes"])
        self.assertIn("dorada", analysis["attributes"])
        self.assertTrue(len(analysis["meaning"]) > 0)

    @patch("image_finder.GoogleTranslator")
    def test_generate_prompt(self, mock_translator_class):
        # Mock GoogleTranslator translate method
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.side_effect = lambda text: {
            "Un caballero": "A knight",
            "caballero": "knight",
            "armadura": "armor",
            "valiente": "brave"
        }.get(text, text)
        mock_translator_class.return_value = mock_translator_instance

        analysis = {
            "meaning": ["Un caballero"],
            "characters": ["caballero"],
            "actions": ["lucha"],
            "context": ["armadura"],
            "attributes": ["valiente"]
        }

        prompt_data = image_finder.generate_prompt(analysis, "Un caballero", source_lang="es")

        # Verify prompt and keywords structures
        self.assertIn("prompt", prompt_data)
        self.assertIn("keywords", prompt_data)

    @patch("requests.get")
    def test_search_free_images(self, mock_get):
        # Mock API response of Wikimedia Commons
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "12345": {
                        "title": "File:TestImage.jpg",
                        "imageinfo": [
                            {
                                "url": "https://upload.wikimedia.org/wikipedia/commons/test.jpg",
                                "extmetadata": {
                                    "License": {"value": "pd"},
                                    "LicenseUrl": {"value": "https://creativecommons.org/publicdomain/zero/1.0/"},
                                    "UsageTerms": {"value": "Public domain"},
                                    "Artist": {"value": "John Doe"},
                                    "ImageDescription": {"value": "A beautiful test image"}
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        results = image_finder.search_free_images("test query", limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "File:TestImage.jpg")
        self.assertEqual(results[0]["url"], "https://upload.wikimedia.org/wikipedia/commons/test.jpg")
        self.assertEqual(results[0]["license"], "pd")
        self.assertEqual(results[0]["artist"], "John Doe")


if __name__ == "__main__":
    unittest.main()
