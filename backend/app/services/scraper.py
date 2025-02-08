import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import queue
import json
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/",
}

# File to store the visited URLs
VISITED_URLS_FILE = "visited_urls.json"

def load_visited_urls():
    """Load the set of visited URLs from a JSON file."""
    if os.path.exists(VISITED_URLS_FILE):
        with open(VISITED_URLS_FILE, "r") as f:
            try:
                # JSON stores lists so we convert to a set
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_visited_urls(visited_urls):
    """Save the set of visited URLs to a JSON file."""
    with open(VISITED_URLS_FILE, "w") as f:
        json.dump(list(visited_urls), f, indent=2)

def crawl_website(starting_url, call_limit=200):
    # Load any previously visited URLs
    visited_urls = load_visited_urls()  # Persisted set from previous runs
    urls_to_crawl = queue.Queue()        # Thread-safe FIFO queue for URLs to crawl
    urls_to_crawl_set = set()             # Set to ensure no duplicates in the queue
    call_count = 0

    # Add the starting URL to the queue and the set if not already visited
    if starting_url not in visited_urls:
        urls_to_crawl.put(starting_url)
        urls_to_crawl_set.add(starting_url)

    while not urls_to_crawl.empty() and call_count < call_limit:
        # Get the next URL to crawl from the queue
        current_url = urls_to_crawl.get()

        # Skip URLs that have already been processed
        if current_url in visited_urls:
            continue

        # Mark the URL as visited
        visited_urls.add(current_url)
        call_count += 1
        print(f"Added: {current_url} to dataset! (Call #{call_count})")
        
        # Print queue size every second call
        if call_count % 2 != 0:
            print(f"Queue size: {urls_to_crawl.qsize()}")

        # Optionally, save progress every 10 calls to persist state in case of interruption
        if call_count % 10 == 0:
            save_visited_urls(visited_urls)
            print("Progress saved to visited_urls.json")

        # Optionally, save a snapshot of the current queue set at a specific call count
        if call_count == 99:
            with open("queue_snapshot.txt", "w") as f:
                f.write("\n".join(urls_to_crawl_set))
            print("Saved queue to queue_snapshot.txt")

        try:
            # Send a GET request to the specified URL
            response = requests.get(current_url, headers=HEADERS)
            
            # Check if the request was successful
            if response.status_code != 200:
                print(f"Status: {response.status_code}")
                continue
            
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extract all text from the page (for later use in your Neo4j node, etc.)
            text = soup.get_text()
            cleaned_text = text.encode('utf-8', errors='ignore').decode('utf-8')
            # Here you can add the logic to store 'cleaned_text' in your Neo4j database

            # Sleep between calls
            sleep_time = 1
            print(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)

            # Get all links on the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                
                # Ensure we're still in the same domain
                if urlparse(full_url).netloc == urlparse(current_url).netloc:
                    exclude_patterns = (
                        r'cytoverse|\.jpg|\.png|\.jpeg|\.svg|\.gif|\.webp|&oldid|action=info|https?:\/\/[^\s#]+#[^\s]+',
                        r'&mobileaction=toggle_view_mobile|\?action=history|Brandon_Sanderson|cite_ref',
                        r'#cite_note|edit|wiki/Help|/wiki/Special:.*|/w/|/mw/|Root|/wiki/Coppermind:.*',
                        r'Previously_reviewed_articles|Statistical_analysis|Alcatraz|The_Wheel_of_Time|Dark_One|Infinity_Blade',
                        r'Firstborn|I_Hate_Dragons|The_Reckoners|Legion|Skyward|Stephen_Leeds:_Death_%26_Faxes|The_Gathering_Storm',
                        r'Towers_of_Midnight|A_Memory_of_Light|River_of_Souls|Heuristic_Algorithm_and_Reasoning_Response_Engine',
                        r'The_Rithmatist|Dreamer|Perfect_State|Snapshot|Children_of_the_Nameless|The_Original|Starsight|Cytonic',
                        r'Defiant_(book)|Defending_Elysium|Sunreach|ReDawn_(novella)|Evershore_(novella)|Hyperthief|Steelheart',
                        r'Firefight|Calamity|Lux_(book)|The_Scrivener%27s_Bones|The_Knights_of_Crystallia|The_Shattered_Lens',
                        r'The_Dark_Talent|Bastille_Versus_the_Evil_Librarians|Bibliography|Sample_material|Unpublished_works',
                        r'Media_rights|Category:People|User:|User_talk:|Kelley_Harris'
                    )

                    if re.search('|'.join(exclude_patterns), full_url, re.IGNORECASE):
                        continue  # Skip this URL

                    # Add the link to the queue if it hasn't been visited or queued already
                    if full_url not in visited_urls and full_url not in urls_to_crawl_set:
                        urls_to_crawl.put(full_url)
                        urls_to_crawl_set.add(full_url)
        
        except Exception as e:
            print(f"An error occurred while crawling {current_url}: {e}")

    # Save the final visited URLs set at the end of the crawl
    save_visited_urls(visited_urls)
    print(f"Crawled {len(visited_urls)} URLs. Final state saved to {VISITED_URLS_FILE}.")

# Example usage:
# starting_url = 'https://coppermind.net/wiki/Category:Stormlight_Archive'
# crawl_website(starting_url)
