import asyncio
import os
import argparse
from playwright.async_api import async_playwright

async def create_categories(file_path, base_url, username, password):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        categories = [line.strip() for line in f if line.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Logging in to {base_url}...")
        await page.goto(f"{base_url}/wp-login.php")
        await page.fill("#user_login", username)
        await page.fill("#user_pass", password)
        await page.click("#wp-submit")

        try:
            await page.wait_for_url("**/wp-admin/**", timeout=60000)
            print("Login successful.")
        except Exception as e:
            print(f"Login failed: {e}")
            await browser.close()
            return

        print("Navigating to categories page...")
        await page.goto(f"{base_url}/wp-admin/edit-tags.php?taxonomy=category")

        for i, category_name in enumerate(categories):
            print(f"[{i+1}/{len(categories)}] Adding category: {category_name}")
            try:
                await page.wait_for_selector("#tag-name", timeout=10000)
                await page.fill("#tag-name", category_name)
                await page.click("#submit")

                # Wait for form to clear after successful AJAX add
                await page.wait_for_function('document.querySelector("#tag-name").value === ""', timeout=10000)

            except Exception as e:
                print(f"Error adding {category_name}: {e}")
                # Recovery: reload the page
                await page.goto(f"{base_url}/wp-admin/edit-tags.php?taxonomy=category")
                await page.wait_for_load_state("load")

        print("Finished adding categories.")
        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch add categories to WordPress.")
    parser.add_argument("--file", default="data/blog_categories_es.txt", help="Path to categories file")
    parser.add_argument("--url", default="https://juanmoisesdelaserna.es", help="WordPress site URL")

    args = parser.parse_args()

    username = os.getenv("WP_USERNAME")
    password = os.getenv("WP_PASSWORD")

    if not username or not password:
        print("Please set WP_USERNAME and WP_PASSWORD environment variables.")
    else:
        asyncio.run(create_categories(args.file, args.url, username, password))
