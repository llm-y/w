import os
import certifi
import requests

def search_google_vision(image_input, max_results=15, creds_file=None):
    """
    Melakukan Web Detection melalui Google Cloud Vision API seperti pada GReverse.
    Mencari:
    - pages_with_matching_images
    - full_matching_images
    - partial_matching_images
    - visually_similar_images
    """
    try:
        from google.cloud import vision_v1
        from google.cloud.vision_v1 import types
        from google.protobuf.json_format import MessageToDict
    except ImportError:
        raise ImportError(
            "Pustaka 'google-cloud-vision' belum terpasang.\n"
            "Silakan pasang dengan menjalankan: pip install google-cloud-vision"
        )

    if creds_file and os.path.exists(creds_file):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(creds_file)

    if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
        raise ValueError(
            "Kredensial Google Cloud Vision belum disetel.\n"
            "Atur environment variable GOOGLE_APPLICATION_CREDENTIALS=<path/to/key.json>\n"
            "atau masukkan argumen --creds <path/to/key.json>"
        )

    client = vision_v1.ImageAnnotatorClient()

    # Load image content
    if image_input.startswith(('http://', 'https://')):
        resp = requests.get(image_input, headers={'User-Agent': 'Mozilla/5.0'}, verify=certifi.where())
        image = types.Image(content=resp.content)
    else:
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"File gambar tidak ditemukan: {image_input}")
        with open(image_input, 'rb') as f:
            content = f.read()
        image = types.Image(content=content)

    results = {
        "pages_with_matching_images": [],
        "full_matching_images": [],
        "partial_matching_images": [],
        "visually_similar_images": [],
        "raw": None
    }

    request = vision_v1.AnnotateImageRequest(
        image=image,
        features=[
            vision_v1.Feature(
                type_=vision_v1.Feature.Type.WEB_DETECTION,
                max_results=max_results
            )
        ]
    )

    response = client.annotate_image(request)
    if response.error.message:
        raise RuntimeError(f"Google Vision API Error: {response.error.message}")

    web_detection = response.web_detection

    for page in web_detection.pages_with_matching_images:
        results["pages_with_matching_images"].append({
            "url": page.url,
            "title": page.page_title
        })

    for img in web_detection.full_matching_images:
        results["full_matching_images"].append(img.url)

    for img in web_detection.partial_matching_images:
        results["partial_matching_images"].append(img.url)

    for img in web_detection.visually_similar_images:
        results["visually_similar_images"].append(img.url)

    results["raw"] = MessageToDict(response._pb)
    return results

def extract_all_image_urls(vision_results):
    """Mengekstrak seluruh tautan gambar langsung dari hasil Google Vision."""
    urls = []
    for key in ['full_matching_images', 'partial_matching_images', 'visually_similar_images']:
        for item in vision_results.get(key, []):
            if isinstance(item, str):
                urls.append(item)
            elif isinstance(item, dict) and 'url' in item:
                urls.append(item['url'])
    return list(dict.fromkeys(urls))
