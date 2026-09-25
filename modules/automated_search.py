import os
import sys
import re
import cv2
from playwright.sync_api import sync_playwright

def crop_face_for_search(image_path, face_engine, output_dir=None):
    """
    Mendeteksi wajah utama dan memotongnya KETAT pada area wajah & kepala saja.
    Tidak menyertakan baju/jas/dasi agar Google Lens fokus 100% pada fitur biometrik
    wajah dan tidak salah fokus mencari katalog pakaian/baju.
    """
    if not output_dir:
        output_dir = os.path.dirname(os.path.abspath(image_path))

    faces = face_engine.extract_faces(image_path)
    if not faces:
        return image_path, None

    img = face_engine.load_image(image_path)
    h, w, _ = img.shape
    box = faces[0]['box']  # [x1, y1, x2, y2]

    bw = box[2] - box[0]
    bh = box[3] - box[1]

    # Margin sedikit di atas (rambut/kening) dan samping (telinga/pipi)
    # PENTING: Margin bawah DIBATASI tepat di dagu (tidak sampai ke baju/jas)
    margin_top = int(bh * 0.15)
    margin_side = int(bw * 0.10)

    x1 = max(0, box[0] - margin_side)
    y1 = max(0, box[1] - margin_top)
    x2 = min(w, box[2] + margin_side)
    y2 = min(h, box[3])  # Berhenti tepat di dagu!

    cropped = img[y1:y2, x1:x2]
    crop_filename = f"crop_face_{os.path.basename(image_path)}"
    crop_path = os.path.join(output_dir, crop_filename)
    cv2.imwrite(crop_path, cropped)
    return crop_path, faces[0]

def search_identity_automated(image_path, face_engine, headless=False):
    """
    Mengotomatisasi pencarian reverse visual Google Lens via Playwright.
    Otomatis upload foto, mengekstrak judul, identitas, profil medsos, dan link terkait.
    """
    crop_path, face_info = crop_face_for_search(image_path, face_engine)
    abs_photo = os.path.abspath(crop_path)

    profile_dir = os.path.abspath('./.browser_profile')
    os.makedirs(profile_dir, exist_ok=True)

    extracted_data = {
        'summary': None,
        'social_profiles': [],
        'public_records': [],
        'general_matches': [],
        'all_links': []
    }

    print("[*] Meluncurkan peramban otomatis (Playwright Chromium)...")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        page = context.new_page()

        try:
            print("[*] Mengakses Google Images...")
            page.goto('https://images.google.com/', timeout=25000)
            page.wait_for_timeout(1000)

            # Klik tombol kamera Lens
            lens_btn = page.locator('div[jsname="R5mgy"], [aria-label*="gambar"], [aria-label*="image"]').first
            if lens_btn.count() > 0:
                lens_btn.click()
                page.wait_for_timeout(1000)

            # Upload file foto
            file_input = page.locator('input[type="file"]')
            if file_input.count() > 0:
                print(f"[*] Mengunggah foto target secara otomatis: {os.path.basename(abs_photo)}...")
                file_input.set_input_files(abs_photo)
                print("[*] Menunggu analisis visual & identifikasi di web (sekitar 6 detik)...")
                page.wait_for_timeout(7000)

            # Ekstrak Ringkasan AI jika ada
            try:
                ai_texts = page.locator('div[data-attrid="wa:/description"], div.kno-rdesc').all_inner_texts()
                if ai_texts:
                    extracted_data['summary'] = ' '.join(ai_texts).strip()
            except Exception:
                pass

            # Ekstrak seluruh tautan hasil visual
            links_raw = page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a')).map(a => ({
                    href: a.href,
                    text: a.innerText.trim(),
                    aria: a.getAttribute('aria-label') || ''
                })).filter(x => x.href && !x.href.includes('google.com/search') && !x.href.includes('google.com/intl') && (x.text || x.aria));
            }''')

            seen_urls = set()
            for item in links_raw:
                href = item['href']
                text = (item['text'] or item['aria']).strip()
                lines = [l.strip() for l in text.splitlines() if l.strip()]
                clean_title = ' | '.join(lines[:2]) if lines else text

                # Filter link non-hasil pencarian (seperti bantuan/privasi google)
                if any(k in href.lower() for k in ['support.google.com', 'policies.google.com', 'google.co.id/intl', 'webhp']):
                    continue
                if any(k in clean_title.lower() for k in ['bantuan aksesibilitas', 'kebijakan privasi', 'aplikasi google', 'ke beranda']):
                    continue
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                record = {
                    'title': clean_title,
                    'url': href,
                    'source': lines[0] if lines else 'Web'
                }

                # Kategorisasi
                lower_title = clean_title.lower()
                is_social = any(soc in lower_title or soc in href.lower() for soc in [
                    'linkedin', 'facebook', 'instagram', 'twitter', 'x.com', 'tiktok', 'youtube', 'pinterest', 'lemon8'
                ])
                is_record = any(rec in lower_title for rec in [
                    'dinas', 'pemerintah', 'universitas', 'uin', 'politeknik', 'bkpsdm', 'caleg', 'kependudukan', 'jurnal', 'espos', 'detik', 'kompas'
                ])

                if is_social:
                    extracted_data['social_profiles'].append(record)
                elif is_record:
                    extracted_data['public_records'].append(record)
                else:
                    extracted_data['general_matches'].append(record)

                extracted_data['all_links'].append(record)

        except Exception as e:
            print(f"[!] Error selama otomasi: {e}")
        finally:
            context.close()

    # Bersihkan file crop sementara jika dibuat
    if crop_path != image_path and os.path.exists(crop_path):
        try:
            os.remove(crop_path)
        except Exception:
            pass

    return extracted_data, face_info
