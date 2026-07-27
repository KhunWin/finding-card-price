import requests
import time
import json

# Create a session with a clearly identifiable User-Agent
session = requests.Session()
session.headers.update({
    'User-Agent': 'YourApplication/1.0'
})

category_id = '27'  # 1=Pokemon, 3=YuGiOh, 4=Magic: The Gathering, 7=Epic
output_file = 'tcg_data.json'

# Get all groups
print("Fetching groups...")
r = session.get(f"https://tcgcsv.com/tcgplayer/{category_id}/groups")
all_groups = r.json()['results']

all_data = []

# Process each group
for group in all_groups:
    group_id = group['groupId']
    group_name = group['name']
    print(f"Processing group: {group_name} (ID: {group_id})")
    
    # Get products for this group
    r = session.get(f"https://tcgcsv.com/tcgplayer/{category_id}/{group_id}/products")
    products = r.json()['results']
    
    # Get prices for this group
    r = session.get(f"https://tcgcsv.com/tcgplayer/{category_id}/{group_id}/prices")
    prices = r.json()['results']
    
    # Create a dictionary to store product data with prices
    product_data = {}
    
    # First, add all products to the dictionary
    for product in products:
        product_data[product['productId']] = {
            'productId': product['productId'],
            'name': product['name'],
            'cleanName': product.get('cleanName', ''),
            'imageUrl': product.get('imageUrl', ''),
            'categoryId': product.get('categoryId'),
            'groupId': product.get('groupId'),
            'url': product.get('url', ''),
            'modifiedOn': product.get('modifiedOn', ''),
            'imageCount': product.get('imageCount', 0),
            'presaleInfo': product.get('presaleInfo', {}),
            'extendedData': product.get('extendedData', []),
            'prices': []  # Will be filled with price data
        }
    
    # Then, add the price information to the corresponding product
    for price in prices:
        product_id = price['productId']
        if product_id in product_data:
            product_data[product_id]['prices'].append({
                'lowPrice': price.get('lowPrice'),
                'midPrice': price.get('midPrice'),
                'highPrice': price.get('highPrice'),
                'marketPrice': price.get('marketPrice'),
                'directLowPrice': price.get('directLowPrice'),
                'subTypeName': price.get('subTypeName', '')
            })
    
    # Convert dictionary to list and add to all_data
    group_data = {
        'group': group,
        'products': list(product_data.values())
    }
    all_data.append(group_data)
    
    # Respect rate limits - wait 0.25 seconds between requests
    time.sleep(0.25)
    # break  # Remove this line to process all groups

# Save to JSON file with pretty formatting
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f"Data saved to {output_file}")
print(f"Processed {len(all_data)} groups")

# Print summary
total_products = sum(len(group['products']) for group in all_data)
print(f"Total products: {total_products}")