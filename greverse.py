#!/usr/bin/env python3
"""
    GReverse Plus - Enhanced Face Identification & OSINT Reverse Search Tool
    Berdasarkan konsep GReverse (https://github.com/Th3Tr1ckst3r/GReverse)
    Dengan penyempurnaan:
    - Multi-Engine Face Recognition (InsightFace ArcFace 512-D / SFace / dlib)
    - Google Cloud Vision Web Detection support
    - Free Web Reverse Search & Query Candidate Collector
    - Local Face Database Scanner (pemindaian folder foto lokal)
    - Visual HTML Report & CSV/JSON Exporters
    - Interaktif Wizard mode
"""
import os
import sys
import certifi

# Fix SSL CA certificates for Windows Python
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import argparse
from face_engine import FaceEngine
from modules.downloader import download_images_batch, download_single_image
from modules.local_db_search import scan_local_directory
from modules.web_reverse import generate_reverse_search_links, search_web_images_by_query
from modules.reporter import (
    print_banner,
    print_results_table,
    save_json,
    save_csv,
    generate_html_report,
    get_color_tag
)

def run_interactive_mode():
    print_banner()
    print("Mode Interaktif Wizard:")
    print("1. Identifikasi Wajah di Database / Folder Foto Lokal")
    print("2. Cari & Verifikasi Wajah di Web via Nama / Query (Free Web Search)")
    print("3. Reverse Search via Google Cloud Vision API")
    print("4. Buka / Dapatkan Link Pencarian Web Reverse (Google Lens, Yandex, FaceCheck)")
    print("5. Keluar")
    
    choice = input("\nPilih opsi [1-5]: ").strip()
    if choice == "1":
        target = input("Masukkan path foto wajah target: ").strip().strip('"')
        db_dir = input("Masukkan path folder database foto yang ingin dipindai: ").strip().strip('"')
        thresh_input = input("Threshold kemiripan wajah [default 0.50]: ").strip()
        threshold = float(thresh_input) if thresh_input else 0.50
        html = input("Ingin membuat laporan visual HTML? (y/n) [default y]: ").strip().lower() != 'n'
        
        args = [
            sys.executable, "greverse.py",
            "--image", target,
            "--db_dir", db_dir,
            "--facecheck",
            "--threshold", str(threshold)
        ]
        if html:
            args.extend(["--html_report", "laporan_hasil.html"])
        os.system(" ".join(f'"{a}"' if " " in a else a for a in args))

    elif choice == "2":
        target = input("Masukkan path foto wajah target: ").strip().strip('"')
        query = input("Masukkan nama orang / kata kunci pencarian web: ").strip()
        out_dir = input("Folder penyimpanan hasil unduhan [default ./downloaded_images]: ").strip() or "./downloaded_images"
        args = [
            sys.executable, "greverse.py",
            "--image", target,
            "--query", query,
            "--download_dir", out_dir,
            "--facecheck",
            "--html_report", "laporan_web.html"
        ]
        os.system(" ".join(f'"{a}"' if " " in a else a for a in args))

    elif choice == "3":
        target = input("Masukkan path atau URL foto wajah target: ").strip().strip('"')
        creds = input("Masukkan path file kredensial Google Vision JSON (tekan enter jika sudah di environment): ").strip().strip('"')
        out_dir = input("Folder penyimpanan hasil unduhan [default ./downloaded_images]: ").strip() or "./downloaded_images"
        args = [
            sys.executable, "greverse.py",
            "--image", target,
            "--download_dir", out_dir,
            "--facecheck",
            "--html_report", "laporan_vision.html"
        ]
        if creds:
            args.extend(["--creds", creds])
        os.system(" ".join(f'"{a}"' if " " in a else a for a in args))

    elif choice == "4":
        target = input("Masukkan path atau URL foto wajah: ").strip().strip('"')
        links = generate_reverse_search_links(target)
        print("\n[INFO] Tautan Pencarian Reverse Image:")
        for name, link in links.items():
            print(f"- {name}: {link}")
    else:
        print("Keluar.")

