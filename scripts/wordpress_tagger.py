import asyncio
import json
import logging
import os
import re
import urllib.parse
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class WordPressTagger:
    def __init__(self, login_url, username, password):
        self.login_url = login_url
        self.username = username
        self.password = password
        self.playwright = None
        self.browser = None
        self.page = None
        self.tag_cache = {}

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        await self.login()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def login(self):
        logger.info("Logging in to WordPress...")
        await self.page.goto(self.login_url, timeout=60000)
        await self.page.fill("#user_login", self.username)
        await self.page.fill("#user_pass", self.password)
        await self.page.click("#wp-submit")
        try:
            await self.page.wait_for_url("**/wp-admin/**", timeout=60000)
            logger.info("Successfully logged in.")
        except Exception:
            if "wp-admin" in self.page.url:
                logger.info("Already in wp-admin, continuing...")
            else:
                raise Exception("Login failed. Please check credentials.")

    def generate_tags(self, title):
        title = re.sub(r'<[^>]+>', '', title)
        clean_title = re.sub(r'[^\w\s]', '', title)
        words = clean_title.split()
        keywords = [w for w in words if len(w) > 3]

        tags = set(keywords)
        for i in range(len(keywords) - 1):
            tags.add(f"{keywords[i]} {keywords[i+1]}")
        for i in range(len(keywords) - 2):
            tags.add(f"{keywords[i]} {keywords[i+1]} {keywords[i+2]}")

        lowered_title = title.lower()
        if any(w in lowered_title for w in ["psicología", "comportamiento", "mente"]):
            tags.update(["psicología clínica", "salud mental", "bienestar emocional"])
        if any(w in lowered_title for w in ["educación", "enseñanza", "aprendizaje"]):
            tags.update(["pedagogía", "desarrollo cognitivo", "formación"])
        if any(w in lowered_title for w in ["ambiental", "sostenible", "naturaleza"]):
            tags.update(["medio ambiente", "sostenibilidad", "ecología"])

        general_tags = ["investigación", "ciencia", "análisis", "divulgación", "conocimiento", "estudio"]
        idx = 0
        while len(tags) < 12 and idx < len(general_tags):
            tags.add(general_tags[idx])
            idx += 1

        return sorted(list(tags))[:15]

    async def get_total_posts(self):
        result = await self.page.evaluate("""
            async () => {
                const response = await fetch('/wp-json/wp/v2/posts?per_page=1');
                return response.headers.get('X-WP-Total');
            }
        """)
        return int(result) if result else 0

    async def get_posts(self, page=1, per_page=10):
        api_url = f"/wp-json/wp/v2/posts?page={page}&per_page={per_page}&_fields=id,title,tags"
        return await self.page.evaluate(f"""
            async () => {{
                const response = await fetch('{api_url}');
                if (!response.ok) return null;
                return await response.json();
            }}
        """)

    async def get_or_create_tag(self, name):
        name_lower = name.lower()
        if name_lower in self.tag_cache:
            return self.tag_cache[name_lower]

        encoded_name = urllib.parse.quote(name)
        search_url = f"/wp-json/wp/v2/tags?search={encoded_name}"
        try:
            tags = await self.page.evaluate(f"""
                async () => {{
                    const response = await fetch('{search_url}');
                    if (!response.ok) return null;
                    return await response.json();
                }}
            """)

            if isinstance(tags, list):
                for tag in tags:
                    if tag['name'].lower() == name_lower:
                        self.tag_cache[name_lower] = tag['id']
                        return tag['id']

            new_tag = await self.page.evaluate(f"""
                async () => {{
                    const response = await fetch('/wp-json/wp/v2/tags', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'X-WP-Nonce': wpApiSettings.nonce
                        }},
                        body: JSON.stringify({{name: {json.dumps(name)}}})
                    }});
                    return await response.json();
                }}
            """)
            if isinstance(new_tag, dict):
                tid = new_tag.get('id') or (new_tag.get('data', {}).get('term_id') if new_tag.get('code') == 'term_exists' else None)
                if tid:
                    self.tag_cache[name_lower] = tid
                    return tid
        except Exception as e:
            logger.error(f"Error handling tag '{name}': {e}")
        return None

    async def update_post_tags(self, post_id, existing_tag_ids, new_tag_names):
        tag_ids = list(existing_tag_ids)
        for name in new_tag_names:
            tag_id = await self.get_or_create_tag(name)
            if tag_id and tag_id not in tag_ids:
                tag_ids.append(tag_id)

        return await self.page.evaluate(f"""
            async () => {{
                const response = await fetch('/wp-json/wp/v2/posts/{post_id}', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-WP-Nonce': wpApiSettings.nonce
                    }},
                    body: JSON.stringify({{tags: {json.dumps(tag_ids)}}})
                }});
                return await response.json();
            }}
        """)

async def main():
    login_url = "https://juanmoisesdelaserna.es/wp-login.php"
    username = os.getenv("WP_USERNAME")
    password = os.getenv("WP_PASSWORD")

    if not username or not password:
        logger.error("Please set WP_USERNAME and WP_PASSWORD environment variables.")
        return

    async with WordPressTagger(login_url, username, password) as tagger:
        total_posts = await tagger.get_total_posts()
        logger.info(f"Total posts found: {total_posts}")

        per_page = 50
        total_pages = (total_posts // per_page) + 1

        for page in range(1, total_pages + 1):
            logger.info(f"Processing page {page}/{total_pages}...")
            posts = await tagger.get_posts(page, per_page)
            if not posts: break

            for post in posts:
                if len(post['tags']) < 10:
                    new_tags = tagger.generate_tags(post['title']['rendered'])
                    await tagger.update_post_tags(post['id'], post['tags'], new_tags)
                    logger.info(f"Updated post {post['id']} with tags.")
                else:
                    logger.debug(f"Skipped post {post['id']}, already has enough tags.")

if __name__ == "__main__":
    asyncio.run(main())
