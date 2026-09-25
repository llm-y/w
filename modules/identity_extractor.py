import os
import certifi
import requests
from bs4 import BeautifulSoup
import re

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
}

def analyze_web_matches(vision_data):
    """
    Mengekstrak kemungkinan nama orang, judul halaman, dan identitas profil
    dari hasil Web Detection Google Vision.
    """
    names_detected = []
    social_profiles = []
    related_pages = []

    # 1. Best Guess Labels (Tebakan nama/entitas terbaik dari Google Vision)
    raw = vision_data.get('raw', {})
    web_det = raw.get('webDetection', {})
    
    best_guesses = web_det.get('bestGuessLabels', [])
    for bg in best_guesses:
        label = bg.get('label')
        if label and label.lower() not in ['person', 'human', 'face', 'photography', 'portrait']:
            names_detected.append(label)

    # 2. Web Entities (Nama publik, aktor, tokoh publik, akun)
    web_entities = web_det.get('webEntities', [])
    for ent in web_entities:
        desc = ent.get('description')
        score = ent.get('score', 0)
        if desc and desc.lower() not in ['face', 'image', 'person', 'photography', 'head', 'hair']:
            names_detected.append(f"{desc} (Keyakinan: {score*100:.0f}%)" if score > 0 else desc)

    # 3. Pages with matching images (Halaman media sosial / web berita)
    pages = vision_data.get('pages_with_matching_images', [])
    for p in pages:
        url = p.get('url', '')
        title = p.get('title', '')
        domain = re.sub(r'https?://(www\.)?', '', url).split('/')[0]

        is_social = any(soc in url.lower() for soc in [
            'instagram.com', 'linkedin.com', 'facebook.com', 'twitter.com', 'x.com',
            'tiktok.com', 'youtube.com', 'wikipedia.org', 'github.com', 'pinterest.com'
        ])

        item = {
            'domain': domain,
            'title': title or domain,
            'url': url,
            'is_social': is_social
        }

        if is_social:
            social_profiles.append(item)
        else:
            related_pages.append(item)

    return {
        'candidate_names': list(dict.fromkeys(names_detected)),
        'social_profiles': social_profiles,
        'related_pages': related_pages
    }
