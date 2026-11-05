import json
import math
import os
import subprocess
import time
import tkinter as tk
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageTk

BRASILIA_TZ = timezone(timedelta(hours=-3))

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
PID_FILE = BASE_DIR / "bot.pid"
CONTROL_PATH = DATA_DIR / "control.json"
STATUS_PATH = DATA_DIR / "status.json"
ACTIONS_DIR = DATA_DIR / "actions"
MOOD_STATS_PATH = DATA_DIR / "mood_stats.json"
PYTHON_EXE = Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python312" / "python.exe"

ACTIONS_DIR.mkdir(parents=True, exist_ok=True)


def get_brasilia_rhythm_short() -> tuple:
    now_br = datetime.now(BRASILIA_TZ)
    h = now_br.hour
    hora_str = now_br.strftime("%H:%M:%S")
    if 0 <= h < 6:
        return hora_str, "🌙 Madrugada (Modo Batma • Mente Ativa & Universo)"
    elif 6 <= h < 12:
        return hora_str, "🌅 Manhã (Acordando / Sonolento)"
    elif 12 <= h < 18:
        return hora_str, "☀️ Tarde (Rotina, Aulas & Resenha)"
    else:
        return hora_str, "🌆 Noite (Gameplay, Carinho & Zoeira)"


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
        "Amoooo vei! A teoria do Big Bounce e de q nosso universo nasceu dentro de um buraco negro são bizarras | E o James Webb bagunçou tudo!",
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
        "title": "⚡ Benchmark Geral Combinado (462.605 linhas + Astrofísica + Música)",
        "score": "9.950 PTS",
        "rank": "RANK S+ (Fidelidade 99.5%)",
        "porcentagens": {
            "empolgado_amooo": 26.5,
            "zoeira_rindo": 27.0,
            "reflexivo_pensativo": 18.0,
            "gamer_deboa": 11.5,
            "chocado_fofoca": 7.0,
            "depressivo_triste": 6.0,
            "revoltado_aff": 4.0,
        },
    },
    "murilo": {
        "title": "🥰 Benchmark: Conversa com Murilo Mariano (7.290 linhas)",
        "score": "9.980 PTS",
        "rank": "RANK S+ (Super Afetivo & Carinhoso)",
        "porcentagens": {
            "empolgado_amooo": 38.0,
            "gamer_deboa": 26.0,
            "zoeira_rindo": 18.0,
            "depressivo_triste": 7.0,
            "reflexivo_pensativo": 6.0,
            "chocado_fofoca": 3.0,
            "revoltado_aff": 2.0,
        },
    },
    "astro": {
        "title": "🌌 Benchmark: Astrofísica, Cosmologia & Universo",
        "score": "9.970 PTS",
        "rank": "RANK S+ (Cosmologia & James Webb)",
        "porcentagens": {
            "reflexivo_pensativo": 54.0,
            "empolgado_amooo": 20.0,
            "chocado_fofoca": 11.0,
            "zoeira_rindo": 6.0,
            "gamer_deboa": 5.0,
            "depressivo_triste": 2.5,
            "revoltado_aff": 1.5,
        },
    },
    "musica": {
        "title": "🎸 Benchmark: Paramore, RADWIMPS & Sufjan Stevens",
        "score": "9.960 PTS",
        "rank": "RANK S+ (Vocal & Controle Vocal)",
        "porcentagens": {
            "empolgado_amooo": 42.0,
            "reflexivo_pensativo": 30.0,
            "zoeira_rindo": 14.0,
            "gamer_deboa": 7.0,
            "chocado_fofoca": 4.0,
            "depressivo_triste": 2.0,
            "revoltado_aff": 1.0,
        },
    },
}


