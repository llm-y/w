import os
import re
import certifi
import requests
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,id;q=0.8'
}

def generate_reverse_search_links(image_path_or_url):
    """Menghasilkan tautan langsung ke mesin pencari reverse image web populer."""
    links = {}
    if image_path_or_url.startswith(('http://', 'https://')):
        encoded_url = quote_plus(image_path_or_url)
        links['Google Lens'] = f"https://lens.google.com/uploadbyurl?url={encoded_url}"
        links['Yandex Images'] = f"https://yandex.com/images/search?rpt=imageview&url={encoded_url}"
        links['Bing Visual Search'] = f"https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl={encoded_url}"
    else:
        links['Google Lens Upload'] = "https://images.google.com/"
        links['Yandex Images Upload'] = "https://yandex.com/images/"
        links['FaceCheck ID'] = "https://facecheck.id/"
    return links

def search_web_images_by_query(query, max_results=20):
    """
    Mencari tautan gambar dari web menggunakan query (nama orang / entitas)
    sebagai kandidat verifikasi wajah tanpa memerlukan API key berbayar.
    Menggunakan Bing Image Search parser.
    """
    image_urls = []
    try:
        search_url = f"https://www.bing.com/images/search?q={quote_plus(query)}&form=HDRSC2&first=1"
        resp = requests.get(search_url, headers=DEFAULT_HEADERS, verify=certifi.where(), timeout=12)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Temukan elemen 'm' yang berisi JSON data gambar
            for a in soup.find_all('a', class_='iusc'):
                m_data = a.get('m')
                if m_data:
                    match = re.search(r'"murl":"(http[^"]+)"', m_data)
                    if match:
                        img_url = match.group(1)
                        if img_url not in image_urls:
                            image_urls.append(img_url)
                if len(image_urls) >= max_results:
                    break
    except Exception as e:
        print(f"[Warning] Gagal melakukan pencarian gambar via web: {e}")

    return image_urls[:max_results]
