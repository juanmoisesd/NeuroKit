import requests
import json
import os

# Zenodo API configuration
ACCESS_TOKEN = os.getenv("ZENODO_TOKEN")
BASE_URL = "https://zenodo.org/api"

def publish_to_zenodo():
    if not ACCESS_TOKEN:
        print("Error: ZENODO_TOKEN environment variable not set.")
        return None

    print("Iniciando proceso de publicación en Zenodo...")

    # 1. Create a new deposition
    headers = {"Content-Type": "application/json"}
    params = {'access_token': ACCESS_TOKEN}

    metadata = {
        'metadata': {
            'title': 'Scripts de Análisis Neurofisiológico para NeuroKit: Automatización y Reproducibilidad',
            'upload_type': 'software',
            'description': 'Este paquete contiene scripts de Python para el procesamiento automatizado de señales de ECG, EDA y datos multimodales. Diseñado para investigadores de alto nivel, facilita el cumplimiento de los estándares de Ciencia Abierta (Open Science) mediante la automatización de la limpieza, análisis estadístico y visualización de datos biofisiológicos.',
            'creators': [{'name': 'de la Serna Tuya, Juan Moisés',
                           'affiliation': 'Universidad Internacional de La Rioja (UNIR)',
                           'orcid': '0000-0002-8401-8018'}],
            'keywords': ['neuroscience', 'neurokit2', 'ECG', 'EDA', 'multimodal', 'open-science', 'python'],
            'license': 'mit',
            'access_right': 'open'
        }
    }

    response = requests.post(f"{BASE_URL}/deposit/depositions",
                             params=params,
                             json=metadata,
                             headers=headers)

    if response.status_code != 201:
        print(f"Error al crear la deposición: {response.status_code}")
        print(response.json())
        return

    deposition_id = response.json()['id']
    bucket_url = response.json()['links']['bucket']
    print(f"Deposición creada exitosamente. ID: {deposition_id}")

    # 2. Upload files
    files_to_upload = [
        'scripts/analyze_ecg.py',
        'scripts/analyze_eda.py',
        'scripts/analyze_multimodal.py',
        'scripts/README.md'
    ]

    for file_path in files_to_upload:
        file_name = os.path.basename(file_path)
        print(f"Subiendo {file_name}...")
        with open(file_path, "rb") as fp:
            upload_response = requests.put(
                f"{bucket_url}/{file_name}",
                data=fp,
                params=params,
            )
        if upload_response.status_code == 200:
            print(f"Archivo {file_name} subido correctamente.")
        else:
            print(f"Error al subir {file_name}: {upload_response.status_code}")

    # 3. Publish (Optional - uncomment to make it permanent and get a real DOI)
    print("Publicando la deposición para obtener el DOI...")
    publish_response = requests.post(f"{BASE_URL}/deposit/depositions/{deposition_id}/actions/publish",
                                     params=params)

    if publish_response.status_code == 202:
        doi = publish_response.json()['doi']
        print(f"¡Publicación exitosa! DOI asignado: {doi}")
        return doi
    else:
        print(f"Error al publicar: {publish_response.status_code}")
        print(publish_response.json())
        return None

if __name__ == "__main__":
    doi = publish_to_zenodo()
    if doi:
        # Update README with the new DOI
        readme_path = 'scripts/README.md'
        with open(readme_path, 'r') as f:
            content = f.read()

        updated_content = content.replace("[Pendiente tras publicación en Zenodo]", doi)

        with open(readme_path, 'w') as f:
            f.write(updated_content)
        print("README.md actualizado con el DOI.")
