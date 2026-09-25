import os
import certifi
import requests
from urllib.parse import unquote, urlsplit
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def sanitize_filename(name):
    # Bersihkan karakter terlarang di Windows
    invalid_chars = '<>:"/\\|?*'
    for c in invalid_chars:
        name = name.replace(c, '_')
    return name.strip()

def download_single_image(image_url, output_dir, timeout=12):
    """
    Mengunduh satu gambar dari URL dengan SSL certifi bypass/support dan error handling.
    Mengembalikan path file lokal jika berhasil, None jika gagal.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        parsed = urlsplit(image_url)
        raw_name = os.path.basename(unquote(parsed.path))
        if not raw_name or '.' not in raw_name:
            raw_name = f"image_{abs(hash(image_url)) % 1000000}.jpg"

        clean_name = sanitize_filename(raw_name)
        if len(clean_name) > 60:
            ext = os.path.splitext(clean_name)[1] or '.jpg'
            clean_name = f"img_{abs(hash(image_url)) % 10000000}{ext}"

        file_path = os.path.join(output_dir, clean_name)

        # Jika sudah ada, tambahkan suffix
        base, ext = os.path.splitext(clean_name)
        counter = 1
        while os.path.exists(file_path):
            # Cek ukuran file, jika valid (> 1KB) kita anggap sudah diunduh
            if os.path.getsize(file_path) > 1024:
                return file_path
            file_path = os.path.join(output_dir, f"{base}_{counter}{ext}")
            counter += 1

        response = requests.get(
            image_url,
            headers=DEFAULT_HEADERS,
            verify=certifi.where(),
            timeout=timeout,
            stream=True
        )

        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Validasi ukuran gambar minimal 1KB
            if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                return file_path
            else:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return None
        return None
    except Exception:
        return None

def download_images_batch(image_urls, output_dir, max_workers=5):
    """
    Mengunduh sekumpulan URL gambar secara paralel dengan indikator progress.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    unique_urls = list(dict.fromkeys(image_urls))
    results = {}

    print(f"\n[INFO] Mengunduh {len(unique_urls)} gambar ke: {output_dir}")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_single_image, url, output_dir): url
            for url in unique_urls
        }
        with tqdm(total=len(unique_urls), desc="Mengunduh Gambar", unit="img") as pbar:
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    local_path = future.result()
                    if local_path:
                        results[url] = local_path
                except Exception:
                    pass
                pbar.update(1)

    print(f"[OK] Berhasil mengunduh {len(results)} dari {len(unique_urls)} gambar.\n")
    return results
