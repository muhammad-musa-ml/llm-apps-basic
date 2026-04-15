from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
from collections import deque
from tqdm import tqdm


# Standard headers to fetch a website
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)


def fetch_website_links(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]


def fetch_all_website_links(start_url, timeout=10):
    visited_pages = set()
    found_links = set()
    pages_to_visit = deque([start_url])
    start_domain = urlparse(start_url).netloc
    with tqdm(total=1, desc="Crawling pages", unit=" pages") as pbar:

        while pages_to_visit:
            current_url = pages_to_visit.popleft()
            if current_url in visited_pages:
                continue
            visited_pages.add(current_url)
            try:
                response = requests.get(current_url, headers=headers, timeout=timeout)
                response.raise_for_status()
            except requests.RequestException:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup.find_all("a", href=True):
                href = tag["href"].strip()
                if not href:
                    continue
                full_url = urljoin(current_url, href)
                parsed = urlparse(full_url)

                # Keep only http/https links
                if parsed.scheme not in ("http", "https"):
                    continue

                # Removing fragment so same page#section isn't treated as different
                clean_url = parsed._replace(fragment="").geturl()

                found_links.add(clean_url)

                # Crawl only pages on the same domain
                if parsed.netloc == start_domain and clean_url not in visited_pages:
                    pages_to_visit.append(clean_url)
            
            pbar.update(1)

            if len(found_links) >= 100:
                break


    return sorted(found_links)
    
