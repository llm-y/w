#!/usr/bin/env python3
"""
    WHO? (w.py) - Automated OSINT Face Identity Finder
    Mengotomatisasi pencarian identitas dari foto menggunakan Playwright & InsightFace.
"""
import os
import sys
import certifi
import warnings

# Konfigurasi terminal Windows untuk UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

warnings.filterwarnings("ignore")
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from face_engine import FaceEngine
from modules.automated_search import search_identity_automated

def clean_path(path_str):
    if not path_str:
        return ""
    return path_str.strip().strip('"').strip("'").strip('& ')

def main():
    if len(sys.argv) > 1:
        photo_path = clean_path(sys.argv[1])
    else:
        print("\n" + "=" * 64)
        print("          WHO? (w.py) - PENCARIAN IDENTITAS WAJAH OTOMATIS      ")
        print("=" * 64)
        photo_input = input("\nTarik dan lepas (drag & drop) foto ke sini lalu tekan Enter:\n> ")
        photo_path = clean_path(photo_input)

    if not photo_path or not os.path.exists(photo_path):
        print(f"\n[!] Error: File foto tidak ditemukan: '{photo_path}'")
        return

    print("\n" + "=" * 64)
    print("           WHO? (w.py) - MEMPROSES IDENTIFIKASI WAJAH           ")
    print("=" * 64)
    print(f"File Foto: {os.path.abspath(photo_path)}")
    print("-" * 64)

    # 1. Inisialisasi Engine Wajah
    print("[*] Menganalisis biometrik wajah (InsightFace)...")
    engine = FaceEngine()

    # 2. Otomatisasi Pencarian Web & Ekstraksi Data via Playwright
    print("[*] Menjalankan pencarian web & ekstraksi identitas secara otomatis...")
    data, face_info = search_identity_automated(photo_path, engine, headless=False)

    print("\n" + "=" * 64)
    print("                    HASIL IDENTIFIKASI WAJAH                    ")
    print("=" * 64)

    # Info Biometrik
    if face_info:
        print("[+] BIOMETRIK WAJAH:")
        print(f"    - Kualitas Deteksi: {face_info.get('confidence', 0)*100:.1f}%")
        print(f"    - Posisi Wajah    : {face_info.get('box')}")
    else:
        print("[!] Catatan: Wajah manusia spesifik tidak terdeteksi tajam, mencari seluruh gambar.")

    # Ringkasan Deskripsi AI
    if data.get('summary'):
        print(f"\n[+] DESKRIPSI VISUAL:\n    {data['summary']}")

    # Profil Media Sosial
    if data['social_profiles']:
        print(f"\n[+] PROFIL MEDIA SOSIAL & AKUN DITEMUKAN ({len(data['social_profiles'])}):")
        for i, item in enumerate(data['social_profiles'][:8], 1):
            print(f"    {i}. {item['title']}")
            print(f"       -> {item['url']}")

    # Instansi, Kampus, Arsip Publik & Berita
    if data['public_records']:
        print(f"\n[+] ARSIP PUBLIK, KAMPUS & INSTANSI DITEMUKAN ({len(data['public_records'])}):")
        for i, item in enumerate(data['public_records'][:8], 1):
            print(f"    {i}. {item['title']}")
            print(f"       -> {item['url']}")

    # Hasil Web Lainnya
    if data['general_matches']:
        print(f"\n[+] KECOCOKAN WEB LAINNYA ({len(data['general_matches'])}):")
        for i, item in enumerate(data['general_matches'][:5], 1):
            print(f"    {i}. {item['title']}")
            print(f"       -> {item['url']}")

    total = len(data['all_links'])
    print("\n" + "-" * 64)
    print(f"Total {total} sumber kecocokan visual ditemukan di internet.")
    print("=" * 64 + "\n")

if __name__ == "__main__":
    main()
