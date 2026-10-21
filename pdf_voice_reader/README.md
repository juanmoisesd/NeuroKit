# PDF Voice Reader Español

Aplicación de escritorio para Windows 10 que permite abrir documentos PDF y escucharlos íntegramente en español mediante síntesis de voz (TTS).

Todo el procesamiento, tanto la extracción de texto como el motor de voz (SAPI5 por defecto en Windows), se realiza localmente garantizando la privacidad. También incorpora soporte para OCR básico mediante Tesseract para PDFs escaneados (si está instalado).

## Características

- Lectura completa de documentos PDF en español.
- Controles de reproducción: Reproducir, Pausar, Detener.
- Navegación por párrafos y páginas.
- Selector de voz local y velocidad de lectura.
- Guardado automático de la última posición de lectura y biblioteca de documentos recientes.
- Procesamiento 100% local, sin envío de datos a servidores externos.

## Requisitos

- Python 3.12 (o compatible)
- Dependencias (ver `requirements.txt`)

Opcional para OCR:
- Instalar Tesseract OCR en el sistema y añadirlo al PATH.

## Instalación y Ejecución

1. Clona el repositorio e ingresa a la carpeta `pdf_voice_reader`.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta la aplicación:
   ```bash
   python main.py
   ```

## Compilación a Ejecutable (Windows)

Para generar un ejecutable distribuible `.exe` en Windows:

1. Ejecuta el script de compilación:
   ```cmd
   build.bat
   ```
2. El ejecutable se generará en la carpeta `dist/PDF Voice Reader/`.

*Nota: La compilación debe realizarse en un entorno Windows real para generar un ejecutable nativo de Windows 10.*
