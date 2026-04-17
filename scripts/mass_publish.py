import os
import requests
import json
import time
import csv
from analyze_file import analyze

ACCESS_TOKEN = os.getenv("ZENODO_TOKEN")
BASE_URL = "https://zenodo.org/api"

def publish_dataset(filepath, registry_file):
    """
    Analyzes a dataset file and publishes it to Zenodo, obtaining a DOI.
    """
    if not os.path.exists(filepath):
        return None

    filename = os.path.basename(filepath)
    print(f"Processing {filepath}...")

    # Generate analysis
    analysis_text = analyze(filepath)
    analysis_filename = f"{filename}_analysis.txt"
    with open(analysis_filename, 'w') as f:
        f.write(analysis_text)

    # Zenodo Metadata
    params = {'access_token': ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    metadata = {
        'metadata': {
            'title': f'Dataset Analysis: {filename}',
            'upload_type': 'dataset',
            'description': f'Automated analysis report and raw data for file {filepath} from the NeuroKit project. Part of an Open Science reproducibility initiative.',
            'creators': [{'name': 'de la Serna Tuya, Juan Moisés',
                           'affiliation': 'Universidad Internacional de La Rioja (UNIR)',
                           'orcid': '0000-0002-8401-8018'}],
            'access_right': 'open',
            'license': 'cc-zero'
        }
    }

    try:
        # 1. Create Deposition
        r = requests.post(f"{BASE_URL}/deposit/depositions", params=params, json=metadata, headers=headers)
        if r.status_code == 429:
            print("Rate limit reached. Waiting 60s...")
            time.sleep(60)
            return publish_dataset(filepath, registry_file)
        if r.status_code != 201:
            print(f"Error creating deposition: {r.status_code} - {r.text}")
            return None

        depo = r.json()
        depo_id = depo['id']
        bucket_url = depo['links']['bucket']

        # 2. Upload Files
        with open(filepath, 'rb') as f:
            requests.put(f"{bucket_url}/{filename}", data=f, params=params)
        with open(analysis_filename, 'rb') as f:
            requests.put(f"{bucket_url}/{analysis_filename}", data=f, params=params)

        # 3. Publish
        r = requests.post(f"{BASE_URL}/deposit/depositions/{depo_id}/actions/publish", params=params)
        if r.status_code == 202:
            doi = r.json()['doi']
            print(f"Published {filename} -> {doi}")

            # Record in registry
            with open(registry_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([filepath, doi])
            return doi
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        if os.path.exists(analysis_filename):
            os.remove(analysis_filename)
    return None

if __name__ == "__main__":
    if not ACCESS_TOKEN:
        print("Error: ZENODO_TOKEN environment variable is required.")
        exit(1)

    registry = "published_dois.csv"
    if not os.path.exists(registry):
        with open(registry, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["filepath", "doi"])

    # List of files to process (e.g., from data/ and studies/ folders)
    files_to_process = []
    for root, dirs, files in os.walk('data'):
        for file in files:
            files_to_process.append(os.path.join(root, file))
    for root, dirs, files in os.walk('studies'):
        for file in files:
            if file.endswith('.csv'):
                files_to_process.append(os.path.join(root, file))

    # Filter out code/config
    exclude_exts = {'.py', '.pyc', '.sh', '.yml', '.yaml', '.bat', '.js', '.css', '.html', '.md', '.rst', '.ini', '.cfg', '.jsonld', '.xml', '.bib', '.cff'}
    files_to_process = [f for f in files_to_process if os.path.splitext(f)[1].lower() not in exclude_exts]

    print(f"Found {len(files_to_process)} candidates for publication.")

    # Check current registry to avoid duplicates
    published_paths = set()
    if os.path.exists(registry):
        with open(registry, 'r') as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                if row: published_paths.add(row[0])

    for fpath in files_to_process:
        if fpath not in published_paths:
            publish_dataset(fpath, registry)
            time.sleep(0.5) # Compliance with API rate limits
