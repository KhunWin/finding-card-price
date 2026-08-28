import re
import csv
import os
from pathlib import Path

def extract_cards_from_html(html_content):
    """
    Extract card codes and names from HTML content.
    Handles cases with or without brackets [CODE].
    Returns a list of tuples (card_name, card_code)
    """
    cards = []
    
    # Pattern 1: With brackets - [CODE] Name
    pattern_with_brackets = r'<label[^>]*>\s*\[([A-Za-z0-9\.]+)\]\s*([^<]+?)\s*</label>'
    matches_with_brackets = re.findall(pattern_with_brackets, html_content, re.DOTALL)
    
    for code, name in matches_with_brackets:
        name = ' '.join(name.split())  # Clean whitespace
        cards.append((name, code))
    
    # Pattern 2: Without brackets - just name (for items like marker cards)
    # But we need to find the value attribute from the input tag
    pattern_no_brackets = r'<input[^>]*value="([^"]+)"[^>]*>.*?<label[^>]*>\s*([^<]+?)\s*</label>'
    matches_no_brackets = re.findall(pattern_no_brackets, html_content, re.DOTALL)
    
    # Also handle the case where label spans multiple lines
    pattern_no_brackets_multiline = r'<input[^>]*value="([^"]+)"[^>]*>.*?<label[^>]*>\s*([\s\S]+?)\s*</label>'
    matches_no_brackets_multiline = re.findall(pattern_no_brackets_multiline, html_content, re.DOTALL)
    
    all_matches = matches_no_brackets + matches_no_brackets_multiline
    
    # Check if we already have these codes from the bracketed pattern
    existing_codes = {code for _, code in cards}
    
    for value, name in all_matches:
        # Clean name
        name = ' '.join(name.split())
        # Skip if this code was already found with brackets
        if value not in existing_codes:
            cards.append((name, value))
            existing_codes.add(value)
    
    return cards

def extract_cards_improved(html_content):
    """
    Improved extraction that handles all cases properly.
    Extracts from label text and input value together.
    """
    cards = []
    
    # Find all input-label pairs
    # Pattern matches the input tag and its following label
    pattern = r'<input[^>]*value="([^"]+)"[^>]*>.*?<label[^>]*>\s*([^<]+?)\s*</label>'
    matches = re.findall(pattern, html_content, re.DOTALL)
    
    for value, label_text in matches:
        label_text = ' '.join(label_text.split())
        
        # Check if the label already has a bracketed code
        bracketed_match = re.match(r'\[([A-Za-z0-9\.]+)\]\s*(.+)', label_text)
        if bracketed_match:
            # If it has brackets, use that code
            code = bracketed_match.group(1)
            name = bracketed_match.group(2).strip()
        else:
            # If no brackets, use the input value as code
            code = value
            name = label_text
        
        cards.append((name, code))
    
    # Remove duplicates by code
    seen = set()
    unique_cards = []
    for name, code in cards:
        if code not in seen:
            seen.add(code)
            unique_cards.append((name, code))
    
    return unique_cards

def save_to_csv(cards, filename='cards.csv', format_type='display'):
    """
    Save cards to CSV file.
    format_type: 'display' -> [CODE] Name, CODE
                 'simple' -> Name, CODE
    """
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Display Name', 'Card Code'])
        
        for name, code in cards:
            if format_type == 'display':
                writer.writerow([f'[{code}] {name}', code])
            else:
                writer.writerow([name, code])

def read_html_file(filepath):
    """Read HTML content from a file."""
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def process_html_file(input_file, output_file='cards.csv', format_type='display'):
    """
    Main function to process an HTML file and extract cards to CSV.
    """
    print(f"Processing: {input_file}")
    
    # Read the HTML content
    html_content = read_html_file(input_file)
    
    # Extract cards
    cards = extract_cards_improved(html_content)
    
    if not cards:
        print("No cards found in the file.")
        return []
    
    # Save to CSV
    save_to_csv(cards, output_file, format_type)
    
    # Print results
    print(f"Total cards extracted: {len(cards)}")
    print(f"Saved to: {output_file}")
    
    # Display first few cards
    print("\nFirst 5 cards:")
    for i, (name, code) in enumerate(cards[:5]):
        print(f"  [{code}] {name}")
    if len(cards) > 5:
        print(f"  ... and {len(cards) - 5} more")
    
    return cards

def main():
    """Main execution function."""
    # Get input file from user or use default
    input_file = 'vg.txt'  # Default
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"File '{input_file}' not found.")
        # Try to find any .txt or .html file
        possible_files = list(Path('.').glob('*.txt')) + list(Path('.').glob('*.html'))
        if possible_files:
            input_file = str(possible_files[0])
            print(f"Using: {input_file}")
        else:
            print("No input files found.")
            return
    
    # Process the file
    cards = process_html_file(
        input_file=input_file,
        output_file='extracted_cards.csv',
        format_type='display'
    )
    
    # Also save a simple version without brackets
    if cards:
        save_to_csv(cards, 'extracted_cards_simple.csv', format_type='simple')
        print(f"Also saved simple version to: extracted_cards_simple.csv")

if __name__ == "__main__":
    main()