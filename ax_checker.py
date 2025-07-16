import requests
from bs4 import BeautifulSoup
import time
import os
import json
from urllib.parse import urljoin

# --- CONFIGURATION ---
URL = "https://store.epic.leapevent.tech/anime-expo/2025"

NTFY_TOPIC = os.getenv('NTFY_TOPIC')
if not NTFY_TOPIC:
    raise ValueError("The NTFY_TOPIC environment variable is not set.")

CHECK_INTERVAL_SECONDS = 600 
# Using a new file to accommodate the new data structure (with image URLs)
KNOWN_GUESTS_FILE = "known_guests.json" 
# --- END CONFIGURATION ---

def send_notification(title, page_url, image_url):
    """Sends a push notification with a clickable link and an attached image."""
    headers = {
        "Title": title.encode('utf-8'),
        "Tags": "tada,photo",
        "Click": page_url,
        # The Attach header tells ntfy to fetch the URL and attach it as an image
        "Attach": image_url.encode('utf-8')
    }
    try:
        # The body of the message will be the guest's page URL
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=page_url.encode('utf-8'),
            headers=headers
        )
        print(f"  -> Notification sent for: {title}")
    except Exception as e:
        print(f"  -> ERROR: Failed to send notification: {e}")

def load_known_guests():
    """Loads the dictionary of known guests from a JSON file."""
    if not os.path.exists(KNOWN_GUESTS_FILE):
        return {}
    try:
        with open(KNOWN_GUESTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_known_guests(guests_dict):
    """Saves the current dictionary of guests to a JSON file."""
    with open(KNOWN_GUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(guests_dict, f, indent=4)

def get_current_guests():
    """Fetches static HTML and extracts guest name, page URL, and image URL."""
    print(f"Fetching static HTML from {URL}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: Could not fetch the webpage: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    product_container = soup.find('div', id='productContainer')
    if not product_container:
        print("WARNING: Could not find the 'productContainer' div.")
        return {}

    guest_cards = product_container.select('div.ProductCard')
    print(f"Searching for guests within 'div.ProductCard' elements...")
    
    if not guest_cards:
        print("WARNING: Found 'productContainer' but no 'ProductCard' divs inside.")
        return {}
        
    # The dictionary will now store a nested dictionary for each guest
    guests = {} # {page_url: {'name': name, 'image_url': image_url}}
    for card in guest_cards:
        name_element = card.select_one('h2.ProductTitle')
        link_element = card.select_one('div.card-footer a')
        image_element = card.select_one('img.card-img-top') # <-- Extract the image tag

        if name_element and link_element and image_element and link_element.get('href'):
            guest_name = name_element.get('title', '').strip()
            relative_url = link_element['href']
            page_url = urljoin(URL, relative_url)
            image_url = urljoin(URL, image_element.get('src')) # <-- Get image URL

            if guest_name and page_url and image_url:
                 guests[page_url] = {
                     'name': guest_name,
                     'image_url': image_url
                 }
        else:
            print("WARNING: A ProductCard was found but was missing a name, link, or image. Skipping.")
            
    print(f"Found {len(guests)} guests from static HTML.")
    return guests

def main():
    """The main loop to periodically check for new guests."""
    print("--- Anime Expo Guest Checker (with Images) ---")
    print(f"Monitoring for 'div.ProductCard' elements.")
    print(f"Checking every {CHECK_INTERVAL_SECONDS / 60} minutes.")
    print("--------------------------------")
    
    known_guests = load_known_guests()
    if known_guests:
        print(f"Loaded {len(known_guests)} known guests from {KNOWN_GUESTS_FILE}.")
    else:
        print("No known guests file found. Will create one on first run.")

    while True:
        current_guests = get_current_guests()

        if current_guests is not None:
            # First run populates the baseline
            if not known_guests and current_guests:
                print("First run. Populating initial guest list.")
                save_known_guests(current_guests)
                known_guests = current_guests
            else:
                # Compare the page URLs (the keys) to find new guests
                new_guest_urls = current_guests.keys() - known_guests.keys()

                if new_guest_urls:
                    print("\n!!! NEW GUEST(S) FOUND !!!")
                    for page_url in new_guest_urls:
                        # Get the data for the new guest
                        guest_data = current_guests[page_url]
                        guest_name = guest_data['name']
                        guest_image_url = guest_data['image_url']
                        
                        title = f"New AX Guest: {guest_name}"
                        send_notification(title, page_url, guest_image_url)
                    
                    # Update the list of known guests
                    save_known_guests(current_guests)
                    known_guests = current_guests
                else:
                    print("No new guests found. All is quiet.")

        print("--------------------------------")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting script. Goodbye!")