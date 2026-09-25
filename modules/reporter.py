import os
import json
import csv
import base64

def print_banner():
    banner = r"""
========================================================================
   ____ ____                              ____  _           
  / ___|  _ \ _____   _____ _ __ ___  ___|  _ \| |_   _ ___ 
 | |  _| |_) / _ \ \ / / _ \ '__/ __|/ _ \ |_) | | | | / __|
 | |_| |  _ <  __/\ V /  __/ |  \__ \  __/  __/| | |_| \__ \
  \____|_| \_\___| \_/ \___|_|  |___/\___|_|   |_|\__,_|___/
        OSINT Face Identification & Recognition Engine
========================================================================
"""
    print(banner)

def get_color_tag(text, color):
    # ANSI colors
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'bold': '\033[1m',
        'reset': '\033[0m'
    }
    # Check if Windows console supports ANSI
    if os.name == 'nt':
        os.system('') # Enables VT100 in Windows 10/11
    c = colors.get(color, '')
    r = colors['reset']
    return f"{c}{text}{r}"

def print_results_table(results, title="HASIL VERIFIKASI WAJAH"):
    print("\n" + "=" * 76)
    print(f" {title.center(74)} ")
    print("=" * 76)
    header = f"{'No':<4} | {'Status':<12} | {'Similarity':<12} | {'Target Source / File'}"
    print(header)
    print("-" * 76)

    matches_count = 0
    for i, r in enumerate(results, 1):
        status_raw = r.get('status', 'UNKNOWN')
        sim_pct = r.get('similarity_pct', '0%')
        source = r.get('file_path') or r.get('url') or r.get('filename') or '-'
        if len(source) > 42:
            source = "..." + source[-39:]

        if r.get('match'):
            matches_count += 1
            status_str = get_color_tag("[MATCH]", 'green')
        else:
            status_str = get_color_tag("[NO MATCH]", 'red')

        print(f"{i:<4} | {status_str:<21} | {sim_pct:<12} | {source}")

    print("-" * 76)
    summary_text = f"Total Diperiksa: {len(results)} | Cocok: {matches_count} | Tidak Cocok: {len(results) - matches_count}"
    print(get_color_tag(summary_text, 'cyan'))
    print("=" * 76 + "\n")

def save_json(data, output_filepath):
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[OK] Hasil disimpan ke JSON: {output_filepath}")

