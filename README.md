# WHO? (`w.py`) - Face Identity Finder

Aplikasi sederhana dan cepat untuk mencari identitas seseorang dari foto (**"Who is this person?"**).

---

## 🚀 Cara Penggunaan

Cukup jalankan satu perintah ini di terminal:

```bash
python w.py
```

Lalu terminal akan meminta Anda memasukkan foto:
```text
======================================================
          WHO? (w.py) - SIAPA ORANG INI?             
======================================================

Tarik dan lepas (drag & drop) foto ke sini lalu tekan Enter:
> 
```

*(Atau jika ingin langsung: `python w.py foto_target.jpg`)*

---

## 🔍 Apa Saja yang Dihasilkan?

1. **Analisis Biometrik Wajah**:
   - Jumlah wajah yang terdeteksi
   - Estimasi jenis kelamin dan usia
   - Skor kualitas & kejelasan deteksi foto

2. **Dugaan Nama & Akun Medsos**:
   - Menampilkan dugaan nama dari database web / Google Vision jika tersedia.
   - Daftar tautan akun media sosial (Instagram, LinkedIn, Wikipedia, Facebook).

3. **Pencarian 1-Klik di Browser**:
   - **[1] Google Lens** : Langsung mencari nama dan halaman web yang memuat foto tersebut.
   - **[2] Yandex Images** : Paling efektif untuk mencocokkan wajah ke akun medsos asli.
   - **[3] FaceCheck.id** : Database pencarian wajah publik khusus OSINT.
