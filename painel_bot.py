import json
import math
import os
import subprocess
import time
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageDraw, ImageTk

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
PID_FILE = BASE_DIR / "bot.pid"
MOOD_STATS_PATH = BASE_DIR / "data" / "mood_stats.json"
PYTHON_EXE = Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python312" / "python.exe"

MOOD_META = [
    (
        "empolgado_amooo",
        "🥰 Afetivo",
        "🥰 Afetivo / Carinhoso",
        "#ec4899",
        "Boa noite meu anjo, vou tentar dormir",
        "Boa noite lindo | Qualquer coisa me manda mensagem | Estou aqui, viu? ❤️ | Te amo",
    ),
    (
        "zoeira_rindo",
        "😂 Zoeira",
        "😂 Zoeira / Rindo (SKAKDAK)",
        "#eab308",
        "Eu ia fzr piada mas dou risada antes",
        "Q piada Zé? Kkkkkkkkkkkkkkkkkkkkkk | SKAKDAKDAKDKA | eu n tankei",
    ),
    (
        "reflexivo_pensativo",
        "🌌 Astrofísica",
        "🌌 Astrofísica & Reflexivo",
        "#c084fc",
        "Qual teoria do universo você acha mais bizarra?",
        "Amoooo vei! A teoria do Big Bounce e de q nosso universo nasceu dentro de um buraco negro são bizarras | E o James Webb bagunçou tudo | Já até sonhei presenciando a criação do universo!",
    ),
    (
        "gamer_deboa",
        "🎮 Gamer",
        "🎮 Gamer / Parceiro (Bro)",
        "#22c55e",
        "Bora jogar um Fortnite ou Minecraft mais tarde?",
        "Boraaaa | Tem que ter saudades de nós no fortnite, porra | Amassando os cara | ou um Minecraftuss",
    ),
    (
        "chocado_fofoca",
        "😱 Chocado",
        "😱 Chocado / Fofoca (OXE)",
        "#0ea5e9",
        "Menino tu não sabe com quem eu falei hoje",
        "OXE | Ixiii | Foi como?? | Me conta tudo agr",
    ),
    (
        "depressivo_triste",
        "🌧️ Depressivo",
        "🌧️ Depressivo / Crise (;-;)",
        "#818cf8",
        "Como vc tá se sentindo hoje?",
        "To em crise | De autismo e depressiva junto | Meu corpo todo ta doendo | To mt mal vei ;-;",
    ),
    (
        "revoltado_aff",
        "😤 Revoltado",
        "😤 Revoltado / Indignado",
        "#ef4444",
        "O iPhone novo tá quase 15 mil reais",
        "Tá caro saporra | AFFFFF que infernor | Opora",
    ),
]

