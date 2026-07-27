import requests
import time
import json

session = requests.Session()
session.headers.update({
    'User-Agent': 'YourApplication/1.0'
})

category_id = '4'  # Pokemon
all_data = []

# Get all groups
r = session.get(f"https://tcgcsv.com/tcgplayer/{category_id}/groups")
all_groups = r.json()['results']

for group in all_groups:
    group_id = group['groupId']
    print(f"Processing group: {group['name']}")
    
    # Get products
    r = session.get(f"https://tcgcsv.com/tcgplayer/{category_id}/{group_id}/products")
    products = r.json()['results']
    
    # Get prices
    r = session.get(f"https://tcgcsv.com/tcgplayer/{category_id}/{group_id}/prices")
    prices = r.json()['results']
    
    all_data.append({
        'group': group,
        'products': products,
        'prices': prices
    })
    
    time.sleep(0.25)
    # break  # Remove this line to process all groups

# Save to JSON file
with open('tcg_data.json', 'w') as f:
    json.dump(all_data, f, indent=2)

print(f"Data saved to tcg_data.json")