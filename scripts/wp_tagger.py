
import os
import asyncio
import argparse
import re
from playwright.async_api import async_playwright

def clean_word(word):
    """Removes punctuation from a word."""
    return re.sub(r'[^\w\s]', '', word).strip()

def generate_tags(title, existing_tags_str=""):
    """
    Generates relevant tags and appends them to existing ones.
    """
    # Simple stop words to exclude
    stop_words = {"sobre", "donde", "desde", "estas", "entre", "hacia", "hasta", "tanto", "quien"}

    words = title.lower().split()
    new_tags = []
    for w in words:
        cleaned = clean_word(w)
        if len(cleaned) > 4 and cleaned not in stop_words:
            new_tags.append(cleaned)

    # Domain specific fillers
    fillers = [
        "psicología", "neurociencia", "salud mental", "bienestar",
        "investigación", "divulgación", "ciencia", "comportamiento",
        "cerebro", "mente", "emociones", "terapia"
    ]

    for f in fillers:
        if len(new_tags) >= 15: # Aim for more to ensure at least 10
            break
        if f not in new_tags:
            new_tags.append(f)

    # Merge with existing tags
    existing_tags = [t.strip() for t in existing_tags_str.split(",") if t.strip()]
    combined_tags = list(existing_tags)
    for nt in new_tags:
        if nt.lower() not in [et.lower() for et in combined_tags]:
            combined_tags.append(nt)

    # Ensure at least 10 tags total
    if len(combined_tags) < 10:
        for f in fillers:
            if f.lower() not in [et.lower() for et in combined_tags]:
                combined_tags.append(f)
            if len(combined_tags) >= 10:
                break

    return ", ".join(combined_tags)

async def run_tagger(max_posts=20, start_page=1):
    user = os.environ.get("WP_USER")
    password = os.environ.get("WP_PASS")

    if not user or not password:
        print("Error: WP_USER and WP_PASS environment variables must be set.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Logging in to WordPress...")
        await page.goto("https://juanmoisesdelaserna.es/wp-login.php")
        await page.fill("#user_login", user)
        await page.fill("#user_pass", password)
        await page.click("#wp-submit")
        await page.wait_for_load_state("networkidle")

        total_tagged = 0
        current_page = start_page

        while total_tagged < max_posts:
            print(f"Processing admin page {current_page}...")
            await page.goto(f"https://juanmoisesdelaserna.es/wp-admin/edit.php?paged={current_page}")
            await page.wait_for_load_state("networkidle")

            posts = await page.evaluate("""
                () => {
                    const results = [];
                    document.querySelectorAll('tr[id^="post-"]').forEach(tr => {
                        const id = tr.id.replace('post-', '');
                        const titleEl = tr.querySelector('.row-title');
                        const tagsEl = tr.querySelector('.column-tags');
                        if (titleEl) {
                            results.push({
                                id,
                                title: titleEl.innerText,
                                current_tags: tagsEl ? tagsEl.innerText : ""
                            });
                        }
                    });
                    return results;
                }
            """)

            if not posts:
                print("No more posts found.")
                break

            for post in posts:
                if total_tagged >= max_posts:
                    break

                post_id = post['id']
                title = post['title']
                current_tags = post['current_tags']

                # Check if it already has 10+ tags
                existing_count = len([t for t in current_tags.split(",") if t.strip()])
                if existing_count >= 10:
                    print(f"Skipping post {post_id} (already has {existing_count} tags)")
                    continue

                new_tags_str = generate_tags(title, current_tags)

                print(f"[{total_tagged+1}/{max_posts}] Tagging post {post_id}: {title}")

                try:
                    # Hover to make row actions visible
                    await page.hover(f"#post-{post_id}")
                    # Quick Edit
                    await page.click(f"#post-{post_id} .editinline")

                    # Wait for tags textarea
                    textarea_selector = f"#edit-{post_id} textarea[name='tax_input[post_tag]']"
                    await page.wait_for_selector(textarea_selector, timeout=5000)

                    # Fill and Save
                    await page.fill(textarea_selector, new_tags_str)
                    await page.click(f"#edit-{post_id} .save")

                    # Wait for the row to stop being 'updating'
                    await asyncio.sleep(2)
                    total_tagged += 1
                except Exception as e:
                    print(f"Error tagging post {post_id}: {e}")
                    try:
                        await page.click(f"#edit-{post_id} .cancel")
                    except:
                        pass

            current_page += 1

        print(f"Batch completed. Total posts tagged: {total_tagged}")
        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WordPress Auto-Tagger")
    parser.add_argument("--max", type=int, default=20, help="Maximum posts to tag")
    parser.add_argument("--page", type=int, default=1, help="Start page in admin list")
    args = parser.parse_args()

    asyncio.run(run_tagger(max_posts=args.max, start_page=args.page))
