import os
import re
import requests
import sys
from concurrent.futures import ThreadPoolExecutor

# Regex patterns for different file types
MD_LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\)\s]+)\)')
RST_LINK_RE = re.compile(r'`([^<]+)\s*<([^>]+)>`_')
HTML_LINK_RE = re.compile(r'href=["\'](https?://[^"\']+)["\']')
GENERIC_URL_RE = re.compile(r'https?://[^\s"\'<>{}|\\^~\[\]`]+(?<![\.\,\;\:\!\?\)\(\[\]])')

def extract_links(filepath):
    """Extracts links from a file based on its extension."""
    links = []
    ext = os.path.splitext(filepath)[1].lower()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []

    if ext == '.md':
        for text, url in MD_LINK_RE.findall(content):
            links.append({'text': text, 'url': url})
    elif ext == '.rst':
        for text, url in RST_LINK_RE.findall(content):
            links.append({'text': text, 'url': url})
    elif ext == '.html':
        for url in HTML_LINK_RE.findall(content):
            links.append({'text': '', 'url': url})

    for url in GENERIC_URL_RE.findall(content):
        if not any(link['url'] == url for link in links):
            links.append({'text': '', 'url': url})

    return links

def crawl_repo(root_dir='.', target_files=None):
    """Crawls the repository for supported files."""
    all_links = {}
    supported_exts = {'.md', '.rst', '.html', '.py'}

    if target_files:
        for filepath in target_files:
            if os.path.exists(filepath):
                links = extract_links(filepath)
                if links:
                    all_links[filepath] = links
        return all_links

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if any(file.endswith(ext) for ext in supported_exts):
                filepath = os.path.join(root, file)
                links = extract_links(filepath)
                if links:
                    all_links[filepath] = links
    return all_links

def validate_link(url, timeout=10):
    """Checks if a URL is broken."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        if response.status_code >= 400 and response.status_code != 405:
            return response.status_code
        if response.status_code == 405:
            response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
        return response.status_code
    except requests.exceptions.RequestException:
        return "Timeout/Unreachable"

def get_wayback_url(url):
    """Fetches the latest archived version from Wayback Machine."""
    api_url = f"https://archive.org/wayback/available?url={url}"
    try:
        response = requests.get(api_url, timeout=10)
        data = response.json()
        if 'archived_snapshots' in data and 'closest' in data['archived_snapshots']:
            return data['archived_snapshots']['closest']['url']
    except Exception:
        pass
    return None

def search_updated_url(broken_url, link_text, all_repo_links):
    """Searches for a potential updated URL based on text, with domain matching."""
    if not link_text or len(link_text) < 5: # Require more descriptive text
        return None

    try:
        broken_domain = broken_url.split('/')[2]
    except IndexError:
        return None

    for filepath, links in all_repo_links.items():
        for link in links:
            if link['text'] == link_text and link['url'] != broken_url:
                try:
                    candidate_domain = link['url'].split('/')[2]
                except IndexError:
                    continue
                # Only accept if domains match to avoid generic text mismatch (like "Profile")
                if candidate_domain == broken_domain:
                    # Simple validation for candidate
                    if validate_link(link['url']) == 200:
                        return link['url']
    return None

def main():
    target_files = sys.argv[1:] if len(sys.argv) > 1 else None
    repo_links = crawl_repo(target_files=target_files)
    unique_urls = set()
    for links in repo_links.values():
        for link in links:
            unique_urls.add(link['url'])

    print(f"Validating {len(unique_urls)} unique URLs...")
    url_statuses = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(validate_link, url): url for url in unique_urls}
        for future in future_to_url:
            url_statuses[future_to_url[future]] = future.result()

    fixes = {}
    manual_review = []

    for filepath, links in repo_links.items():
        file_updated = False
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue

        for link in links:
            url = link['url']
            status = url_statuses[url]
            # Ignore 200 OK and some common non-broken statuses
            if status == 200 or status == "Error" or status == 999: continue

            updated_url = search_updated_url(url, link['text'], repo_links)
            if not updated_url:
                updated_url = get_wayback_url(url)

            if updated_url:
                # Use word boundaries or other markers to be safer during replace
                # However, URLs can be complex. Simple replace for now,
                # but the workflow runs it, not this PR.
                if url in content:
                    content = content.replace(url, updated_url)
                    fixes[url] = updated_url
                    file_updated = True
            else:
                manual_review.append(f"{filepath}: {url} ({status})")

        if file_updated:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"Error writing {filepath}: {e}")

    # Summary Report
    print("\n--- LINK FIXER REPORT ---")
    print(f"Total links checked: {len(unique_urls)}")
    print(f"Total fixes applied: {len(fixes)}")
    for old, new in fixes.items():
        print(f"  Fixed: {old} -> {new}")

    print(f"\nManual review required: {len(manual_review)}")
    for item in manual_review:
        print(f"  {item}")

if __name__ == "__main__":
    main()