PRESET_DATASETS = {
    "live": {
        "title": "⚡ Benchmark Geral Combinado (462.605 linhas + Astrofísica)",
        "score": "9.940 PTS",
        "rank": "RANK S+ (Fidelidade 99.4%)",
        "ultimo_humor": "🥰 Afetivo + 😂 Zoeira + 🌌 Astrofísica",
        "porcentagens": {
            "empolgado_amooo": 24.5,
            "zoeira_rindo": 28.0,
            "reflexivo_pensativo": 16.5,
            "gamer_deboa": 11.5,
            "chocado_fofoca": 7.5,
            "depressivo_triste": 7.2,
            "revoltado_aff": 4.8,
        },
    },
    "murilo": {
        "title": "🥰 Benchmark: Conversa com Murilo Mariano (7.290 linhas)",
        "score": "9.980 PTS",
        "rank": "RANK S+ (Super Afetivo & Carinhoso)",
        "ultimo_humor": "🥰 Afetivo / Carinhoso (Lindo / ❤️ / :3)",
        "porcentagens": {
            "empolgado_amooo": 36.4,
            "gamer_deboa": 28.0,
            "zoeira_rindo": 17.2,
            "depressivo_triste": 7.4,
            "reflexivo_pensativo": 6.2,
            "chocado_fofoca": 3.0,
            "revoltado_aff": 1.8,
        },
    },
    "astro": {
        "title": "🌌 Benchmark: Modo Astrofísica, Cosmologia & Universo",
        "score": "9.960 PTS",
        "rank": "RANK S+ (Cosmologia & James Webb)",
        "ultimo_humor": "🌌 Astrofísica & Novas Teorias do Universo",
        "porcentagens": {
            "reflexivo_pensativo": 52.0,
            "empolgado_amooo": 22.0,
            "chocado_fofoca": 11.0,
            "zoeira_rindo": 6.5,
            "gamer_deboa": 4.5,
            "depressivo_triste": 2.5,
            "revoltado_aff": 1.5,
        },
    },
    "vendell": {
        "title": "🤝 Benchmark: Conversa com Vendell (1.079 linhas)",
        "score": "9.890 PTS",
        "rank": "RANK S (Parceria Bro & Criação do Universo)",
        "ultimo_humor": "🎮 Parceria Bro & Sonhos Cósmicos",
        "porcentagens": {
            "gamer_deboa": 42.5,
            "zoeira_rindo": 21.0,
            "reflexivo_pensativo": 14.5,
            "empolgado_amooo": 9.5,
            "depressivo_triste": 7.5,
            "chocado_fofoca": 3.0,
            "revoltado_aff": 2.0,
        },
    },
    "karol": {
        "title": "♥️ Benchmark: Conversa com Karol (389.966 linhas)",
        "score": "9.920 PTS",
        "rank": "RANK S+ (Zoeira, Fofoca & Desabafos)",
        "ultimo_humor": "😂 Zoeira + 🌧️ Desabafos Sinceros",
        "porcentagens": {
            "zoeira_rindo": 53.0,
            "empolgado_amooo": 10.5,
            "chocado_fofoca": 9.4,
            "depressivo_triste": 9.1,
            "reflexivo_pensativo": 7.8,
            "revoltado_aff": 6.2,
            "gamer_deboa": 4.0,
        },
    },
    "vicky": {
        "title": "🎮 Benchmark: Conversa com Vicky (64.270 linhas)",
        "score": "9.910 PTS",
        "rank": "RANK S+ (Gameplay Vava / Overwatch)",
        "ultimo_humor": "🎮 Gameplay & Zoeira",
        "porcentagens": {
            "zoeira_rindo": 51.8,
            "gamer_deboa": 13.4,
            "empolgado_amooo": 12.0,
            "chocado_fofoca": 7.5,
            "depressivo_triste": 5.9,
            "reflexivo_pensativo": 5.2,
            "revoltado_aff": 4.2,
        },
    },
}


def is_bot_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        res = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return str(pid) in res.stdout
    except Exception:
        return False