def save_csv(results, output_filepath):
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    if not results:
        return
    fieldnames = ['no', 'match', 'status', 'similarity', 'similarity_pct', 'source']
    with open(output_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for idx, r in enumerate(results, 1):
            writer.writerow({
                'no': idx,
                'match': r.get('match'),
                'status': r.get('status'),
                'similarity': r.get('similarity'),
                'similarity_pct': r.get('similarity_pct'),
                'source': r.get('file_path') or r.get('url') or ''
            })
    print(f"[OK] Hasil disimpan ke CSV: {output_filepath}")

def encode_img_to_base64(path):
    try:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')
    except Exception:
        pass
    return ""

def generate_html_report(target_image_path, results, output_filepath):
    """Menghasilkan laporan visual HTML interaktif dengan perbandingan foto."""
    os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
    target_b64 = encode_img_to_base64(target_image_path)

    cards_html = ""
    for idx, r in enumerate(results, 1):
        is_match = r.get('match', False)
        sim_pct = r.get('similarity_pct', '0%')
        sim_val = r.get('similarity', 0.0)
        source = r.get('file_path') or r.get('url') or ''
        badge_cls = "badge-match" if is_match else "badge-nomatch"
        badge_text = "MATCH" if is_match else "NO MATCH"
        
        img_b64 = ""
        if r.get('file_path'):
            img_b64 = encode_img_to_base64(r['file_path'])
        elif r.get('url'):
            img_b64 = r['url']

        meter_color = "#10b981" if is_match else "#ef4444"

        cards_html += f"""
        <div class="result-card {'border-match' if is_match else ''}">
            <div class="card-img-container">
                {f'<img src="{img_b64}" alt="Result Image" />' if img_b64 else '<div class="no-img">No Preview</div>'}
                <span class="badge {badge_cls}">{badge_text}</span>
            </div>
            <div class="card-body">
                <div class="similarity-row">
                    <span class="score-label">Kemiripan:</span>
                    <span class="score-value">{sim_pct}</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {min(100, int(sim_val * 100))}%; background: {meter_color};"></div>
                </div>
                <div class="source-info">
                    <small>Sumber:</small>
                    <p class="source-text" title="{source}">{source}</p>
                </div>
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Laporan Identifikasi Wajah - GReverse Plus</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        body {{ background: var(--bg-primary); color: var(--text-main); padding: 2rem 1rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 2rem; border-bottom: 1px solid #334155; padding-bottom: 1.5rem; }}
        h1 {{ font-size: 2.2rem; background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        p.subtitle {{ color: var(--text-muted); margin-top: 0.5rem; }}
        
        .overview-panel {{ display: flex; flex-wrap: wrap; gap: 2rem; background: var(--bg-secondary); border-radius: 12px; padding: 1.5rem; margin-bottom: 2.5rem; align-items: center; border: 1px solid #334155; }}
        .target-box {{ flex: 0 0 200px; text-align: center; }}
        .target-img {{ width: 180px; height: 180px; object-fit: cover; border-radius: 10px; border: 3px solid var(--accent-blue); }}
        .stats-box {{ flex: 1; min-width: 280px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-top: 1rem; }}
        .stat-card {{ background: #0f172a; padding: 1rem; border-radius: 8px; text-align: center; }}
        .stat-num {{ font-size: 1.8rem; font-weight: bold; color: #38bdf8; }}
        .stat-label {{ font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; margin-top: 0.2rem; }}

        .results-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; }}
        .result-card {{ background: var(--card-bg); border-radius: 12px; overflow: hidden; border: 1px solid #334155; transition: transform 0.2s, box-shadow 0.2s; }}
        .result-card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        .border-match {{ border: 2px solid var(--accent-green); }}
        .card-img-container {{ position: relative; width: 100%; height: 220px; background: #090d16; overflow: hidden; }}
        .card-img-container img {{ width: 100%; height: 100%; object-fit: cover; }}
        .no-img {{ display: flex; height: 100%; align-items: center; justify-content: center; color: var(--text-muted); }}
        .badge {{ position: absolute; top: 10px; right: 10px; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }}
        .badge-match {{ background: var(--accent-green); color: #022c22; }}
        .badge-nomatch {{ background: var(--accent-red); color: #450a0a; }}

        .card-body {{ padding: 1rem; }}
        .similarity-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }}
        .score-value {{ font-size: 1.2rem; font-weight: bold; color: #f8fafc; }}
        .progress-bar-bg {{ width: 100%; height: 8px; background: #0f172a; border-radius: 4px; overflow: hidden; margin-bottom: 1rem; }}
        .progress-bar-fill {{ height: 100%; border-radius: 4px; }}
        .source-info small {{ color: var(--text-muted); font-size: 0.75rem; }}
        .source-text {{ color: #cbd5e1; font-size: 0.8rem; word-break: break-all; margin-top: 2px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>GReverse Plus - Laporan Identifikasi Wajah</h1>
            <p class="subtitle">Hasil Pemindaian OSINT & Verifikasi Kemiripan Wajah Berbasis Deep Learning</p>
        </header>

        <div class="overview-panel">
            <div class="target-box">
                {f'<img class="target-img" src="{target_b64}" alt="Foto Target" />' if target_b64 else '<div class="target-img no-img">Foto Target</div>'}
                <div style="margin-top: 8px; font-weight: 600; font-size: 0.9rem;">Foto Target</div>
            </div>
            <div class="stats-box">
                <h2>Ringkasan Pemindaian</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-num">{len(results)}</div>
                        <div class="stat-label">Total Diperiksa</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" style="color: var(--accent-green);">{sum(1 for r in results if r.get('match'))}</div>
                        <div class="stat-label">Wajah Cocok</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" style="color: var(--accent-red);">{sum(1 for r in results if not r.get('match'))}</div>
                        <div class="stat-label">Tidak Cocok</div>
                    </div>
                </div>
            </div>
        </div>

        <h3 style="margin-bottom: 1rem;">Daftar Kandidat & Hasil Perbandingan:</h3>
        <div class="results-grid">
            {cards_html}
        </div>
    </div>
</body>
</html>
"""
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[OK] Laporan visual HTML berhasil dibuat: {output_filepath}")
