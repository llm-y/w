"""
Konfigurasi Kredensial API untuk GReverse Plus
"""
import os

# Kredensial Google Custom Search (jika ingin digunakan)
googleCreds = {
    'devKey': os.environ.get('GOOGLE_DEV_KEY', ''),
    'imageSearchID': os.environ.get('GOOGLE_CSE_IMAGE_ID', ''),
    'querySearchID': os.environ.get('GOOGLE_CSE_QUERY_ID', '')
}

# Path ke file service account Google Cloud Vision JSON (opsional)
GOOGLE_VISION_KEY_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'api_creds/google_vision_key.json')
