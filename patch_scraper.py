"""One-shot patch: add 1 s delay before every yuyu-tei.jp HTTP request."""
path = r'c:\Users\Win Khun Myint\Desktop\card-scrap\yuyu_tei\scarp_yuyu_v4.py'

with open(path, encoding='utf-8') as f:
    content = f.read()

orig = content  # keep for diff check

# 1. Before search-page fetch
content = content.replace(
    '        logger.info(f"Fetching search results for group: {group_code} with ws: {ws}")\n'
    '        response = self.session.get(search_url, params=params)',
    '        logger.info(f"Fetching search results for group: {group_code} with ws: {ws}")\n'
    '        time.sleep(self.delay)\n'
    '        response = self.session.get(search_url, params=params)',
)

# 2. Before card-detail fetch
content = content.replace(
    '            logger.info(f"Fetching card detail: {url}")\n'
    '            response = self.session.get(url)',
    '            logger.info(f"Fetching card detail: {url}")\n'
    '            time.sleep(self.delay)\n'
    '            response = self.session.get(url)',
)

# 3. Before image-download fetch
content = content.replace(
    '            logger.info(f"Downloading image: {image_url}")\n'
    '            response = self.session.get(image_url, timeout=30)',
    '            logger.info(f"Downloading image: {image_url}")\n'
    '            time.sleep(self.delay)\n'
    '            response = self.session.get(image_url, timeout=30)',
)

# 4. Remove the old end-of-loop redundant sleep block
content = content.replace(
    '            # Respectful delay\n'
    '            if i < len(pending_links):\n'
    '                time.sleep(self.delay)\n',
    '',
)

assert content != orig, "No changes made – check search strings"

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied successfully.")
