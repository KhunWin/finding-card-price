# pip install firecrawl-py
from firecrawl import Firecrawl

app = Firecrawl(api_key="fc-4d11197b35a741c6905b15f84861d16f")

# Scrape a website:
result = app.scrape('https://www.cloudflare.com/learning/security/what-are-indicators-of-compromise/')
print(result)

# Extract HTML content
# html_content = result['html']

# Save to HTML file
# print("it's printing the html content")
# with open('scraped_page.html', 'w', encoding='utf-8') as f:
#     f.write(html_content)
# print("Scraped content saved to scraped_page.html")


# Connect via CLI
# npx -y firecrawl-cli@latest init --all -k fc-4d11197b35a741c6905b15f84861d16f