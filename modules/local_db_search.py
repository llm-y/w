import os
from tqdm import tqdm

SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.tif')

def scan_local_directory(target_image_path, folder_path, face_engine, threshold=0.50, recursive=True):
    """
    Memindai seluruh foto di dalam folder/database lokal untuk mencocokkan wajah target.
    Mengembalikan daftar hasil yang sudah diurutkan dari skor kemiripan tertinggi.
    """
    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Folder tidak valid: {folder_path}")

    # Kumpulkan seluruh file gambar
    image_files = []
    if recursive:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(SUPPORTED_EXTENSIONS):
                    image_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(folder_path):
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                full_p = os.path.join(folder_path, file)
                if os.path.isfile(full_p):
                    image_files.append(full_p)

    if not image_files:
        print(f"[Warning] Tidak ditemukan file gambar di direktori: {folder_path}")
        return []

    print(f"\n[INFO] Mengekstrak embedding wajah target dari: {target_image_path}")
    target_faces = face_engine.extract_faces(target_image_path)
    if not target_faces:
        print(f"[Error] Tidak ada wajah yang terdeteksi pada foto target!")
        return []

    target_emb = target_faces[0]['embedding']
    print(f"[OK] Wajah target terdeteksi! Memindai {len(image_files)} foto lokal...\n")

    results = []
    for img_path in tqdm(image_files, desc="Memindai Database Lokal", unit="foto"):
        # Abaikan file target itu sendiri jika berada di folder yang sama
        if os.path.abspath(img_path) == os.path.abspath(target_image_path):
            continue

        try:
            cand_faces = face_engine.extract_faces(img_path)
            if not cand_faces:
                continue

            max_sim = 0.0
            best_face = None
            for f in cand_faces:
                sim = face_engine.calculate_similarity(target_emb, f['embedding'])
                if sim > max_sim:
                    max_sim = sim
                    best_face = f

            is_match = max_sim >= threshold
            results.append({
                'file_path': img_path,
                'filename': os.path.basename(img_path),
                'match': is_match,
                'similarity': round(max_sim, 4),
                'similarity_pct': f"{max_sim * 100:.1f}%",
                'faces_count': len(cand_faces),
                'best_box': best_face['box'] if best_face else None,
                'threshold': threshold,
                'status': "MATCH" if is_match else "NO_MATCH"
            })
        except Exception:
            continue

    # Urutkan berdasarkan similarity tertinggi
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results