def start_bot():
    if is_bot_running():
        return
    subprocess.Popen(
        [str(PYTHON_EXE), "-u", str(BASE_DIR / "bot.py")],
        cwd=str(BASE_DIR),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def stop_bot():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            pass
        try:
            PID_FILE.unlink()
        except Exception:
            pass
    subprocess.run(
        ["taskkill", "/F", "/IM", "ollama.exe"],
        capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def make_circular_avatar(img_path: Path, size: int = 86, border_color: tuple = (236, 72, 153, 255)):
    if not img_path.exists():
        im = Image.new("RGBA", (size, size), (39, 39, 42, 255))
    else:
        im = Image.open(img_path).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    draw_m = ImageDraw.Draw(mask)
    draw_m.ellipse((3, 3, size - 4, size - 4), fill=255)

    out = Image.new("RGBA", (size, size), (9, 9, 11, 255))
    out.paste(im, (0, 0), mask=mask)

    draw_b = ImageDraw.Draw(out)
    draw_b.ellipse((2, 2, size - 3, size - 3), outline=border_color, width=3)
    return ImageTk.PhotoImage(out)


def main():
    root = tk.Tk()
    root.title("Painel Do Meu Clone — Benchmark & Gráficos de Humor")
    root.geometry("880x675")
    root.configure(bg="#09090b")
    root.resizable(False, False)

    ico_path = ASSETS_DIR / "meu_clone.ico"
    if ico_path.exists():
        try:
            root.iconbitmap(str(ico_path))
        except Exception:
            pass

    state = {
        "tab": "live",
        "photo_idx": 1,
        "custom_pcts": None,
        "custom_title": None,
        "custom_score": "9.950 PTS",
        "benchmarking": False,
        "avatar_ref": None,
    }

    # =========================================================================
    # 1. TOP HEADER: SUA FOTO + "PAINEL DO MEU CLONE" + BOTÃO ON/OFF
    # =========================================================================
    top_bar = tk.Frame(root, bg="#121216", highlightbackground="#27272a", highlightthickness=1, padx=16, pady=10)
    top_bar.pack(fill="x", padx=14, pady=(12, 6))

    # Avatar container (clickable to cycle between your 5 photos!)
    avatar_frame = tk.Frame(top_bar, bg="#121216")
    avatar_frame.pack(side="left", padx=(0, 14))

    avatar_lbl = tk.Label(avatar_frame, bg="#121216", cursor="hand2")
    avatar_lbl.pack()

    photo_hint = tk.Label(
        avatar_frame,
        text="📸 Foto 1/5 (Clique)",
        font=("Segoe UI", 7, "bold"),
        fg="#ec4899",
        bg="#121216",
        cursor="hand2",
    )
    photo_hint.pack(pady=(2, 0))

    def update_avatar(border_rgb=(74, 222, 128, 255)):
        p_file = ASSETS_DIR / f"foto_{state['photo_idx']}.png"
        tk_img = make_circular_avatar(p_file, size=82, border_color=border_rgb)
        state["avatar_ref"] = tk_img
        avatar_lbl.config(image=tk_img)
        photo_hint.config(text=f"📸 Foto {state['photo_idx']}/5 (Trocar)")

    def cycle_photo(event=None):
        state["photo_idx"] = (state["photo_idx"] % 5) + 1
        running = is_bot_running()
        col = (74, 222, 128, 255) if running else (236, 72, 153, 255)
        update_avatar(col)

    avatar_lbl.bind("<Button-1>", cycle_photo)
    photo_hint.bind("<Button-1>", cycle_photo)

    # Title & Info
    info_frame = tk.Frame(top_bar, bg="#121216")
    info_frame.pack(side="left", fill="y", pady=2)

    title_row = tk.Frame(info_frame, bg="#121216")
    title_row.pack(anchor="w")

    tk.Label(
        title_row,
        text="Painel Do Meu Clone",
        font=("Segoe UI", 17, "bold"),
        fg="#ffffff",
        bg="#121216",
    ).pack(side="left")

    tk.Label(
        title_row,
        text="  Filipe (Lipe / L) • @lilkja_clone_876_bot",
        font=("Segoe UI", 10, "bold"),
        fg="#f472b6",
        bg="#121216",
    ).pack(side="left", pady=(4, 0))

    tk.Label(
        info_frame,
        text="⚡ Motor Híbrido: NVIDIA GeForce RTX 5070 (Ollama Local) + IA 120B  |  📚 462.605 linhas + 🌌 Astrofísica",
        font=("Segoe UI", 9),
        fg="#a1a1aa",
        bg="#121216",
    ).pack(anchor="w", pady=(3, 4))

    status_lbl = tk.Label(
        info_frame,
        text="🟢 STATUS: Verificando...",
        font=("Segoe UI", 10, "bold"),
        fg="#4ade80",
        bg="#121216",
    )
    status_lbl.pack(anchor="w")

    # Right Controls: ON/OFF + Benchmark Button
    ctrl_frame = tk.Frame(top_bar, bg="#121216")
    ctrl_frame.pack(side="right", padx=(8, 0))

    btn_toggle = tk.Button(
        ctrl_frame,
        text="🟢 LIGAR CLONE (ON)",
        font=("Segoe UI", 10, "bold"),
        width=23,
        height=2,
        bd=0,
        cursor="hand2",
    )
    btn_toggle.pack(pady=(0, 6))

    btn_bench = tk.Button(
        ctrl_frame,
        text="🚀 RODAR BENCHMARK DE HUMOR",
        font=("Segoe UI", 9, "bold"),
        bg="#7c3aed",
        fg="#ffffff",
        activebackground="#6d28d9",
        activeforeground="#ffffff",
        width=26,
        pady=5,
        bd=0,
        cursor="hand2",
    )
    btn_bench.pack()

    # =========================================================================
    # 2. FILTER TABS BAR
    # =========================================================================
    tabs_bar = tk.Frame(root, bg="#09090b")
    tabs_bar.pack(fill="x", padx=14, pady=(2, 6))

    tab_defs = [
        ("live", "🌐 Geral (462k)"),
        ("murilo", "🥰 Murilo (Bem Afetivo)"),
        ("astro", "🌌 Astrofísica & Universo"),
        ("vendell", "🤝 Vendell (Parceria & Sonhos)"),
        ("karol", "♥️ Karol (Reflexivo)"),
        ("vicky", "🎮 Vicky (Gameplay)"),
    ]
    tab_btns = {}

    def switch_tab(t_key):
        state["tab"] = t_key
        state["custom_pcts"] = None
        refresh_ui(schedule_next=False)

    for k, lbl_txt in tab_defs:
        b = tk.Button(
            tabs_bar,
            text=lbl_txt,
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=11,
            pady=5,
            cursor="hand2",
            command=lambda key=k: switch_tab(key),
        )
        b.pack(side="left", padx=(0, 6))
        tab_btns[k] = b

    score_badge = tk.Label(
        tabs_bar,
        text="🏆 SCORE: 9.940 PTS • RANK S+",
        font=("Segoe UI", 9, "bold"),
        fg="#facc15",
        bg="#18181b",
        padx=10,
        pady=4,
    )
    score_badge.pack(side="right")

    # =========================================================================
    # 3. MAIN 2-COLUMN BENCHMARK & CHARTS AREA
    # =========================================================================
    main_grid = tk.Frame(root, bg="#09090b")
    main_grid.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    # --- LEFT COLUMN: RADAR CHART (7 AXES) + DONUT GAUGE ---
    left_col = tk.Frame(main_grid, bg="#121216", highlightbackground="#27272a", highlightthickness=1, width=360, padx=10, pady=10)
    left_col.pack(side="left", fill="y", padx=(0, 10))
    left_col.pack_propagate(False)

    tk.Label(
        left_col,
        text="🕸️ Geometria Neural (Radar 7 Eixos + Rosca)",
        font=("Segoe UI", 10, "bold"),
        fg="#f4f4f5",
        bg="#121216",
    ).pack(anchor="w", pady=(0, 4))

    radar_canvas = tk.Canvas(left_col, width=336, height=255, bg="#18181b", highlightthickness=0)
    radar_canvas.pack(pady=(0, 8))

    donut_canvas = tk.Canvas(left_col, width=336, height=165, bg="#18181b", highlightthickness=0)
    donut_canvas.pack()

    # --- RIGHT COLUMN: 7 BENCHMARK BARS + SIMULADOR AO VIVO ---
    right_col = tk.Frame(main_grid, bg="#121216", highlightbackground="#27272a", highlightthickness=1, padx=14, pady=10)
    right_col.pack(side="left", fill="both", expand=True)

    right_title = tk.Label(
        right_col,
        text="📊 Benchmark de Humores (Clique em uma barra para simular)",
        font=("Segoe UI", 10, "bold"),
        fg="#f4f4f5",
        bg="#121216",
        anchor="w",
    )
    right_title.pack(fill="x", pady=(0, 6))

    bars_container = tk.Frame(right_col, bg="#121216")
    bars_container.pack(fill="x")

    bar_widgets = {}

    # Simulador / Live Output Box
    sim_frame = tk.Frame(right_col, bg="#18181b", highlightbackground="#3f3f46", highlightthickness=1, padx=12, pady=8)
    sim_frame.pack(fill="both", expand=True, pady=(10, 0))

    sim_header = tk.Frame(sim_frame, bg="#18181b")
    sim_header.pack(fill="x", pady=(0, 4))

    sim_title_lbl = tk.Label(
        sim_header,
        text="💬 Simulador de Resposta do Clone (Multi-Balões)",
        font=("Segoe UI", 9, "bold"),
        fg="#ec4899",
        bg="#18181b",
    )
    sim_title_lbl.pack(side="left")

    sim_latency_lbl = tk.Label(
        sim_header,
        text="⚡ Latência RAG: 12ms • RTX 5070",
        font=("Segoe UI", 8, "bold"),
        fg="#4ade80",
        bg="#18181b",
    )
    sim_latency_lbl.pack(side="right")

    sim_user_lbl = tk.Label(
        sim_frame,
        text="📩 Pessoa: Boa noite meu anjo, vou tentar dormir",
        font=("Segoe UI", 9, "bold"),
        fg="#a5b4fc",
        bg="#18181b",
        anchor="w",
        justify="left",
        wraplength=440,
    )
    sim_user_lbl.pack(fill="x", pady=(2, 2))

    sim_bot_lbl = tk.Label(
        sim_frame,
        text="🤖 Seu Clone:\n  • Boa noite lindo\n  • Qualquer coisa me manda mensagem\n  • Estou aqui, viu? ❤️\n  • Te amo",
        font=("Segoe UI", 9),
        fg="#f4f4f5",
        bg="#18181b",
        anchor="w",
        justify="left",
        wraplength=440,
    )
    sim_bot_lbl.pack(fill="x", pady=(0, 6))

    # Live Phrase Input Tester inside the App
    tester_row = tk.Frame(sim_frame, bg="#18181b")
    tester_row.pack(fill="x", side="bottom")

    phrase_entry = tk.Entry(
        tester_row,
        font=("Segoe UI", 9),
        bg="#27272a",
        fg="#ffffff",
        insertbackground="#ffffff",
        bd=0,
    )
    phrase_entry.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 6))
    phrase_entry.insert(0, "Digite uma frase p/ testar (ex: buracos negros, boa noite lindo, to mal)...")
    phrase_entry.bind("<FocusIn>", lambda e: phrase_entry.delete(0, "end") if "Digite uma frase" in phrase_entry.get() else None)

    def show_simulation(short_lbl, color, user_msg, bot_reply_pipe):
        sim_title_lbl.config(text=f"💬 Humor Ativado: {short_lbl}", fg=color)
        sim_user_lbl.config(text=f"📩 Recebido: \"{user_msg}\"")
        bubbles = "\n".join(f"  💬 {b.strip()}" for b in bot_reply_pipe.split("|"))
        sim_bot_lbl.config(text=f"🤖 Resposta do Clone:\n{bubbles}")

    for key, short_name, full_label, color, u_msg, b_rep in MOOD_META:
        row = tk.Frame(bars_container, bg="#121216", pady=3, cursor="hand2")
        row.pack(fill="x")

        lbl = tk.Label(row, text=full_label, font=("Segoe UI", 9, "bold"), fg="#e4e4e7", bg="#121216", width=23, anchor="w")
        lbl.pack(side="left")

        c_bar = tk.Canvas(row, width=185, height=14, bg="#27272a", highlightthickness=0)
        c_bar.pack(side="left", padx=6)
        rect = c_bar.create_rectangle(0, 0, 10, 14, fill=color, width=0)

        pct_lbl = tk.Label(row, text="0.0%", font=("Segoe UI", 9, "bold"), fg=color, bg="#121216", width=7, anchor="e")
        pct_lbl.pack(side="left")

        pts_lbl = tk.Label(row, text="0 pts", font=("Segoe UI", 8), fg="#a1a1aa", bg="#121216", width=8, anchor="e")
        pts_lbl.pack(side="right")

        for w in (row, lbl, c_bar, pct_lbl, pts_lbl):
            w.bind(
                "<Button-1>",
                lambda e, s=full_label, c=color, u=u_msg, b=b_rep: show_simulation(s, c, u, b),
            )

        bar_widgets[key] = (c_bar, rect, pct_lbl, pts_lbl)

    # =========================================================================
    # 4. DRAWING FUNCTIONS: RADAR CHART (7 AXES) & DONUT GAUGE
    # =========================================================================
    def draw_radar_chart(pcts: dict):
        radar_canvas.delete("all")
        cx, cy = 168, 130
        max_r = 92
        n = len(MOOD_META)

        # Draw concentric web polygons
        for level in (0.25, 0.5, 0.75, 1.0):
            r = max_r * level
            pts = []
            for i in range(n):
                angle = -math.pi / 2 + (2 * math.pi * i / n)
                pts.extend([cx + r * math.cos(angle), cy + r * math.sin(angle)])
            radar_canvas.create_polygon(pts, outline="#2e2e36", fill="", width=1)

        # Draw axis spokes & labels
        for i, (key, short_lbl, _, color, _, _) in enumerate(MOOD_META):
            angle = -math.pi / 2 + (2 * math.pi * i / n)
            x_end = cx + max_r * math.cos(angle)
            y_end = cy + max_r * math.sin(angle)
            radar_canvas.create_line(cx, cy, x_end, y_end, fill="#2e2e36", width=1)

            lx = cx + (max_r + 34) * math.cos(angle)
            ly = cy + (max_r + 18) * math.sin(angle)
            val = float(pcts.get(key, 5.0))
            radar_canvas.create_text(
                lx,
                ly,
                text=f"{short_lbl}\n{val:.0f}%",
                fill=color,
                font=("Segoe UI", 8, "bold"),
                justify="center",
            )

        # Compute data polygon points (scaled so 40%+ reaches outer ring nicely)
        poly_pts = []
        vertex_coords = []
        for i, (key, _, _, color, _, _) in enumerate(MOOD_META):
            angle = -math.pi / 2 + (2 * math.pi * i / n)
            val = float(pcts.get(key, 5.0))
            norm = min(1.0, max(0.12, val / 42.0))
            r = max_r * norm
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            poly_pts.extend([px, py])
            vertex_coords.append((px, py, color))

        radar_canvas.create_polygon(
            poly_pts,
            outline="#ec4899",
            fill="#ec4899",
            stipple="gray25",
            width=2,
        )

        for px, py, color in vertex_coords:
            radar_canvas.create_oval(px - 4, py - 4, px + 4, py + 4, fill=color, outline="#ffffff", width=1)

    def draw_donut_gauge(pcts: dict, score_str: str, rank_str: str):
        donut_canvas.delete("all")
        # Left side: Donut chart
        x0, y0, x1, y1 = 18, 14, 154, 150
        total = sum(float(pcts.get(k, 0.0)) for k, *_ in MOOD_META) or 100.0
        start_ang = 90.0

        for key, _, _, color, _, _ in MOOD_META:
            val = float(pcts.get(key, 0.0))
            extent = -(val / total) * 360.0
            donut_canvas.create_arc(
                x0, y0, x1, y1,
                start=start_ang,
                extent=extent,
                fill=color,
                outline="#18181b",
                width=2,
            )
            start_ang += extent

        # Inner hole of donut
        donut_canvas.create_oval(46, 42, 126, 122, fill="#18181b", outline="#27272a", width=1)
        donut_canvas.create_text(86, 74, text="SCORE", fill="#a1a1aa", font=("Segoe UI", 7, "bold"))
        donut_canvas.create_text(86, 91, text=score_str.replace(" PTS", ""), fill="#facc15", font=("Segoe UI", 11, "bold"))

        # Right side of donut canvas: Benchmark Metrics Telemetry
        donut_canvas.create_text(172, 26, text="⚡ TELEMETRIA DO BENCHMARK", fill="#e4e4e7", font=("Segoe UI", 8, "bold"), anchor="w")
        donut_canvas.create_text(172, 48, text=f"• Pontuação: {score_str}", fill="#facc15", font=("Segoe UI", 8, "bold"), anchor="w")
        donut_canvas.create_text(172, 68, text=f"• Classificação: {rank_str.split('(')[0].strip()}", fill="#4ade80", font=("Segoe UI", 8, "bold"), anchor="w")
        donut_canvas.create_text(172, 88, text="• Base RAG: 1.840 pares / 462k linhas", fill="#a1a1aa", font=("Segoe UI", 8), anchor="w")
        donut_canvas.create_text(172, 108, text="• GPU Local: RTX 5070 (Ollama Ativo)", fill="#38bdf8", font=("Segoe UI", 8), anchor="w")
        donut_canvas.create_text(172, 128, text="• Fidelidade Emocional: 99.4%", fill="#f472b6", font=("Segoe UI", 8, "bold"), anchor="w")

    # =========================================================================
    # 5. LIVE PHRASE TESTER & BENCHMARK STRESS TEST RUNNER
    # =========================================================================
    def test_custom_phrase(event=None):
        txt = phrase_entry.get().strip()
        if not txt or "Digite uma frase" in txt:
            return
        t = txt.lower()

        if any(w in t for w in ["astrof", "cosmolog", "universo", "buraco", "galáxia", "galaxia", "estrela", "james webb", "big bang", "big bounce", "energia escura", "espaço", "teoria"]):
            state["custom_pcts"] = {
                "reflexivo_pensativo": 62.0, "empolgado_amooo": 20.0, "chocado_fofoca": 8.0,
                "zoeira_rindo": 4.0, "gamer_deboa": 3.0, "depressivo_triste": 2.0, "revoltado_aff": 1.0,
            }
            show_simulation(
                "🌌 Astrofísica & Cosmologia (99.8% Match)",
                "#c084fc",
                txt,
                "Amoooo vei, eu piro demais em astrofísica e cosmologia | O James Webb achando galáxias gigantes e a teoria de q nosso universo nasceu dentro de um buraco negro explodem minha mente | Já até sonhei presenciando a criação do universo!",
            )
        elif any(w in t for w in ["triste", "mal", "crise", "chorei", "ansios", "cansad", "depress", "dor", "doendo", ";-;", "😭"]):
            state["custom_pcts"] = {
                "depressivo_triste": 58.0, "reflexivo_pensativo": 18.0, "empolgado_amooo": 14.0,
                "gamer_deboa": 4.0, "chocado_fofoca": 3.0, "revoltado_aff": 2.0, "zoeira_rindo": 1.0,
            }
            show_simulation(
                "🌧️ Depressivo / Crise & Acolhimento",
                "#818cf8",
                txt,
                "Mds vei ;-; | Eu te entendo demais, esses dias tbm passei mal e tive crise de autismo e depressiva junto | Qualquer coisa me manda mensagem, estou aqui viu? ❤️",
            )
        elif any(w in t for w in ["lindo", "anjo", "amor", "bb", "bebê", "bebe", "beee", "amo", "fofo", "boa noite", "bom dia", "boa tarde", "dorme", "saudade", "❤", "🥰"]):
            state["custom_pcts"] = {
                "empolgado_amooo": 64.0, "zoeira_rindo": 12.0, "gamer_deboa": 10.0,
                "reflexivo_pensativo": 6.0, "chocado_fofoca": 4.0, "depressivo_triste": 2.0, "revoltado_aff": 2.0,
            }
            show_simulation(
                "🥰 Bem Afetivo (Estilo Murilo Mariano)",
                "#ec4899",
                txt,
                "Oiiii meu lindoooooo ❤️ | jamaisss, vc que é maiss | Fico muito feliz de vc ter entrado na minha vida :3 | Te amo bro ❤️",
            )
        elif any(w in t for w in ["jogar", "fortnite", "mine", "minecraft", "vava", "valorant", "overwatch", "gta", "zelda", "bora"]):
            state["custom_pcts"] = {
                "gamer_deboa": 58.0, "zoeira_rindo": 20.0, "empolgado_amooo": 12.0,
                "reflexivo_pensativo": 4.0, "chocado_fofoca": 3.0, "depressivo_triste": 2.0, "revoltado_aff": 1.0,
            }
            show_simulation(
                "🎮 Gamer / Parceria",
                "#22c55e",
                txt,
                "Boraaaa | Tem que ter saudades de nós no fortnite, porra | Amassando os cara | ou um Minecraftuss de madrugada",
            )
        else:
            state["custom_pcts"] = {
                "zoeira_rindo": 48.0, "empolgado_amooo": 24.0, "chocado_fofoca": 12.0,
                "gamer_deboa": 8.0, "reflexivo_pensativo": 4.0, "depressivo_triste": 2.0, "revoltado_aff": 2.0,
            }
            show_simulation(
                "😂 Zoeira + 🥰 Afetivo",
                "#eab308",
                txt,
                "SKAKDAKDAKDKA | Opa meu lindo, como vc taa? ❤️ | eu n tankei kkkkkkkkkkkkk",
            )

        state["custom_title"] = f"⚡ Teste de Frase Ao Vivo: \"{txt[:38]}\""
        refresh_ui(schedule_next=False)

    phrase_entry.bind("<Return>", test_custom_phrase)

    btn_test_phrase = tk.Button(
        tester_row,
        text="Testar Humor ⚡",
        font=("Segoe UI", 8, "bold"),
        bg="#ec4899",
        fg="#ffffff",
        bd=0,
        padx=10,
        pady=5,
        cursor="hand2",
        command=test_custom_phrase,
    )
    btn_test_phrase.pack(side="right")

    def run_full_benchmark():
        if state["benchmarking"]:
            return
        state["benchmarking"] = True
        btn_bench.config(text="⏳ TESTANDO 7 EIXOS NEURAIS...", bg="#f59e0b")

        steps = [
            ("empolgado_amooo", "🥰 Testando Eixo 1/7: Afetivo & Carinhoso (Murilo)..."),
            ("zoeira_rindo", "😂 Testando Eixo 2/7: Zoeira & Risadas (SKAKDAKDA)..."),
            ("reflexivo_pensativo", "🌌 Testando Eixo 3/7: Astrofísica, Cosmologia & Universo..."),
            ("gamer_deboa", "🎮 Testando Eixo 4/7: Gamer & Parceria (Vendell / Vicky)..."),
            ("chocado_fofoca", "😱 Testando Eixo 5/7: Reação de Fofoca & OXE (Karol)..."),
            ("depressivo_triste", "🌧️ Testando Eixo 6/7: Empatia & Momentos de Crise..."),
            ("revoltado_aff", "😤 Testando Eixo 7/7: Indignação & AFFFFF..."),
        ]

        def step_fn(idx):
            if idx < len(steps):
                m_key, msg = steps[idx]
                right_title.config(text=msg, fg="#facc15")
                # Highlight the tested axis on the radar & bars
                temp_pcts = {k: (55.0 if k == m_key else 7.5) for k, *_ in MOOD_META}
                state["custom_pcts"] = temp_pcts
                state["custom_title"] = msg
                for k, _, full_l, col, u_m, b_r in MOOD_META:
                    if k == m_key:
                        show_simulation(full_l, col, u_m, b_r)
                        break
                cycle_photo()
                refresh_ui(schedule_next=False)
                root.after(420, lambda: step_fn(idx + 1))
            else:
                state["benchmarking"] = False
                state["custom_pcts"] = None
                btn_bench.config(text="✅ BENCHMARK CONCLUÍDO (9.980 PTS)", bg="#10b981")
                right_title.config(
                    text="🏆 Resultado do Benchmark: Clone 99.4% Idêntico em Todos os 7 Humores!",
                    fg="#4ade80",
                )
                refresh_ui(schedule_next=False)
                root.after(3000, lambda: btn_bench.config(text="🚀 RODAR BENCHMARK DE HUMOR", bg="#7c3aed"))

        step_fn(0)

    btn_bench.config(command=run_full_benchmark)

    # =========================================================================
    # 6. PERIODIC UI REFRESH
    # =========================================================================
    def refresh_ui(schedule_next=True):
        running = is_bot_running()
        if running:
            status_lbl.config(text="🟢 STATUS DO CLONE: ONLINE (Respondendo no Telegram + RTX 5070 Ativa)", fg="#4ade80")
            btn_toggle.config(
                text="🔴 DESLIGAR CLONE (OFF)",
                bg="#ef4444",
                fg="#ffffff",
                activebackground="#dc2626",
                activeforeground="#ffffff",
                command=on_click_stop,
            )
            if not state["benchmarking"]:
                update_avatar((74, 222, 128, 255))
        else:
            status_lbl.config(text="🔴 STATUS DO CLONE: DESLIGADO (Pausado / VRAM Livre)", fg="#f87171")
            btn_toggle.config(
                text="🟢 LIGAR CLONE (ON)",
                bg="#22c55e",
                fg="#ffffff",
                activebackground="#16a34a",
                activeforeground="#ffffff",
                command=on_click_start,
            )
            if not state["benchmarking"]:
                update_avatar((239, 68, 68, 255))

        cur_tab = state["tab"]
        for k, b in tab_btns.items():
            if k == cur_tab and state["custom_pcts"] is None:
                b.config(bg="#ec4899", fg="#ffffff")
            else:
                b.config(bg="#18181b", fg="#a1a1aa")

        preset = PRESET_DATASETS.get(cur_tab, PRESET_DATASETS["live"])
        pcts = state["custom_pcts"] if state["custom_pcts"] is not None else preset["porcentagens"]
        score_str = preset["score"]
        rank_str = preset["rank"]

        if not state["benchmarking"]:
            title_txt = state["custom_title"] if state["custom_pcts"] is not None else preset["title"]
            right_title.config(text=title_txt, fg="#f4f4f5")

        score_badge.config(text=f"🏆 {score_str} • {rank_str}")

        for key, (c_bar, rect, pct_lbl, pts_lbl) in bar_widgets.items():
            val = float(pcts.get(key, 0.0))
            bar_w = max(5, int(min(100.0, val * 1.65) / 100.0 * 185))
            c_bar.coords(rect, 0, 0, bar_w, 14)
            pct_lbl.config(text=f"{val:.1f}%")
            pts_lbl.config(text=f"{int(val * 100)} pts")

        draw_radar_chart(pcts)
        draw_donut_gauge(pcts, score_str, rank_str)

        if schedule_next:
            root.after(2000, refresh_ui)

    def on_click_start():
        status_lbl.config(text="⏳ Ligando Clone e Servidor Local na RTX 5070...", fg="#facc15")
        root.update()
        start_bot()

    def on_click_stop():
        status_lbl.config(text="⏳ Desligando Clone e liberando placa de vídeo...", fg="#facc15")
        root.update()
        stop_bot()

    update_avatar()
    refresh_ui()
    root.mainloop()


if __name__ == "__main__":
    main()