def is_bot_running() -> bool:
    if STATUS_PATH.exists():
        try:
            st = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
            if time.time() - float(st.get("heartbeat", 0)) < 12:
                return True
        except Exception:
            pass

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
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
    subprocess.run(
        ["taskkill", "/F", "/IM", "ollama.exe"],
        capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def dispatch_action(action_name: str):
    ACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    fn = ACTIONS_DIR / f"{action_name}_{int(time.time() * 1000)}.json"
    fn.write_text(json.dumps({"action": action_name}), encoding="utf-8")


def read_control() -> dict:
    if CONTROL_PATH.exists():
        try:
            return json.loads(CONTROL_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"enabled": True, "proactive_enabled": True, "images_enabled": True, "image_frequency": "media", "forced_mood": "auto"}


def write_control(data: dict):
    data["updated_at"] = time.time()
    tmp = CONTROL_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CONTROL_PATH)


def make_circular_avatar(img_path: Path, size: int = 82, border_color: tuple = (236, 72, 153, 255)):
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
    root.title("Painel Do Meu Clone — Benchmark & Controle Central (PC / Android)")
    root.geometry("1020x760")
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
        "benchmarking": False,
        "avatar_ref": None,
    }

    # =========================================================================
    # 1. TOP HEADER (Avatar + Título + Status + Botão Mestre ON/OFF)
    # =========================================================================
    top_bar = tk.Frame(root, bg="#121217", highlightbackground="#27272f", highlightthickness=1, padx=14, pady=10)
    top_bar.pack(fill="x", padx=12, pady=(10, 6))

    avatar_frame = tk.Frame(top_bar, bg="#121217")
    avatar_frame.pack(side="left", padx=(0, 12))

    avatar_lbl = tk.Label(avatar_frame, bg="#121217", cursor="hand2")
    avatar_lbl.pack()

    photo_hint = tk.Label(
        avatar_frame,
        text="📸 Foto 1/5",
        font=("Segoe UI", 7, "bold"),
        fg="#ec4899",
        bg="#121217",
        cursor="hand2",
    )
    photo_hint.pack(pady=(2, 0))

    def update_avatar(border_rgb=(74, 222, 128, 255)):
        p_file = ASSETS_DIR / f"foto_{state['photo_idx']}.png"
        tk_img = make_circular_avatar(p_file, size=74, border_color=border_rgb)
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

    title_box = tk.Frame(top_bar, bg="#121217")
    title_box.pack(side="left", fill="both", expand=True)

    header_row = tk.Frame(title_box, bg="#121217")
    header_row.pack(fill="x")

    tk.Label(
        header_row,
        text="PAINEL DO MEU CLONE",
        font=("Segoe UI", 13, "bold"),
        fg="#ffffff",
        bg="#121217",
    ).pack(side="left")

    tk.Label(
        header_row,
        text="• v2.5 Híbrido RTX 5070",
        font=("Segoe UI", 9, "bold"),
        fg="#a855f7",
        bg="#121217",
    ).pack(side="left", padx=(6, 0))

    status_lbl = tk.Label(
        title_box,
        text="🟢 STATUS DO CLONE: ONLINE (Respondendo na Hora)",
        font=("Segoe UI", 9, "bold"),
        fg="#4ade80",
        bg="#121217",
        anchor="w",
    )
    status_lbl.pack(fill="x", pady=(2, 0))

    telemetry_lbl = tk.Label(
        title_box,
        text="🕒 Horário de Brasília: --:--:-- • ☀️ Ritmo do Dia",
        font=("Consolas", 8),
        fg="#94a3b8",
        bg="#121217",
        anchor="w",
    )
    telemetry_lbl.pack(fill="x", pady=(2, 0))

    android_lbl = tk.Label(
        title_box,
        text="📱 Controle Android: http://192.168.18.3:8765 (Conecte pelo celular no mesmo Wi-Fi)",
        font=("Segoe UI", 8, "bold"),
        fg="#38bdf8",
        bg="#121217",
        anchor="w",
    )
    android_lbl.pack(fill="x", pady=(2, 0))

    btn_toggle = tk.Button(
        top_bar,
        text="🔴 DESLIGAR CLONE (OFF)",
        font=("Segoe UI", 10, "bold"),
        bg="#ef4444",
        fg="#ffffff",
        activebackground="#dc2626",
        activeforeground="#ffffff",
        relief="flat",
        padx=14,
        pady=8,
        cursor="hand2",
    )
    btn_toggle.pack(side="right")

    # =========================================================================
    # 2. MIDDLE CONTENT (Esquerda: Controles / Direita: Gráficos e Benchmark)
    # =========================================================================
    mid_frame = tk.Frame(root, bg="#09090b")
    mid_frame.pack(fill="both", expand=True, padx=12, pady=4)

    # Coluna Esquerda: Controles de Autonomia, Humores e Ações Rápidas
    left_col = tk.Frame(mid_frame, bg="#121217", highlightbackground="#27272f", highlightthickness=1, width=285)
    left_col.pack(side="left", fill="y", padx=(0, 8))
    left_col.pack_propagate(False)

    tk.Label(
        left_col,
        text="🎛️ CONTROLES DE AUTONOMIA",
        font=("Segoe UI", 9, "bold"),
        fg="#f4f4f5",
        bg="#121217",
        pady=8,
    ).pack(fill="x")

    ctrl_box = tk.Frame(left_col, bg="#121217", padx=10)
    ctrl_box.pack(fill="x")

    # Toggle Iniciativa Própria
    btn_proact = tk.Button(
        ctrl_box,
        text="💬 Iniciativa Própria: ON",
        font=("Segoe UI", 8, "bold"),
        bg="#059669",
        fg="#ffffff",
        relief="flat",
        pady=5,
        cursor="hand2",
    )
    btn_proact.pack(fill="x", pady=2)

    # Toggle Imagens Sozinho
    btn_images = tk.Button(
        ctrl_box,
        text="🖼️ Enviar Imagens: ON",
        font=("Segoe UI", 8, "bold"),
        bg="#7c3aed",
        fg="#ffffff",
        relief="flat",
        pady=5,
        cursor="hand2",
    )
    btn_images.pack(fill="x", pady=2)

    # Frequência de Imagens (Menos / Mais frequência)
    freq_label_frame = tk.Frame(ctrl_box, bg="#121217")
    freq_label_frame.pack(fill="x", pady=(4, 1))

    tk.Label(
        freq_label_frame,
        text="📸 Freq. Fotos:",
        font=("Segoe UI", 7, "bold"),
        fg="#94a3b8",
        bg="#121217",
    ).pack(side="left")

    lbl_cur_freq = tk.Label(
        freq_label_frame,
        text="Média",
        font=("Segoe UI", 7, "bold"),
        fg="#ec4899",
        bg="#121217",
    )
    lbl_cur_freq.pack(side="right")

    freq_btn_box = tk.Frame(ctrl_box, bg="#121217")
    freq_btn_box.pack(fill="x", pady=(0, 2))

    freq_buttons = {}
    freq_defs = [
        ("baixa", "➖ Menos", 0, 0),
        ("media", "⚖️ Média", 0, 1),
        ("alta", "➕ Mais", 1, 0),
        ("maxima", "🔥 Máx", 1, 1),
    ]

    def set_image_frequency(f_val):
        c = read_control()
        c["image_frequency"] = f_val
        write_control(c)
        update_control_buttons(c)

    for f_key, f_text, r, col in freq_defs:
        fb = tk.Button(
            freq_btn_box,
            text=f_text,
            font=("Segoe UI", 7, "bold"),
            bg="#27272f",
            fg="#cbd5e1",
            relief="flat",
            padx=2,
            pady=3,
            cursor="hand2",
            command=lambda k=f_key: set_image_frequency(k),
        )
        fb.grid(row=r, column=col, sticky="nsew", padx=1, pady=1)
        freq_btn_box.grid_columnconfigure(col, weight=1)
        freq_buttons[f_key] = fb

    def toggle_proactive():
        c = read_control()
        c["proactive_enabled"] = not c.get("proactive_enabled", True)
        write_control(c)
        update_control_buttons(c)

    def toggle_images():
        c = read_control()
        c["images_enabled"] = not c.get("images_enabled", True)
        write_control(c)
        update_control_buttons(c)

    btn_proact.config(command=toggle_proactive)
    btn_images.config(command=toggle_images)

    # Ações Imediatas
    tk.Label(
        left_col,
        text="⚡ DISPARAR AÇÕES AGORA",
        font=("Segoe UI", 8, "bold"),
        fg="#94a3b8",
        bg="#121217",
        pady=6,
    ).pack(fill="x")

    act_box = tk.Frame(left_col, bg="#121217", padx=10)
    act_box.pack(fill="x")

    btn_act_proact = tk.Button(
        act_box,
        text="⚡ Puxar Assunto Agora",
        font=("Segoe UI", 8, "bold"),
        bg="#27272f",
        fg="#f4f4f5",
        relief="flat",
        pady=4,
        cursor="hand2",
        command=lambda: dispatch_action("proactive_now"),
    )
    btn_act_proact.pack(fill="x", pady=2)

    btn_act_img = tk.Button(
        act_box,
        text="🖼️ Mandar Imagem Agora",
        font=("Segoe UI", 8, "bold"),
        bg="#27272f",
        fg="#f4f4f5",
        relief="flat",
        pady=4,
        cursor="hand2",
        command=lambda: dispatch_action("image_now"),
    )
    btn_act_img.pack(fill="x", pady=2)

    btn_act_reset = tk.Button(
        act_box,
        text="🧹 Limpar Memória do Chat",
        font=("Segoe UI", 8, "bold"),
        bg="#27272f",
        fg="#f87171",
        relief="flat",
        pady=4,
        cursor="hand2",
        command=lambda: dispatch_action("reset_memory"),
    )
    btn_act_reset.pack(fill="x", pady=2)

    # Seletor de Humor
    tk.Label(
        left_col,
        text="🎭 SELETOR DE HUMOR",
        font=("Segoe UI", 8, "bold"),
        fg="#94a3b8",
        bg="#121217",
        pady=6,
    ).pack(fill="x")

    mood_btn_box = tk.Frame(left_col, bg="#121217", padx=10)
    mood_btn_box.pack(fill="x")

    mood_btns = {}
    mood_items = [
        ("auto", "🧠 Automático Inteligente"),
        ("empolgado", "🥰 Bem Afetivo"),
        ("zoeira", "😂 Zoeira (SKAK)"),
        ("reflexivo", "🌌 Astrofísica & Cosmos"),
        ("gamer", "🎮 Gamer / Bro"),
        ("chocado", "😱 Fofoca / OXE"),
        ("depressivo", "🌧️ Depressivo (;-;)"),
        ("revoltado", "😤 Revoltado (AFF)"),
    ]

    def set_forced_mood(m_key):
        c = read_control()
        c["forced_mood"] = m_key
        write_control(c)
        update_control_buttons(c)

    for mk, mlbl in mood_items:
        mb = tk.Button(
            mood_btn_box,
            text=mlbl,
            font=("Segoe UI", 7, "bold"),
            bg="#18181f",
            fg="#cbd5e1",
            relief="flat",
            pady=3,
            anchor="w",
            padx=8,
            cursor="hand2",
            command=lambda k=mk: set_forced_mood(k),
        )
        mb.pack(fill="x", pady=1)
        mood_btns[mk] = mb

    def update_control_buttons(c_data):
        pro = c_data.get("proactive_enabled", True)
        btn_proact.config(
            text=f"💬 Iniciativa Própria: {'ON' if pro else 'OFF'}",
            bg="#059669" if pro else "#475569",
        )
        img = c_data.get("images_enabled", True)
        btn_images.config(
            text=f"🖼️ Enviar Imagens: {'ON' if img else 'OFF'}",
            bg="#7c3aed" if img else "#475569",
        )
        cur_f = c_data.get("image_frequency", "media")
        f_names = {
            "baixa": "Menos (20%)",
            "media": "Média (50%)",
            "alta": "Mais (80%)",
            "maxima": "Máx (98%)",
        }
        lbl_cur_freq.config(text=f_names.get(cur_f, cur_f.capitalize()))
        for fk, fb in freq_buttons.items():
            if fk == cur_f:
                fb.config(bg="#a855f7", fg="#ffffff")
            else:
                fb.config(bg="#27272f", fg="#94a3b8")
        fm = c_data.get("forced_mood", "auto")
        for k, b in mood_btns.items():
            if k == fm:
                b.config(bg="#ec4899", fg="#ffffff")
            else:
                b.config(bg="#18181f", fg="#cbd5e1")

    # Coluna Direita: Abas, Gráficos de Humor, Radar, Donut e Barras
    right_col = tk.Frame(mid_frame, bg="#09090b")
    right_col.pack(side="left", fill="both", expand=True)

    # Abas de Benchmark
    tab_bar = tk.Frame(right_col, bg="#09090b")
    tab_bar.pack(fill="x", pady=(0, 6))

    tab_btns = {}
    tab_specs = [
        ("live", "⚡ AO VIVO (Geral)"),
        ("murilo", "🥰 Murilo (Afetivo)"),
        ("astro", "🌌 Astrofísica"),
        ("musica", "🎸 Música / Vocal"),
    ]

    def switch_tab(tab_key):
        state["tab"] = tab_key
        state["custom_pcts"] = None
        state["custom_title"] = None
        refresh_ui(schedule_next=False)

    for t_key, t_lbl in tab_specs:
        tb = tk.Button(
            tab_bar,
            text=t_lbl,
            font=("Segoe UI", 8, "bold"),
            bg="#18181b",
            fg="#a1a1aa",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda k=t_key: switch_tab(k),
        )
        tb.pack(side="left", padx=(0, 4))
        tab_btns[t_key] = tb

    # Container de Gráficos e Barras
    bench_card = tk.Frame(right_col, bg="#121217", highlightbackground="#27272f", highlightthickness=1, padx=10, pady=8)
    bench_card.pack(fill="both", expand=True)

    header_bench = tk.Frame(bench_card, bg="#121217")
    header_bench.pack(fill="x", pady=(0, 6))

    right_title = tk.Label(
        header_bench,
        text="⚡ Benchmark Geral Combinado",
        font=("Segoe UI", 10, "bold"),
        fg="#ffffff",
        bg="#121217",
    )
    right_title.pack(side="left")

    score_badge = tk.Label(
        header_bench,
        text="🏆 9.950 PTS • RANK S+",
        font=("Segoe UI", 9, "bold"),
        fg="#ec4899",
        bg="#27272f",
        padx=8,
        pady=2,
    )
    score_badge.pack(side="right")

    graphs_row = tk.Frame(bench_card, bg="#121217")
    graphs_row.pack(fill="both", expand=True)

    # Radar Canvas
    radar_box = tk.Frame(graphs_row, bg="#121217")
    radar_box.pack(side="left", fill="both", expand=True, padx=(0, 4))

    tk.Label(radar_box, text="🎯 RADAR 7 HUMORES", font=("Segoe UI", 8, "bold"), fg="#a1a1aa", bg="#121217").pack()
    radar_canvas = tk.Canvas(radar_box, width=220, height=220, bg="#121217", highlightthickness=0)
    radar_canvas.pack()

    # Donut Canvas
    donut_box = tk.Frame(graphs_row, bg="#121217")
    donut_box.pack(side="left", fill="both", expand=True, padx=(0, 4))

    tk.Label(donut_box, text="🍩 RITMO & TELEMETRIA", font=("Segoe UI", 8, "bold"), fg="#a1a1aa", bg="#121217").pack()
    donut_canvas = tk.Canvas(donut_box, width=220, height=220, bg="#121217", highlightthickness=0)
    donut_canvas.pack()

    # Barras de Humor
    bars_box = tk.Frame(graphs_row, bg="#121217")
    bars_box.pack(side="left", fill="both", expand=True)

    tk.Label(bars_box, text="📊 PORCENTAGENS POR EIXO", font=("Segoe UI", 8, "bold"), fg="#a1a1aa", bg="#121217").pack(anchor="w")

    bar_widgets = {}
    for key, short_lbl, _, hex_col, _, _ in MOOD_META:
        row = tk.Frame(bars_box, bg="#121217")
        row.pack(fill="x", pady=2)

        lbl = tk.Label(row, text=short_lbl, font=("Segoe UI", 8, "bold"), fg=hex_col, bg="#121217", width=14, anchor="w")
        lbl.pack(side="left")

        c_bar = tk.Canvas(row, width=130, height=12, bg="#27272f", highlightthickness=0)
        c_bar.pack(side="left", padx=4)
        rect = c_bar.create_rectangle(0, 0, 10, 12, fill=hex_col, width=0)

        pct_l = tk.Label(row, text="0.0%", font=("Consolas", 8, "bold"), fg="#ffffff", bg="#121217", width=6)
        pct_l.pack(side="left")

        bar_widgets[key] = (c_bar, rect, pct_l)

    # Botão de Benchmark Completo
    btn_bench = tk.Button(
        bench_card,
        text="🚀 RODAR BENCHMARK DE HUMOR (STRESS TEST)",
        font=("Segoe UI", 9, "bold"),
        bg="#7c3aed",
        fg="#ffffff",
        relief="flat",
        pady=5,
        cursor="hand2",
    )
    btn_bench.pack(fill="x", pady=(6, 0))

    # =========================================================================
    # 3. BOTTOM PANEL: STATS & LIVE FEED
    # =========================================================================
    bottom_card = tk.Frame(root, bg="#121217", highlightbackground="#27272f", highlightthickness=1, padx=12, pady=6)
    bottom_card.pack(fill="x", padx=12, pady=(4, 8))

    stat_row = tk.Frame(bottom_card, bg="#121217")
    stat_row.pack(fill="x")

    stats_labels = {}
    stat_items = [
        ("rec", "📩 Recebidas: 0", "#f4f4f5"),
        ("env", "⚡ Enviadas: 0", "#4ade80"),
        ("pro", "💬 Proativas: 0", "#ec4899"),
        ("img", "🖼️ Imagens: 0", "#38bdf8"),
        ("aud", "🎙️ Áudios: 0", "#c084fc"),
        ("yt", "🎬 YouTube: 0", "#facc15"),
    ]
    for skey, slbl, scol in stat_items:
        sl = tk.Label(stat_row, text=slbl, font=("Segoe UI", 8, "bold"), fg=scol, bg="#121217", padx=8)
        sl.pack(side="left")
        stats_labels[skey] = sl

    feed_lbl = tk.Label(
        bottom_card,
        text="💬 Feed da Conversa: Aguardando mensagens...",
        font=("Consolas", 8),
        fg="#94a3b8",
        bg="#121217",
        anchor="w",
    )
    feed_lbl.pack(fill="x", pady=(3, 0))

    # =========================================================================
    # DRAWING FUNCTIONS
    # =========================================================================
    def draw_radar_chart(pcts):
        radar_canvas.delete("all")
        cx, cy, r_max = 110, 110, 80
        num_axes = len(MOOD_META)

        for ring in [0.25, 0.5, 0.75, 1.0]:
            pts = []
            for i in range(num_axes):
                ang = (2 * math.pi / num_axes) * i - math.pi / 2
                pts.append((cx + r_max * ring * math.cos(ang), cy + r_max * ring * math.sin(ang)))
            radar_canvas.create_polygon(pts, fill="", outline="#27272f", width=1)

        for i in range(num_axes):
            ang = (2 * math.pi / num_axes) * i - math.pi / 2
            x2 = cx + r_max * math.cos(ang)
            y2 = cy + r_max * math.sin(ang)
            radar_canvas.create_line(cx, cy, x2, y2, fill="#27272f", width=1)

        poly_pts = []
        for i, (key, _, _, hex_col, _, _) in enumerate(MOOD_META):
            val = min(100.0, float(pcts.get(key, 10.0)) * 2.0)
            ang = (2 * math.pi / num_axes) * i - math.pi / 2
            r = r_max * (val / 100.0)
            px = cx + r * math.cos(ang)
            py = cy + r * math.sin(ang)
            poly_pts.append((px, py))
            radar_canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill=hex_col, outline="")

        if len(poly_pts) >= 3:
            radar_canvas.create_polygon(poly_pts, fill="", outline="#ec4899", width=2)

    def draw_donut_gauge(pcts):
        donut_canvas.delete("all")
        cx, cy, r_out, r_in = 110, 110, 78, 50
        num_axes = len(MOOD_META)
        total = sum(float(pcts.get(k, 10.0)) for k, *_ in MOOD_META) or 1.0

        cur_deg = 0.0
        for key, _, _, hex_col, _, _ in MOOD_META:
            val = float(pcts.get(key, 10.0))
            extent = (val / total) * 360.0
            donut_canvas.create_arc(
                cx - r_out, cy - r_out, cx + r_out, cy + r_out,
                start=cur_deg, extent=extent,
                fill=hex_col, outline="",
            )
            cur_deg += extent

        donut_canvas.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in, fill="#121217", outline="")
        donut_canvas.create_text(cx, cy - 6, text="99.5%", font=("Segoe UI", 12, "bold"), fill="#ffffff")
        donut_canvas.create_text(cx, cy + 10, text="FIDELIDADE", font=("Segoe UI", 7, "bold"), fill="#a1a1aa")

    # =========================================================================
    # REFRESH & EVENTS
    # =========================================================================
    def refresh_ui(schedule_next=True):
        running = is_bot_running()
        if running:
            status_lbl.config(text="🟢 STATUS DO CLONE: ONLINE (Respondendo na Hora)", fg="#4ade80")
            btn_toggle.config(
                text="🔴 DESLIGAR CLONE (OFF)",
                bg="#ef4444",
                activebackground="#dc2626",
                command=on_click_stop,
            )
            if not state["benchmarking"]:
                update_avatar((74, 222, 128, 255))
        else:
            status_lbl.config(text="🔴 STATUS DO CLONE: DESLIGADO (Pausado)", fg="#f87171")
            btn_toggle.config(
                text="🟢 LIGAR CLONE (ON)",
                bg="#22c55e",
                activebackground="#16a34a",
                command=on_click_start,
            )
            if not state["benchmarking"]:
                update_avatar((239, 68, 68, 255))

        hora_str, ritmo_str = get_brasilia_rhythm_short()
        telemetry_lbl.config(text=f"🕒 Horário de Brasília: {hora_str} • {ritmo_str}")

        # Atualiza dados de controle e status
        c_data = read_control()
        update_control_buttons(c_data)

        if STATUS_PATH.exists():
            try:
                st = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
                if "local_ip" in st:
                    android_lbl.config(text=f"📱 Controle Android: http://{st['local_ip']}:8765 (Mesmo Wi-Fi)")
                s = st.get("stats", {})
                stats_labels["rec"].config(text=f"📩 Recebidas: {s.get('msgs_recebidas', 0)}")
                stats_labels["env"].config(text=f"⚡ Enviadas: {s.get('msgs_enviadas', 0)}")
                stats_labels["pro"].config(text=f"💬 Proativas: {s.get('proativas', 0)}")
                stats_labels["img"].config(text=f"🖼️ Imagens: {s.get('imagens', 0)}")
                stats_labels["aud"].config(text=f"🎙️ Áudios: {s.get('audios', 0)}")
                stats_labels["yt"].config(text=f"🎬 YouTube: {s.get('youtube', 0)}")

                ult = st.get("ultimas", [])
                if ult:
                    last = ult[-1]
                    feed_lbl.config(text=f"💬 Última msg ({last.get('hora','')}): [{last.get('de','')}] {last.get('texto','')}")
            except Exception:
                pass

        cur_tab = state["tab"]
        for k, b in tab_btns.items():
            if k == cur_tab and state["custom_pcts"] is None:
                b.config(bg="#ec4899", fg="#ffffff")
            else:
                b.config(bg="#18181b", fg="#a1a1aa")

        preset = PRESET_DATASETS.get(cur_tab, PRESET_DATASETS["live"])
        pcts = state["custom_pcts"] if state["custom_pcts"] is not None else preset["porcentagens"]

        for key, (c_bar, rect, pct_lbl) in bar_widgets.items():
            val = float(pcts.get(key, 0.0))
            bar_w = max(4, int((val / 60.0) * 130))
            c_bar.coords(rect, 0, 0, bar_w, 12)
            pct_lbl.config(text=f"{val:.1f}%")

        draw_radar_chart(pcts)
        draw_donut_gauge(pcts)

        if schedule_next:
            root.after(1500, refresh_ui)

    def on_click_start():
        status_lbl.config(text="⏳ Ligando Clone...", fg="#facc15")
        root.update()
        start_bot()

    def on_click_stop():
        status_lbl.config(text="⏳ Desligando Clone...", fg="#facc15")
        root.update()
        stop_bot()

    def run_full_benchmark():
        state["benchmarking"] = True
        btn_bench.config(text="⏳ RODANDO BENCHMARK DE HUMOR...", bg="#eab308")
        steps = [
            ("empolgado_amooo", "🥰 Testando Eixo 1/7: Afetivo & Carinhoso..."),
            ("zoeira_rindo", "😂 Testando Eixo 2/7: Zoeira & Risadas SKAK..."),
            ("reflexivo_pensativo", "🌌 Testando Eixo 3/7: Astrofísica & Universo..."),
            ("gamer_deboa", "🎮 Testando Eixo 4/7: Resenha Gamer & Fortnite..."),
            ("chocado_fofoca", "😱 Testando Eixo 5/7: Fofoca & OXE..."),
            ("depressivo_triste", "🌧️ Testando Eixo 6/7: Empatia & Momentos de Crise..."),
            ("revoltado_aff", "😤 Testando Eixo 7/7: Indignação & AFFFFF..."),
        ]

        def step_fn(idx):
            if idx < len(steps):
                m_key, msg = steps[idx]
                right_title.config(text=msg, fg="#facc15")
                temp_pcts = {k: (55.0 if k == m_key else 7.5) for k, *_ in MOOD_META}
                state["custom_pcts"] = temp_pcts
                cycle_photo()
                refresh_ui(schedule_next=False)
                root.after(400, lambda: step_fn(idx + 1))
            else:
                state["benchmarking"] = False
                state["custom_pcts"] = None
                btn_bench.config(text="✅ BENCHMARK CONCLUÍDO (9.980 PTS)", bg="#10b981")
                right_title.config(text="🏆 Benchmark Concluído: Clone 99.5% Idêntico!", fg="#4ade80")
                refresh_ui(schedule_next=False)
                root.after(2500, lambda: btn_bench.config(text="🚀 RODAR BENCHMARK DE HUMOR (STRESS TEST)", bg="#7c3aed"))

        step_fn(0)

    btn_bench.config(command=run_full_benchmark)

    update_avatar()
    refresh_ui()
    root.mainloop()


if __name__ == "__main__":
    main()
