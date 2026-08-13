#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Buscador de imágenes libres de derechos de autor con procesamiento de lenguaje natural.
"""

import sys
import warnings
import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from deep_translator import GoogleTranslator
import spacy

# Omitir advertencias espurias de BeautifulSoup cuando recibe una URL simple
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# Intentamos cargar los modelos de spaCy en español e inglés
try:
    nlp_es = spacy.load("es_core_news_sm")
except OSError:
    nlp_es = None

try:
    nlp_en = spacy.load("en_core_web_sm")
except OSError:
    nlp_en = None


def clean_html(html_str):
    """Limpia etiquetas HTML de textos de metadatos de Wikimedia Commons."""
    if not html_str:
        return ""
    # Si parece una URL simple o no tiene etiquetas HTML, devolvemos tal cual para evitar advertencias
    if html_str.startswith("http://") or html_str.startswith("https://") or ("<" not in html_str and ">" not in html_str):
        return html_str.strip()
    try:
        return BeautifulSoup(html_str, "html.parser").get_text().strip()
    except Exception:
        return html_str.strip()


def detect_language(text):
    """Detecta de forma básica si el texto ingresado está en español o inglés."""
    # Heurística simple de palabras comunes en español
    spanish_words = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "con", "en", "para", "por", "y", "o", "que", "es", "lucha", "caballero"}
    words = set(text.lower().split())
    if words.intersection(spanish_words):
        return "es"
    return "en"


def analyze_phrase(text, lang="es"):
    """
    Analiza el contexto de una frase usando spaCy para extraer:
    - Sentido/significado (Noun Chunks / Frases nominales relevantes)
    - Contexto/Escenario (Lugares, elementos situacionales)
    - Personajes/Sujetos (Entidades o sustantivos principales)
    - Acciones (Verbos)
    - Atributos (Adjetivos descriptivos)
    """
    nlp = nlp_es if lang == "es" else nlp_en
    if not nlp:
        # Fallback si el modelo de spacy no está instalado/cargado
        return {
            "meaning": [text],
            "characters": [],
            "actions": [],
            "context": [],
            "attributes": []
        }

    doc = nlp(text)

    # 1. Significado / Sentido (Frases nominales)
    meaning_chunks = [chunk.text for chunk in doc.noun_chunks]

    # 2. Personajes / Sujetos (Entidades o sustantivos principales)
    characters = []
    # Usar entidades reconocidas
    for ent in doc.ents:
        characters.append(ent.text)
    # Usar sujetos gramaticales
    for token in doc:
        if token.dep_ in ("nsubj", "nsubj:pass"):
            characters.append(token.text)

    # Filtrar personajes vacíos y duplicados
    characters = sorted(list(set([c for c in characters if c])))
    if not characters:
        # Tomar los primeros sustantivos comunes/propios como personajes por defecto
        characters = [t.text for t in doc if t.pos_ in ("NOUN", "PROPN")][:2]

    # 3. Acciones (Verbos)
    actions = [token.lemma_ for token in doc if token.pos_ in ("VERB", "AUX")]
    if not actions:
        # Fallback por si la palabra de acción principal fue categorizada como sustantivo (p. ej. 'lucha')
        actions = [t.text for t in doc if t.pos_ == "NOUN" and t.dep_ == "ROOT"]

    # 4. Contexto / Escenario / Entorno (Sustantivos precedidos por preposiciones de ubicación/lugar)
    context_elements = []
    for token in doc:
        if token.pos_ == "NOUN" and token.dep_ in ("obl", "nmod"):
            # Si el token tiene una preposición hija de lugar
            preps = [w for w in token.children if w.pos_ == "ADP"]
            if preps and preps[0].text.lower() in ("en", "sobre", "bajo", "entre", "ante", "desde", "hacia", "in", "on", "under", "between", "at", "through"):
                context_elements.append(f"{preps[0].text} {token.text}")
            else:
                context_elements.append(token.text)

    if not context_elements:
        # Tomamos sustantivos secundarios que no son personajes principales
        context_elements = [t.text for t in doc if t.pos_ == "NOUN" and t.text not in characters]

    # 5. Atributos (Adjetivos descriptivos)
    attributes = [token.text for token in doc if token.pos_ == "ADJ"]

    return {
        "meaning": meaning_chunks if meaning_chunks else [text],
        "characters": characters,
        "actions": actions,
        "context": sorted(list(set(context_elements))),
        "attributes": attributes
    }


def generate_prompt(analysis, original_text, source_lang="es"):
    """
    Genera un prompt de búsqueda optimizado en inglés.
    Utiliza deep-translator para traducir elementos clave o el texto original al inglés,
    sintetizando un prompt descriptivo ideal para buscadores de imágenes libres.
    """
    if source_lang == "es":
        # Traducir el texto original completo al inglés
        try:
            translated_text = GoogleTranslator(source="es", target="en").translate(original_text)
        except Exception:
            # Fallback en caso de fallas de conexión o de traducción
            translated_text = original_text
    else:
        translated_text = original_text

    # Extraer y simplificar elementos clave del análisis para optimizar términos de búsqueda
    # Usamos palabras clave de personajes, contexto y adjetivos traducidos si es posible
    keywords = []

    # Traducir elementos individuales para construir tags/palabras clave refinadas
    for item in (analysis["characters"] + analysis["context"] + analysis["attributes"]):
        # Limpiar preposiciones simples si las hay
        cleaned_item = item.replace("en ", "").replace("sobre ", "").replace("bajo ", "").replace("entre ", "")
        if source_lang == "es" and cleaned_item:
            try:
                translated_item = GoogleTranslator(source="es", target="en").translate(cleaned_item)
                if translated_item:
                    keywords.append(translated_item.lower())
            except Exception:
                keywords.append(cleaned_item.lower())
        else:
            if cleaned_item:
                keywords.append(cleaned_item.lower())

    # Eliminar duplicados en palabras clave
    keywords = sorted(list(set(keywords)))

    # El prompt consistirá en la traducción descriptiva limpia
    prompt_query = translated_text.strip()

    return {
        "prompt": prompt_query,
        "keywords": keywords
    }


def search_free_images(prompt, limit=5):
    """
    Busca imágenes libres de derechos de autor en Wikimedia Commons que coincidan con el prompt.
    Utiliza la API de búsqueda de MediaWiki con namespace 6 (File/Archivo).
    Devuelve una lista de diccionarios con la información de cada imagen encontrada:
    - title: Título del archivo en Commons
    - url: URL de descarga directa de la imagen original
    - license: Tipo de licencia (p. ej., cc-by-sa, pd, etc.)
    - license_url: Enlace a los términos de la licencia
    - artist: Autor/Creador de la imagen (limpio de HTML)
    - description: Descripción de la imagen (limpia de HTML)
    """
    # Usamos el parámetro 'filetype:bitmap' para asegurar que encontramos formatos de imagen reales como jpg/png/webp
    search_query = f"filetype:bitmap {prompt}"

    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": search_query,
        "gsrnamespace": 6,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "gsrlimit": limit
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        # Fallback silencioso o reintento sin el prefijo 'filetype:bitmap'
        try:
            params["gsrsearch"] = prompt
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []

    pages = data.get("query", {}).get("pages", {})
    results = []

    for page_id, page_data in pages.items():
        title = page_data.get("title", "")
        imageinfo_list = page_data.get("imageinfo", [])
        if not imageinfo_list:
            continue

        info = imageinfo_list[0]
        image_url = info.get("url", "")
        extmetadata = info.get("extmetadata", {})

        # Extraemos metadatos detallados y los limpiamos de etiquetas HTML
        license_name = extmetadata.get("License", {}).get("value", "Desconocida/CC")
        license_url = extmetadata.get("LicenseUrl", {}).get("value", "")
        usage_terms = extmetadata.get("UsageTerms", {}).get("value", "")
        artist = extmetadata.get("Artist", {}).get("value", "Desconocido")
        description = extmetadata.get("ImageDescription", {}).get("value", "Sin descripción")

        results.append({
            "title": title,
            "url": image_url,
            "license": clean_html(license_name),
            "license_url": clean_html(license_url),
            "usage_terms": clean_html(usage_terms),
            "artist": clean_html(artist),
            "description": clean_html(description)
        })

    return results


def main():
    """Ejecución interactiva desde terminal."""
    if len(sys.argv) < 2:
        print("Uso: python image_finder.py \"<frase_descriptiva_de_la_imagen>\" [limite_de_resultados]")
        sys.exit(1)

    phrase = sys.argv[1]
    limit = 5
    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except ValueError:
            pass

    print("\n" + "="*60)
    print(" BUSCADOR DE IMÁGENES LIBRES (NLP + WIKIMEDIA COMMONS)")
    print("="*60)
    print(f"Frase original: '{phrase}'")

    # 1. Detectar idioma
    lang = detect_language(phrase)
    print(f"Idioma detectado: {lang.upper()}")

    # 2. Analizar contexto
    print("\nAnalyzing phrase context (spaCy)...")
    analysis = analyze_phrase(phrase, lang)
    print(" - Significado/Frases clave:", analysis["meaning"])
    print(" - Personajes/Sujetos:", analysis["characters"])
    print(" - Acciones principales:", analysis["actions"])
    print(" - Contexto/Entorno:", analysis["context"])
    print(" - Atributos/Adjetivos:", analysis["attributes"])

    # 3. Generar Prompt optimizado
    print("\nTranslating and generating image prompt (deep-translator)...")
    prompt_data = generate_prompt(analysis, phrase, lang)
    print(f" - Prompt de búsqueda generado (EN): '{prompt_data['prompt']}'")
    print(f" - Palabras clave generadas: {prompt_data['keywords']}")

    # 4. Buscar imágenes libres
    print(f"\nSearching Wikimedia Commons (Limit: {limit})...")
    images = search_free_images(prompt_data["prompt"], limit)

    if not images:
        print("\nNo se encontraron imágenes exactas con la frase completa. Intentando búsqueda por palabras clave...")
        # Intento de fallback usando las primeras 3 palabras clave más relevantes combinadas
        fallback_query = " ".join(prompt_data["keywords"][:3])
        if fallback_query:
            print(f"Búsqueda alternativa: '{fallback_query}'")
            images = search_free_images(fallback_query, limit)

    if not images:
        print("\n❌ No se encontraron imágenes libres para esta descripción.")
        return

    print(f"\n🎉 ¡Se encontraron {len(images)} imágenes que encajan con tu búsqueda!:\n")
    for i, img in enumerate(images, 1):
        print(f"[{i}] Título: {img['title']}")
        print(f"    URL descarga: {img['url']}")
        print(f"    Autor: {img['artist']}")
        print(f"    Licencia: {img['license']} ({img['usage_terms']})")
        if img['license_url']:
            print(f"    URL Licencia: {img['license_url']}")
        print(f"    Descripción: {img['description'][:150]}...")
        print("-" * 50)


if __name__ == "__main__":
    main()
