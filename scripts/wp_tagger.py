import os
import time
import re
from playwright.sync_api import sync_playwright

# Configuration
WP_LOGIN_URL = "https://juanmoisesdelaserna.es/wp-login.php"
WP_USER = os.environ.get("WP_USER", "DoctorenPsicologia")
WP_PASS = os.environ.get("WP_PASS", "dp&LVjv3Y%Vbn!C5pu)w)4")

STOP_WORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", "con", "no", "una", "su", "al", "lo", "como", "más", "pero", "sus", "le", "ya", "o", "este", "sí", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre", "también", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mí", "antes", "algunos", "qué", "unos", "yo", "otro", "otras", "otra", "él", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual", "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros", "mi", "mis", "tú", "te", "ti"
}

def generate_tags(title):
    # Clean title: remove non-alphanumeric characters except spaces
    clean_title = re.sub(r'[^\w\s]', '', title.lower())
    words = clean_title.split()
    # Filter out stop words and short words
    keywords = [w for w in words if w not in STOP_WORDS and len(w) > 3]
    # Add some variants or common themes if known (e.g., psychology)
    tags = list(set(keywords))

    # If we don't have 10 tags, we can split some compound words or add generic ones
    if len(tags) < 10:
        generic_tags = ["psicología", "salud mental", "bienestar", "terapia", "análisis", "investigación", "comportamiento", "mente", "cerebro", "emociones"]
        for gt in generic_tags:
            if gt not in tags:
                tags.append(gt)
            if len(tags) >= 12:
                break

    return ", ".join(tags[:15])

def run_tagger(limit=50):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"Logging in to {WP_LOGIN_URL}...")
        page.goto(WP_LOGIN_URL)
        page.fill("#user_login", WP_USER)
        page.fill("#user_pass", WP_PASS)
        page.click("#wp-submit")
        page.wait_for_load_state("networkidle")

        if "wp-admin" not in page.url:
            print("Login failed. Check credentials.")
            return

        print("Login successful. Going to Posts...")
        page.goto("https://juanmoisesdelaserna.es/wp-admin/edit.php")

        count = 0
        while count < limit:
            # Find all rows that don't have many tags or haven't been processed
            # We'll just iterate through the current page
            rows = page.query_selector_all("tr.type-post")

            for row in rows:
                if count >= limit:
                    break

                post_id = row.get_attribute("id")
                title_el = row.query_selector(".row-title")
                if not title_el:
                    continue

                title = title_el.inner_text()
                tags_el = row.query_selector(".column-tags")
                existing_tags = tags_el.inner_text().strip()

                # If tags are few (e.g. "—" or less than 5 tags), we process it
                if existing_tags == "—" or existing_tags.count(",") < 8:
                    print(f"[{count+1}] Tagging: {title}")

                    # Hover to reveal Quick Edit
                    row.hover()
                    quick_edit = row.query_selector(".editinline")
                    if quick_edit:
                        quick_edit.click()

                        # Wait for inline edit row to appear
                        inline_edit_id = post_id.replace("post-", "edit-")
                        inline_row = page.wait_for_selector(f"#{inline_edit_id}")

                        tags_input = inline_row.query_selector("textarea.tax_input_post_tag")
                        if tags_input:
                            new_tags = generate_tags(title)
                            current_val = tags_input.input_value()
                            if current_val and current_val != "—":
                                combined_tags = current_val + ", " + new_tags
                            else:
                                combined_tags = new_tags

                            tags_input.fill(combined_tags)

                            # Click Update
                            save_button = inline_row.query_selector(".save")
                            save_button.click()

                            # Wait for it to disappear
                            page.wait_for_selector(f"#{inline_edit_id}", state="hidden")
                            time.sleep(1) # Small delay to be safe
                            count += 1
                        else:
                            # Cancel
                            cancel_button = inline_row.query_selector(".cancel")
                            cancel_button.click()
                else:
                    # print(f"Skipping (already tagged): {title}")
                    pass

            # Go to next page if limit not reached
            next_page = page.query_selector("a.next-page")
            if next_page and count < limit:
                print("Going to next page...")
                next_page.click()
                page.wait_for_load_state("networkidle")
            else:
                break

        print(f"Finished. Tagged {count} posts.")
        browser.close()

if __name__ == "__main__":
    run_tagger(limit=50) # Small batch for demonstration