def main():
    parser = argparse.ArgumentParser(
        prog='greverse.py',
        description="GReverse Plus - Enhanced Face Identification & OSINT Reverse Image Search Engine",
        epilog="Contoh: python greverse.py --image target.jpg --db_dir ./galeri/ --facecheck --html_report hasil.html"
    )
    # GReverse original arguments
    parser.add_argument('--image', type=str, help='Path ke file gambar wajah target lokal, atau URL gambar publik.')
    parser.add_argument('--query', type=str, help='Pencarian web query (nama/entitas) untuk mengumpulkan kandidat gambar.')
    parser.add_argument('--max_results', type=int, default=15, help='Maksimum hasil gambar yang diunduh/dianalisis (default: 15).')
    parser.add_argument('--facecheck', action='store_true', default=False, help='Jalankan verifikasi dan pencocokan wajah otomatis.')
    parser.add_argument('--download_dir', type=str, default=None, help='Direktori penyimpanan foto hasil unduhan dari web.')
    parser.add_argument('--multi', action='store_true', default=False, help='Gunakan mode unduh cepat paralel.')
    parser.add_argument('--procs', type=int, default=4, help='Jumlah proses worker paralel (default: 4).')
    parser.add_argument('--output_type', type=str, default='pretty', choices=['pretty', 'json', 'csv', 'raw'], help='Format tampilan output terminal.')
    parser.add_argument('--save_output', type=str, default=None, help='Path file untuk menyimpan hasil (misal results.json atau results.csv).')
    
    # Enhanced arguments
    parser.add_argument('--db_dir', '--local_dir', dest='db_dir', type=str, default=None, help='Path folder/database foto lokal untuk dipindai secara menyeluruh.')
    parser.add_argument('--threshold', type=float, default=0.50, help='Threshold batas kemiripan wajah (0.0 - 1.0, default: 0.50).')
    parser.add_argument('--html_report', type=str, default=None, help='Path file untuk menghasilkan visual report HTML interaktif (misal report.html).')
    parser.add_argument('--creds', type=str, default=None, help='Path ke file service account Google Cloud Vision JSON.')
    parser.add_argument('--reverse_links', action='store_true', default=False, help='Tampilkan URL pencarian reverse image (Google Lens, Yandex, Bing).')
    parser.add_argument('-i', '--interactive', action='store_true', default=False, help='Buka antarmuka interaktif wizard.')

    if len(sys.argv) == 1:
        run_interactive_mode()
        return

    args = parser.parse_args()

    if args.interactive:
        run_interactive_mode()
        return

    print_banner()

    # Inisialisasi Face Engine
    engine = None
    if args.facecheck or args.db_dir:
        print("[INFO] Menginisialisasi Engine Pengenalan Wajah...")
        engine = FaceEngine(threshold=args.threshold)
        print(f"[OK] Engine aktif: {get_color_tag(engine.engine_name, 'green')} (Threshold: {args.threshold})\n")

    # 1. MODE: Tampilkan Link Reverse Search Web
    if args.reverse_links:
        if not args.image:
            print("[Error] Masukkan path foto menggunakan --image untuk mendapatkan tautan reverse search.")
            return
        links = generate_reverse_search_links(args.image)
        print("Tautan Reverse Image Search Web:")
        for name, url in links.items():
            print(f"  [{name}] {url}")
        print()
        if not args.download_dir and not args.facecheck:
            return

    # 2. MODE: Pemindaian Database / Folder Foto Lokal
    if args.db_dir:
        if not args.image:
            print("[Error] Anda harus menentukan foto wajah target dengan flag --image.")
            return
        print(f"[INFO] Memulai pemindaian folder database lokal: {args.db_dir}")
        results = scan_local_directory(
            target_image_path=args.image,
            folder_path=args.db_dir,
            face_engine=engine,
            threshold=args.threshold,
            recursive=True
        )

        # Output results
        if args.output_type == 'pretty':
            print_results_table(results, title="HASIL PEMINDAIAN FOTO LOKAL")
        elif args.output_type == 'json':
            import json
            print(json.dumps(results, indent=4))
        
        if args.save_output:
            if args.save_output.lower().endswith('.csv'):
                save_csv(results, args.save_output)
            else:
                save_json(results, args.save_output)

        if args.html_report:
            generate_html_report(args.image, results, args.html_report)
        return

    # 3. MODE: Query Search Web Images (Free Mode tanpa API Key)
    if args.query:
        print(f"[INFO] Mencari kandidat gambar di web dengan kata kunci: '{args.query}'...")
        candidate_urls = search_web_images_by_query(args.query, max_results=args.max_results)
        print(f"[OK] Ditemukan {len(candidate_urls)} tautan gambar kandidat dari web.")

        download_folder = args.download_dir or "./downloaded_candidates"
        workers = args.procs if args.multi else 4
        downloaded_map = download_images_batch(candidate_urls, download_folder, max_workers=workers)

        results = []
        if args.facecheck and args.image:
            print("[INFO] Melakukan verifikasi wajah terhadap gambar yang diunduh...")
            for url, local_file in downloaded_map.items():
                verif = engine.verify_faces(args.image, local_file, custom_threshold=args.threshold)
                results.append({
                    'url': url,
                    'file_path': local_file,
                    'match': verif['match'],
                    'similarity': verif['similarity'],
                    'similarity_pct': verif['similarity_pct'],
                    'status': verif['status']
                })
            results.sort(key=lambda x: x['similarity'], reverse=True)

            print_results_table(results, title=f"HASIL PENCARIAN WEB: '{args.query}'")
            if args.save_output:
                if args.save_output.lower().endswith('.csv'):
                    save_csv(results, args.save_output)
                else:
                    save_json(results, args.save_output)
            if args.html_report:
                generate_html_report(args.image, results, args.html_report)
        else:
            print(f"[OK] Gambar telah tersimpan di direktori: {download_folder}")
        return

    # 4. MODE: Google Cloud Vision API Web Detection (Arsitektur Asli GReverse)
    if args.image:
        try:
            from modules.vision_search import search_google_vision, extract_all_image_urls
            print(f"[INFO] Mengirim gambar ke Google Cloud Vision Web Detection...")
            vision_results = search_google_vision(args.image, max_results=args.max_results, creds_file=args.creds)
            print("[OK] Web Detection selesai!")

            matched_urls = extract_all_image_urls(vision_results)
            print(f"[INFO] Ditemukan {len(matched_urls)} gambar serupa di web.")

            if args.download_dir:
                workers = args.procs if args.multi else 4
                downloaded_map = download_images_batch(matched_urls, args.download_dir, max_workers=workers)

                if args.facecheck and engine:
                    results = []
                    for url, local_file in downloaded_map.items():
                        verif = engine.verify_faces(args.image, local_file, custom_threshold=args.threshold)
                        results.append({
                            'url': url,
                            'file_path': local_file,
                            'match': verif['match'],
                            'similarity': verif['similarity'],
                            'similarity_pct': verif['similarity_pct'],
                            'status': verif['status']
                        })
                    results.sort(key=lambda x: x['similarity'], reverse=True)
                    print_results_table(results, title="HASIL VERIFIKASI GOOGLE VISION")

                    if args.save_output:
                        save_json(results, args.save_output)
                    if args.html_report:
                        generate_html_report(args.image, results, args.html_report)
            else:
                # Cetak daftar halaman web yang memuat gambar
                print("\nHalaman Web yang Memuat Gambar Serupa:")
                for p in vision_results.get('pages_with_matching_images', []):
                    print(f"  - [{p.get('title')}] {p.get('url')}")
                if args.save_output:
                    save_json(vision_results, args.save_output)

        except (ImportError, ValueError, RuntimeError) as e:
            print(f"\n{get_color_tag('[PERHATIAN]', 'yellow')} {e}")
            print("\nAlternatif yang bisa Anda gunakan sekarang tanpa Google Cloud Vision API:")
            print("1. Gunakan opsi pencarian query web: python greverse.py --image <foto> --query \"Nama Orang\" --download_dir ./unduhan --facecheck")
            print("2. Gunakan pemindaian folder database lokal: python greverse.py --image <foto> --db_dir <folder_foto> --facecheck")
            print("3. Dapatkan tautan Google Lens & Yandex: python greverse.py --image <foto> --reverse_links\n")

if __name__ == "__main__":
    main()
