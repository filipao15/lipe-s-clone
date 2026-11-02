import asyncio
import json
import os
import random
import re
import subprocess
import sys
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Deque, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

import httpx
import yaml
from dotenv import load_dotenv
from telethon import Button, TelegramClient, events
from telethon.sessions import MemorySession, SQLiteSession

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

PERFIL_PATH = BASE_DIR / "perfil.yaml"
MOOD_BANK_PATH = BASE_DIR / "data" / "mood_bank.json"
CHAT_HISTORY_PATH = BASE_DIR / "data" / "chat_histories.json"
MOOD_STATS_PATH = BASE_DIR / "data" / "mood_stats.json"

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
SESSION_FILE = str(BASE_DIR / os.getenv("TELEGRAM_SESSION_NAME", "bot_clone_contact_session"))

AI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY") or "").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "meu-clone")

DEBOUNCE_SECONDS = float(os.getenv("DEBOUNCE_SECONDS", "0.8"))
PROACTIVE_FIRST_DELAY = float(os.getenv("PROACTIVE_FIRST_DELAY", "45"))
PROACTIVE_NEXT_DELAY = float(os.getenv("PROACTIVE_NEXT_DELAY", "90"))


def calc_human_typing_seconds(text: str) -> float:
    """
    Calcula o tempo real de uma pessoa digitando aquela frase no celular/PC
    (~15 a 18 caracteres por segundo + pequena variação humana).
    """
    char_count = max(1, len(text.strip()))
    base_time = char_count * random.uniform(0.052, 0.068) + random.uniform(0.35, 0.65)
    return min(max(base_time, 1.15), 3.8)

# Diretrizes específicas para cada um dos 7 humores
MOOD_PROFILES: Dict[str, Tuple[str, str]] = {
    "zoeira_rindo": (
        "😂 Zoeira / Rindo",
        "A pessoa está brincando ou falando algo engraçado. Responda de forma divertida, espontânea e bem-humorada, podendo usar suas risadas (como SKAKDAKDAKDKA ou KKKKKKK) se fizer sentido com a piada.",
    ),
    "empolgado_amooo": (
        "🥰 Afetivo / Carinhoso & Empolgado",
        "ATENÇÃO: Seja MUITO AFETIVO, carinhoso, doce e acolhedor (exatamente como você fala com Murilo Mariano)! Use expressões afetuosas reais suas como 'lindo', 'lindãooo', 'meu bb', 'beee', 'meu bem', 'amore', '❤️', '🥰🥰', ':3', ':)))', 'Te amo', 'Qualquer coisa me manda mensagem / Estou aqui, viu? ❤️', 'Eu espero vc meu bem', 'jamaisss / vc é maiss', demonstrando cuidado genuíno e carinho.",
    ),
    "chocado_fofoca": (
        "😱 Chocado / Fofoca",
        "A pessoa está contando um babado, fofoca ou algo surpreendente. Reaja com curiosidade real e surpresa ('Oxe', 'Ixiii', 'Foi como', 'O praisso', 'Mentira'), fazendo perguntas curtas sobre o caso para render o assunto.",
    ),
    "depressivo_triste": (
        "🌧️ Depressivo / Pra Baixo",
        "ATENÇÃO: O momento da conversa é triste, melancólico, cansado, ansioso ou de crise. PROIBIDO rir ('KKKK' / 'SKAKDAK') ou fazer piada! Responda num tom sincero, baixo-astral, vulnerável ou acolhedor, exatamente como você fala quando está mal ou em crise ('Mds', 'To bem nao', 'To em crise', 'Meu corpo todo ta doendo', 'To mt mal vei ;-;', '☹️').",
    ),
    "reflexivo_pensativo": (
        "🌙 Reflexivo / Astrofísica & Universo",
        "ATENÇÃO: A conversa está num momento reflexivo, profundo ou sobre ASTROFÍSICA, COSMOLOGIA E TEORIAS DO UNIVERSO (ou sobre vida, futuro, sonhos vívidos e espiritualidade). Se o assunto for o Universo/Astrofísica/Cosmologia, demonstre sua paixão real pelo tema, comentando teorias modernas (James Webb, Big Bounce, energia escura variável, universo dentro de buraco negro, dilatação do tempo, Paradoxo de Fermi, seu sonho presenciando a criação do universo) no seu jeito autêntico e espontâneo de falar!",
    ),
    "gamer_deboa": (
        "🎮 Gamer / Parceiro (Bro)",
        "A conversa é casual do dia a dia, resenha de parceria ('Opa amigao', 'bro', 'brother', 'Cara tá trajado filho', 'ficou filé', 'O homi tá maiado') ou sobre jogos (Fortnite — 'amassando os cara', Valorant/vava, Overwatch, GTA 6, DBZ Sparking Zero, PS5). Responda de boa, parceiro e direto no assunto.",
    ),
    "revoltado_aff": (
        "😤 Revoltado / Indignado",
        "A pessoa está reclamando de algo chato, injusto ou estressante. Concorde com a indignação dela e desabafe junto no seu estilo ('AFFFFF', 'que infernor', 'Opora', 'Nossa vei que mancada').",
    ),
}

FORCED_MODE_TO_KEY = {
    "zoeira": "zoeira_rindo",
    "reflexivo": "reflexivo_pensativo",
    "depressivo": "depressivo_triste",
    "empolgado": "empolgado_amooo",
    "chocado": "chocado_fofoca",
    "gamer": "gamer_deboa",
    "revoltado": "revoltado_aff",
}


def load_unlocked_session(session_path: str) -> MemorySession:
    sql_sess = SQLiteSession(session_path)
    if sql_sess.auth_key:
        mem_sess = MemorySession()
        mem_sess.set_dc(sql_sess.dc_id, sql_sess.server_address, sql_sess.port)
        mem_sess.auth_key = sql_sess.auth_key
        sql_sess.close()
        return mem_sess
    return sql_sess


def load_mood_bank() -> Dict[str, List[Dict[str, str]]]:
    if MOOD_BANK_PATH.exists():
        try:
            return json.loads(MOOD_BANK_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {}


BRASILIA_TZ = timezone(timedelta(hours=-3))


def get_brasilia_time_context() -> Dict[str, Any]:
    """
    Retorna o horário exato de Brasília (UTC-3) e o ritmo biológico/emocional
    real do Filipe naquele turno do dia (Manhã, Tarde, Noite ou Madrugada).
    """
    now_br = datetime.now(BRASILIA_TZ)
    h = now_br.hour
    hora_str = now_br.strftime("%H:%M")
    dias = [
        "Segunda-feira", "Terça-feira", "Quarta-feira",
        "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"
    ]
    dia_semana = dias[now_br.weekday()]

    if 0 <= h < 6:
        periodo = "🌙 Madrugada (Modo Batma — Mente Ativa)"
        saudacao_natural = "Boa madrugada / Oiiii beee"
        diretriz_horario = (
            f"Agora são {hora_str} da MADRUGADA ({dia_semana}) no Horário de Brasília. "
            "Como você mesmo diz ('Meu cérebro autista num deixa / Minha cabeça funciona melhor de madrugada / batma'), "
            "na madrugada sua mente fica super ativa para conversas profundas, Astrofísica, Cosmologia, teorias do universo, "
            "sonhos bizarros, desabafos sinceros, carinho ('Vou ficar um pouco acordado pra ficar com vc', 'dorme bemm ❤️') "
            "ou virar a noite jogando contra 'os crackudo' antes de tomar seu remédio (clonazepam/neuleptil) quando o olho pesa ('A mimir lkkkk')."
        )
        mood_boosts = {
            "reflexivo_pensativo": 1.4,
            "empolgado_amooo": 1.1,
            "depressivo_triste": 0.8,
            "gamer_deboa": 0.7,
        }
    elif 6 <= h < 12:
        periodo = "🌅 Manhã (Acordando / Sonolento)"
        saudacao_natural = "Bom diaaa / Bom dkaa"
        diretriz_horario = (
            f"Agora são {hora_str} da MANHÃ ({dia_semana}) no Horário de Brasília. "
            "Como você costuma madrugar, de manhã você geralmente tá acordando aos poucos ou meio com sono "
            "('Bom diaaa', 'Acordou agora foi?', 'Eu dormi mucho kkkkk'), falando de boa, carinhoso ('Bom dia lindo ❤️') "
            "ou vendo como tá o dia e cuidando da sua irmãzinha."
        )
        mood_boosts = {
            "empolgado_amooo": 1.0,
            "gamer_deboa": 0.8,
            "reflexivo_pensativo": 0.5,
        }
    elif 12 <= h < 18:
        periodo = "☀️ Tarde (Rotina, Aulas, Praia & Resenha)"
        saudacao_natural = "Boa tarde lindãooo / Opa amigao"
        diretriz_horario = (
            f"Agora são {hora_str} da TARDE ({dia_semana}) no Horário de Brasília. "
            "Você está ativo na rotina da tarde em Salvador: almoçando, dando suas aulas (inglês/computação), "
            "resenhando com os amigos ('Boa tarde lindãooo', 'Opa amigao', 'Oq fez hj de bom?'), comentando fofocas, "
            "músicas que você canta/cria, novidades de jogos ou querendo 'praiar'."
        )
        mood_boosts = {
            "empolgado_amooo": 1.0,
            "zoeira_rindo": 0.9,
            "chocado_fofoca": 0.8,
            "gamer_deboa": 0.8,
        }
    else:
        periodo = "🌆 Noite (Gameplay, Carinho & Zoeira)"
        saudacao_natural = "Boa noiteee / Buenassss"
        diretriz_horario = (
            f"Agora são {hora_str} da NOITE ({dia_semana}) no Horário de Brasília. "
            "É o seu horário clássico de entrar no PC, chamar os amigos pra jogar Fortnite ('amassando os cara'), "
            "Minecraft ('Minecraftuss'), Valorant ('vava') ou Overwatch, ser super afetivo ('Boa noite lindo ❤️', "
            "'Buenassss', 'To aq bbbbb ❤️'), brisar em Astrofísica/Universo ou comentar que a coluna doeu de tanto ficar no PC."
        )
        mood_boosts = {
            "empolgado_amooo": 1.2,
            "gamer_deboa": 1.2,
            "zoeira_rindo": 1.0,
            "reflexivo_pensativo": 0.9,
        }

    return {
        "hora_str": hora_str,
        "dia_semana": dia_semana,
        "periodo": periodo,
        "saudacao_natural": saudacao_natural,
        "diretriz_horario": diretriz_horario,
        "mood_boosts": mood_boosts,
    }


def detect_contextual_mood(
    user_text: str,
    recent_moods: Deque[str],
    forced_mode: str = "auto",
) -> str:
    """
    Analisa de forma inteligente COMO você digitou a mensagem (palavras, pontuação,
    tamanho, emojis, histórico recente E o Horário de Brasília atual) para escolher
    e equilibrar o humor ideal!
    """
    if forced_mode in FORCED_MODE_TO_KEY:
        return FORCED_MODE_TO_KEY[forced_mode]

    t = user_text.lower().strip()
    scores: Dict[str, float] = {
        "zoeira_rindo": 1.0,
        "empolgado_amooo": 1.45,  # Prioridade afetiva e carinhosa (estilo Murilo Mariano)
        "chocado_fofoca": 1.0,
        "depressivo_triste": 1.0,
        "reflexivo_pensativo": 1.25,  # Prioridade para conversas inteligentes/reflexivas e Astrofísica
        "gamer_deboa": 1.15,
        "revoltado_aff": 1.0,
    }

    # Aplica o ritmo biológico do Horário de Brasília (Manhã / Tarde / Noite / Madrugada)
    br_ctx = get_brasilia_time_context()
    for m_key, boost in br_ctx["mood_boosts"].items():
        if m_key in scores:
            scores[m_key] += boost

    # 1. Sinais de Humor Depressivo / Melancólico / Cansado / Crise
    for kw in [
        "triste", "mal", "cansad", "ansios", "sozinh", "chorei", "chorar",
        "depress", "desanim", "vazio", "insônia", "insonia", "crise", "autismo",
        "dor", "doendo", "ruim", ";-;", "☹", "😭", "💔", "😔", "😞", "to bem nao",
        "tô bem não", "n to bem", "passando mal", "desisto", "exausto", "exaustao",
        "devastado", "difícil", "dificil"
    ]:
        if kw in t:
            scores["depressivo_triste"] += 4.5
            scores["reflexivo_pensativo"] += 2.0
            scores["zoeira_rindo"] = 0.0

    # 2. Sinais de Astrofísica, Cosmologia, Universo & Humor Reflexivo / Profundo
    for astro_kw in [
        "astrofísica", "astrofisica", "cosmologia", "universo", "cosmos", "big bang",
        "buraco negro", "buracos negros", "galáxia", "galaxia", "estrela", "planeta",
        "espaço", "espaco", "james webb", "matéria escura", "materia escura",
        "energia escura", "multiverso", "quântica", "quantica", "quântico", "quantico",
        "relatividade", "gravidade", "singularidade", "horizonte de eventos", "entropia",
        "teoria", "teorias", "big bounce", "big freeze", "anos-luz", "fermi", "dimensão"
    ]:
        if astro_kw in t:
            scores["reflexivo_pensativo"] += 6.5

    for kw in [
        "pensando", "pensei", "vida", "futuro", "será", "sera", "sentido",
        "sonho", "sonhei", "mudar", "sair", "salvador", "conselho", "trabalho", "emprego",
        "vaga", "faculdade", "curso", "cabeça", "às vezes", "as vezes", "sinceramente",
        "sei lá", "sla", "acha que", "o que vc acha", "oq vc acha", "entendo",
        "verdade", "tempo", "medo", "decisão", "escolha", "conversar", "papo", "oração"
    ]:
        if kw in t:
            scores["reflexivo_pensativo"] += 3.8

    # Mensagens mais longas sem risadas geralmente são reflexivas ou explicativas
    has_laugh = any(x in t for x in ["kkk", "skak", "sakd", "ksks", "kakak", "haha", "😂"])
    if len(t) > 45 and not has_laugh:
        scores["reflexivo_pensativo"] += 2.8

    # 3. Sinais de Revoltado / Indignado / Rant
    for kw in [
        "aff", "odeio", "ódio", "odio", "raiva", "inferno", "saco", "nojera",
        "opora", "caceta", "lixo", "ranço", "mancada", "chato", "merda",
        "porra", "estresse", "aguento mais", "ridículo", "ridiculo", "absurdo"
    ]:
        if kw in t:
            scores["revoltado_aff"] += 4.2

    # 4. Sinais de Chocado / Fofoca / Curiosidade
    for kw in [
        "oxe", "ixi", "menino", "mulher", "fofoca", "conta", "falei com",
        "tu viu", "cê viu", "ce viu", "nem sabe", "mentira", "chocad",
        "passad", "mds", "querdita", "acredita", "babado", "quem", "sério", "serio"
    ]:
        if kw in t:
            scores["chocado_fofoca"] += 3.6
    if "??" in user_text or "!!" in user_text or (len(user_text) >= 4 and user_text.isupper()):
        scores["chocado_fofoca"] += 2.2

    # 5. Sinais de Gamer / De boa / Cotidiano
    for kw in [
        "jogar", "jg", "vava", "valorant", "overwatch", "moira", "fortnite",
        "minecraft", "mine", "zelda", "gta", "ps5", "dbz", "play", "bora",
        "vamos", "vms", "pc", "notebook", "jogo", "skin", "passe",
        "rank", "diamante", "praia", "filme", "série", "serie", "fazendo oq",
        "tá fazendo", "ta fazendo", "opa", "e ai", "e aí", "bro", "amigao"
    ]:
        if kw in t:
            scores["gamer_deboa"] += 3.5

    # 6. Sinais de Afetivo / Carinhoso / Empolgado & Paixão por Música/Vocal (RADWIMPS & Paramore)
    for music_kw in [
        "radwimps", "paramore", "hayley", "yojiro", "vocal", "controle vocal",
        "cantar", "canto", "cantando", "música", "musica", "banda", "belting",
        "falsete", "alcance vocal", "voz", "afinação", "afinacao", "suzume",
        "sparkle", "zenzenzense", "decode"
    ]:
        if music_kw in t:
            scores["empolgado_amooo"] += 5.5
            scores["reflexivo_pensativo"] += 3.0

    for kw in [
        "amooo", "amo", "te amo", "lindo", "linda", "lindhu", "lindão", "fofo", "fofa",
        "anjo", "meu bem", "bb", "bebê", "bebe", "beee", "amore", "amor", "amigo",
        "irmãozinho", "saudade", "abraço", "carinho", "dorme bem", "durma", "bom sono",
        "bons sonhos", "comprei", "ganhei", "passei", "bom dia", "boa tarde", "boa noite",
        "buenas", "oi", "oii", "tudo bem", "td bem", "como vc ta", "como vc tá",
        "obrigado", "obg", "parabéns", "merece", "delícia", "delicia", "perfeito",
        "pfto", "massa", "gloria", "glória", "❤", "🥺", "💋", "😍", "🥰", "💕", "🥹", ":3"
    ]:
        if kw in t:
            scores["empolgado_amooo"] += 4.2

    # 7. Sinais de Zoeira / Rindo
    if has_laugh:
        scores["zoeira_rindo"] += 3.5
    for kw in ["piada", "meme", "engraçado", "rindo", "tankei"]:
        if kw in t:
            scores["zoeira_rindo"] += 3.0

    # EQUILÍBRIO DINÂMICO: penaliza humores repetidos seguidamente para variar de forma humana!
    for prev_mood in recent_moods:
        if prev_mood in scores:
            scores[prev_mood] *= 0.65

    # Se o usuário mandou uma mensagem curta e neutra logo após um momento triste/reflexivo,
    # mantém suavemente a continuidade emocional em vez de quebrar o clima com risada!
    if recent_moods and recent_moods[-1] in ("depressivo_triste", "reflexivo_pensativo") and not has_laugh:
        scores[recent_moods[-1]] += 2.2
        scores["zoeira_rindo"] *= 0.3

    best_mood = max(scores.items(), key=lambda item: item[1])[0]
    return best_mood


def retrieve_relevant_examples(
    user_text: str,
    target_mood: str,
    mood_bank: Dict[str, List[Dict[str, str]]],
    max_topic_matches: int = 8,
    max_mood_matches: int = 10,
) -> List[Dict[str, str]]:
    """
    Busca inteligente (RAG) nas 1.400 conversas reais:
    1) Encontra exemplos onde alguém falou sobre as MESMAS palavras/assunto que você digitou.
    2) Encontra exemplos reais seus naquele exato HUMOR detectado.
    """
    words = {w for w in re.findall(r"\b\w+\b", user_text.lower()) if len(w) >= 3}

    scored_all: List[Tuple[float, Dict[str, str]]] = []
    for mood_key, pairs in mood_bank.items():
        mood_bonus = 1.5 if mood_key == target_mood else 0.0
        for p in pairs:
            rec_words = set(re.findall(r"\b\w+\b", p["recebido"].lower()))
            overlap = len(words & rec_words)
            if overlap > 0:
                score = overlap * 2.0 + mood_bonus + random.uniform(0, 0.3)
                scored_all.append((score, p))

    scored_all.sort(key=lambda x: x[0], reverse=True)
    selected: List[Dict[str, str]] = [p for _, p in scored_all[:max_topic_matches]]

    low_t = user_text.lower()
    if any(
        ak in low_t
        for ak in [
            "astrofísica", "astrofisica", "cosmologia", "universo", "cosmos", "big bang",
            "buraco negro", "buracos", "galáxia", "galaxia", "estrela", "planeta",
            "espaço", "espaco", "james webb", "matéria escura", "energia escura",
            "multiverso", "quântica", "quantica", "relatividade", "gravidade",
            "singularidade", "teoria", "big bounce", "big freeze", "fermi"
        ]
    ):
        for p in mood_bank.get("reflexivo_pensativo", []):
            if p.get("chat") in ("Astrofísica & Universo", "Vendell") and p not in selected:
                selected.insert(0, p)

    if any(
        mk in low_t
        for mk in [
            "radwimps", "paramore", "hayley", "yojiro", "vocal", "controle vocal",
            "cantar", "canto", "cantando", "música", "musica", "banda", "belting",
            "falsete", "alcance", "voz", "suzume", "sparkle", "decode"
        ]
    ):
        for p in mood_bank.get("empolgado_amooo", []):
            if p.get("chat") == "Música & Vocal" and p not in selected:
                selected.insert(0, p)

    if target_mood == "empolgado_amooo":
        murilo_aff = [p for p in mood_bank.get("empolgado_amooo", []) if p.get("chat") == "Murilo Mariano"]
        for p in murilo_aff[:5]:
            if p not in selected:
                selected.insert(0, p)

    # Completa com exemplos autênticos do humor atual
    mood_pool = mood_bank.get(target_mood, [])
    if mood_pool:
        sampled_mood = random.sample(mood_pool, min(len(mood_pool), max_mood_matches))
        for p in sampled_mood:
            if p not in selected:
                selected.append(p)

    return selected[: (max_topic_matches + max_mood_matches)]


def update_mood_stats_file(detected_key: str, reply_text: str):
    """Atualiza data/mood_stats.json com o humor detectado para os gráficos ao vivo."""
    label = MOOD_PROFILES.get(detected_key, ("🎮 Gamer / De boa", ""))[0]
    try:
        if MOOD_STATS_PATH.exists():
            data = json.loads(MOOD_STATS_PATH.read_text(encoding="utf-8-sig"))
        else:
            data = {
                "contagem_bruta": {
                    "zoeira_rindo": 22,
                    "reflexivo_pensativo": 18,
                    "empolgado_amooo": 16,
                    "chocado_fofoca": 14,
                    "depressivo_triste": 12,
                    "gamer_deboa": 10,
                    "revoltado_aff": 8,
                }
            }
        counts = data["contagem_bruta"]
        counts[detected_key] = counts.get(detected_key, 0) + 1
        total = sum(counts.values()) or 1
        data["porcentagens"] = {k: round(v / total * 100, 1) for k, v in counts.items()}
        data["ultimo_humor"] = label
        data["ultima_frase"] = reply_text.replace("\n", " | ")[:80]
        MOOD_STATS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return label


def format_telegram_mood_chart(forced_mode: str = "auto") -> tuple:
    try:
        data = json.loads(MOOD_STATS_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        data = {"porcentagens": {}, "ultimo_humor": "🌙 Reflexivo / Pensativo"}

    pcts = data.get("porcentagens", {})
    ultimo = data.get("ultimo_humor", "🌙 Reflexivo / Pensativo")
    mode_label = (
        "🔄 Automático Inteligente (Adapta ao seu texto)"
        if forced_mode == "auto"
        else MOOD_PROFILES.get(FORCED_MODE_TO_KEY.get(forced_mode, ""), ("Automático", ""))[0]
    )

    items = [
        ("🥰 Afetivo / Carinhoso", pcts.get("empolgado_amooo", 22.0)),
        ("😂 Zoeira / Rindo", pcts.get("zoeira_rindo", 20.0)),
        ("🌙 Reflexivo / Astrofísica", pcts.get("reflexivo_pensativo", 18.0)),
        ("😱 Chocado / OXE", pcts.get("chocado_fofoca", 13.0)),
        ("🌧️ Depressivo / Pra Baixo", pcts.get("depressivo_triste", 11.0)),
        ("🎮 Gamer / Parceiro", pcts.get("gamer_deboa", 10.0)),
        ("😤 Revoltado / AFF", pcts.get("revoltado_aff", 6.0)),
    ]

    br_ctx = get_brasilia_time_context()
    lines = [
        "📊 **GRÁFICO DE HUMOR EQUILIBRADO DO CLONE**",
        "*(Adaptando o humor ao seu texto + Horário de Brasília)*\n",
        f"🕒 **Horário de Brasília:** `{br_ctx['hora_str']} ({br_ctx['dia_semana']})`",
        f"🌞 **Ritmo do Dia:** `{br_ctx['periodo']}`",
        f"🧠 **Modo de Inteligência:** `{mode_label}`",
        f"🎭 **Humor na última resposta:** `{ultimo}`\n",
    ]
    for label, pct in items:
        filled = max(1, int(round(pct / 100 * 12)))
        empty = 12 - filled
        bar = "█" * filled + "░" * empty
        lines.append(f"{label}\n`[{bar}]` **{pct}%**")

    lines.append("\n👇 *Deixe no Automático Inteligente ou force um humor:*")

    buttons = [
        [
            Button.inline("🧠 Automático Inteligente", b"mood_auto"),
            Button.inline("🥰 Bem Afetivo", b"mood_empolgado"),
        ],
        [
            Button.inline("🌌 Astrofísica / Reflexivo", b"mood_reflexivo"),
            Button.inline("🌧️ Depressivo", b"mood_depressivo"),
            Button.inline("😂 Zoeira", b"mood_zoeira"),
        ],
    ]
    return "\n".join(lines), buttons


def build_dynamic_system_prompt(user_text: str, target_mood: str, mood_bank: Dict[str, List[Dict[str, str]]]) -> str:
    """Monta um System Prompt inteligente sob medida para o assunto e humor exatos da mensagem atual."""
    perfil = {}
    if PERFIL_PATH.exists():
        with open(PERFIL_PATH, "r", encoding="utf-8-sig") as f:
            perfil = yaml.safe_load(f) or {}

    nome = perfil.get("nome", "Filipe")
    resumo = perfil.get("resumo_pessoal", f"Você é {nome}.")
    estilo_lista = perfil.get("estilo_de_escrita", [])
    regras_lista = perfil.get("regras_importantes", [])

    mood_label, mood_directive = MOOD_PROFILES.get(target_mood, MOOD_PROFILES["gamer_deboa"])
    relevant_examples = retrieve_relevant_examples(user_text, target_mood, mood_bank)
    br_ctx = get_brasilia_time_context()

    exemplos_str = "\n\n".join(
        f"Pessoa: {ex['recebido']}\nVocê: {ex['resposta']}" for ex in relevant_examples
    )
    estilo_str = "\n".join(f"- {item}" for item in estilo_lista)
    regras_str = "\n".join(f"- {item}" for item in regras_lista)

    return f"""Você NÃO é um assistente de IA. Você é {nome} (também chamado de Lipe ou L), morador de Salvador (BA), conversando no Telegram.

## Quem é você
{resumo.strip()}

## HORÁRIO DE BRASÍLIA ATUAL E SEU RITMO DO DIA: {br_ctx['hora_str']} ({br_ctx['dia_semana']}) — {br_ctx['periodo']}
{br_ctx['diretriz_horario']}
- Se for cumprimentar ou se despedir, use a saudação certa para o horário atual de Brasília ({br_ctx['saudacao_natural']}).

## TOM E HUMOR DESTE MOMENTO DA CONVERSA: {mood_label}
{mood_directive}

## Inteligência e Coerência Conversacional (MUITO IMPORTANTE)
- Preste MUITA atenção no que a pessoa acabou de dizer e responda DIRETAMENTE ao assunto dela com inteligência, memória e sentido lógico.
- NÃO jogue frases soltas ou sem relação com o que a pessoa falou.
- Adapte sua energia à energia da mensagem recebida: se a pessoa falou sério, triste ou reflexivo, seja sério/reflexivo/melancólico; se ela puxou fofoca ou piada, entre na onda.

## Seu estilo de escrita
{estilo_str}

## Regras absolutas
{regras_str}

## Exemplos reais seus nesse mesmo tom e assunto
{exemplos_str}

---
Responda APENAS com o texto que você enviaria para a pessoa (sem prefixos como "Você:" ou "{nome}:").
Cada linha será enviada como um balão separado no Telegram (use de 1 a 3 linhas curtas e naturais).
"""


def ensure_ollama_running():
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2.0)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    ollama_exe = Path(os.getenv("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
    cmd = str(ollama_exe) if ollama_exe.exists() else "ollama"
    try:
        print("⚡ Iniciando seu servidor local de IA (Ollama na RTX 5070)...")
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            [cmd, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        for _ in range(10):
            time.sleep(0.6)
            try:
                if httpx.get(f"{OLLAMA_URL}/api/tags", timeout=1.5).status_code == 200:
                    print("✅ Servidor local Ollama (RTX 5070) ONLINE em http://127.0.0.1:11434!")
                    return True
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ Aviso ao iniciar Ollama local: {e}")
    return False


def clean_vei_style(text: str) -> str:
    """Garante que 'vei' nunca saia com acento ou entre vírgulas ('véi')."""
    text = re.sub(r",\s*\bv[ée]i\b\s*,", " vei ", text, flags=re.IGNORECASE)
    text = re.sub(r",\s*\bv[ée]i\b", " vei", text, flags=re.IGNORECASE)
    text = re.sub(r"\bv[ée]i\b", "vei", text, flags=re.IGNORECASE)
    return text


class CloneContactBot:
    def __init__(self):
        pid_file = BASE_DIR / "bot.pid"
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                if old_pid != os.getpid():
                    os.kill(old_pid, 9)
                    time.sleep(0.3)
            except Exception:
                pass
        pid_file.write_text(str(os.getpid()))

        ensure_ollama_running()
        self.client = TelegramClient(load_unlocked_session(SESSION_FILE), API_ID, API_HASH)
        self.http_client = httpx.AsyncClient(timeout=20.0)
        self.mood_bank = load_mood_bank()

        self.enabled: bool = True
        self.proactive_enabled: bool = True
        self.forced_mood: str = "auto"
        self.recent_moods: Dict[int, Deque[str]] = {}
        self.pending_buffers: Dict[int, List[str]] = {}
        self.debounce_tasks: Dict[int, asyncio.Task] = {}
        self.histories: Dict[str, List[Dict[str, str]]] = self._load_histories()

        # Controle de iniciativa própria (mensagens independentes caso o usuário não responda)
        now = time.time() - 25.0
        self.last_interaction: Dict[int, float] = {5377524441: now}
        self.proactive_stage: Dict[int, int] = {5377524441: 0}
        for cid_str in self.histories.keys():
            try:
                cid = int(cid_str)
                self.last_interaction[cid] = now
                self.proactive_stage[cid] = 0
            except Exception:
                pass

    def _load_histories(self) -> Dict[str, List[Dict[str, str]]]:
        if CHAT_HISTORY_PATH.exists():
            try:
                with open(CHAT_HISTORY_PATH, "r", encoding="utf-8-sig") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_histories(self):
        CHAT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(self.histories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar histórico: {e}")

    def append_history(self, chat_id: int, role: str, text: str):
        key = str(chat_id)
        hist = self.histories.setdefault(key, [])
        if hist and hist[-1]["role"] == role:
            hist[-1]["content"] += f"\n{text}"
        else:
            hist.append({"role": role, "content": text})
        if len(hist) > 16:
            self.histories[key] = hist[-16:]
        self._save_histories()

    def _build_control_panel_markup(self):
        status_emoji = "🟢 LIGADO (Respondendo na Hora)" if self.enabled else "🔴 DESLIGADO (Pausado)"
        proactive_emoji = "🟢 ATIVA (Manda msg sozinho)" if self.proactive_enabled else "🔴 PAUSADA"
        mood_str = (
            "🧠 Automático Inteligente"
            if self.forced_mood == "auto"
            else MOOD_PROFILES.get(FORCED_MODE_TO_KEY.get(self.forced_mood, ""), ("Automático", ""))[0]
        )
        br_ctx = get_brasilia_time_context()
        text = (
            f"🎛️ **Painel de Controle do Seu Clone**\n\n"
            f"**Status atual:** {status_emoji}\n"
            f"**Iniciativa Própria:** {proactive_emoji}\n"
            f"**Horário de Brasília:** `{br_ctx['hora_str']} ({br_ctx['dia_semana']})`\n"
            f"**Ritmo do Dia:** `{br_ctx['periodo']}`\n"
            f"**Humor:** `{mood_str}`\n"
            f"**Velocidade:** ⚡ Resposta Instantânea (Na Hora)\n\n"
            f"Clique nos botões abaixo para controlar:"
        )
        buttons = [
            [
                Button.inline("🟢 Ligar (ON)", b"clone_on"),
                Button.inline("🔴 Desligar (OFF)", b"clone_off"),
            ],
            [
                Button.inline(
                    f"💬 Iniciativa: {'ON' if self.proactive_enabled else 'OFF'}",
                    b"clone_proactive_toggle",
                ),
                Button.inline("⚡ Puxar Assunto Agora", b"clone_proactive_now"),
            ],
            [
                Button.inline("📊 Gráfico de Humor", b"clone_mood"),
                Button.inline("🧹 Limpar Memória", b"clone_reset"),
            ],
        ]
        return text, buttons

    async def generate_ai_reply(
        self,
        chat_id: int,
        user_text: str,
        target_mood: str,
        extra_instruction: str = "",
    ) -> str:
        hist = self.histories.get(str(chat_id), [])
        sys_prompt = build_dynamic_system_prompt(user_text, target_mood, self.mood_bank)
        if extra_instruction:
            sys_prompt += f"\n\n## INSTRUÇÃO ESPECIAL AGORA:\n{extra_instruction}\n"
        messages = [{"role": "system", "content": sys_prompt}] + hist

        # 1. Modelos rápidos na Groq com conexão persistente para responder NA HORA!
        if AI_API_KEY.startswith("gsk_"):
            for groq_model in ("openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"):
                try:
                    resp = await self.http_client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {AI_API_KEY}"},
                        json={
                            "model": groq_model,
                            "messages": messages,
                            "temperature": 0.75,
                            "max_tokens": 350,
                        },
                        timeout=10.0,
                    )
                    if resp.status_code == 200:
                        content = (resp.json()["choices"][0]["message"]["content"] or "").strip()
                        if "</think>" in content:
                            content = content.split("</think>")[-1].strip()
                        if content:
                            return clean_vei_style(content)
                except Exception:
                    continue

        # 2. Servidor Local na sua RTX 5070 (Ollama — zero limites, sempre disponível!)
        for local_model in (OLLAMA_MODEL, "qwen2.5:7b", "llama3.1:8b"):
            try:
                resp = await self.http_client.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": local_model,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": 0.75, "num_predict": 140},
                    },
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    content = (resp.json().get("message", {}).get("content") or "").strip()
                    if content:
                        return clean_vei_style(content)
            except Exception:
                break

        # 3. Fallback adicional sem limites
        try:
            resp = await self.http_client.post(
                "https://text.pollinations.ai/openai",
                json={"model": "openai", "messages": messages, "temperature": 0.75},
                timeout=12.0,
            )
            if resp.status_code == 200:
                content = (resp.json()["choices"][0]["message"]["content"] or "").strip()
                if content:
                    return clean_vei_style(content)
        except Exception:
            pass

        return "Oxe\nperaí q deu ruim aq"

    async def transcribe_telegram_audio(self, event) -> str:
        """
        Escuta e transcreve mensagens de voz (voice notes) e arquivos de áudio
        enviados no Telegram usando Whisper Large V3 Turbo.
        """
        msg = getattr(event, "message", None)
        if not msg:
            return ""

        is_voice_or_audio = bool(getattr(msg, "voice", False) or getattr(msg, "audio", False))
        file_obj = getattr(msg, "file", None)
        mime_type = getattr(file_obj, "mime_type", "") or ""
        if not is_voice_or_audio and not mime_type.startswith("audio/") and mime_type != "video/ogg":
            return ""

        try:
            audio_bytes = await msg.download_media(file=bytes)
            if not audio_bytes:
                return ""

            ext = getattr(file_obj, "ext", None) or ".ogg"
            if not ext.startswith("."):
                ext = f".{ext}"
            filename = f"telegram_voice{ext}"
            content_type = mime_type if mime_type else "audio/ogg"

            if AI_API_KEY.startswith("gsk_"):
                for whisper_model in ("whisper-large-v3-turbo", "whisper-large-v3"):
                    try:
                        resp = await self.http_client.post(
                            "https://api.groq.com/openai/v1/audio/transcriptions",
                            headers={"Authorization": f"Bearer {AI_API_KEY}"},
                            files={"file": (filename, audio_bytes, content_type)},
                            data={
                                "model": whisper_model,
                                "language": "pt",
                                "prompt": (
                                    "Conversa de voz no Telegram com Filipe (Lipe, lil). "
                                    "Termos comuns: vei, vey, oxe, RADWIMPS, Paramore, Hayley Williams, "
                                    "Yojiro Noda, vocal, controle vocal, belting, falsete, astrofísica, "
                                    "cosmologia, universo, buraco negro, James Webb, Fortnite, Valorant, vava, Minecraft."
                                ),
                            },
                            timeout=18.0,
                        )
                        if resp.status_code == 200:
                            transcript = (resp.json().get("text") or "").strip()
                            if transcript:
                                return transcript
                    except Exception:
                        continue
        except Exception as e:
            print(f"⚠️ Erro ao escutar/transcrever áudio: {e}")

        return ""

    async def process_debounced_reply(self, chat_id: int, contact_name: str):
        try:
            # Pausa humana rápida de leitura antes de começar a digitar
            await asyncio.sleep(DEBOUNCE_SECONDS)

            if not self.enabled:
                self.pending_buffers.pop(chat_id, None)
                return

            incoming_messages = self.pending_buffers.pop(chat_id, [])
            if not incoming_messages:
                return

            self.last_interaction[chat_id] = time.time()
            self.proactive_stage[chat_id] = 0

            combined_user_text = "\n".join(incoming_messages)
            recent_q = self.recent_moods.setdefault(chat_id, deque(maxlen=4))

            # Detecta o humor ideal baseado em como a pessoa digitou/falou + equilíbrio de histórico!
            target_mood = detect_contextual_mood(combined_user_text, recent_q, self.forced_mood)
            recent_q.append(target_mood)
            mood_title = MOOD_PROFILES[target_mood][0]

            print(f"📩 [{contact_name}] enviou: {' | '.join(incoming_messages)} -> [Humor escolhido: {mood_title}]")

            self.append_history(chat_id, "user", combined_user_text)

            # Começa a mostrar "digitando..." enquanto pensa e calcula o tempo real de digitação
            t_start = time.time()
            async with self.client.action(chat_id, "typing"):
                reply_text = await self.generate_ai_reply(chat_id, combined_user_text, target_mood)
                gen_elapsed = time.time() - t_start

                if not reply_text:
                    return

                bubbles = [clean_vei_style(b.strip()) for b in reply_text.splitlines() if b.strip()][:4]
                if not bubbles:
                    return

                # Completa o tempo humano de digitação do 1º balão (descontando o que já passou gerando)
                first_typing_wait = max(0.35, calc_human_typing_seconds(bubbles[0]) - gen_elapsed)
                await asyncio.sleep(first_typing_wait)

            joined_reply = "\n".join(bubbles)
            self.append_history(chat_id, "assistant", joined_reply)
            update_mood_stats_file(target_mood, joined_reply)

            for idx, bubble in enumerate(bubbles):
                if idx > 0:
                    # Pausa natural entre um balão e outro + tempo real digitando o próximo balão
                    await asyncio.sleep(random.uniform(0.35, 0.75))
                    typing_duration = calc_human_typing_seconds(bubble)
                    async with self.client.action(chat_id, "typing"):
                        await asyncio.sleep(typing_duration)

                await self.client.send_message(chat_id, bubble)
                print(f"⌨️ [{mood_title}] -> [{contact_name}] ({idx + 1}/{len(bubbles)}): {bubble}")

            # Atualiza o relógio de interação para contar o tempo de silêncio a partir de agora
            self.last_interaction[chat_id] = time.time()
            self.proactive_stage[chat_id] = 0

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ Erro ao responder no chat {chat_id}: {e}")

    async def send_proactive_message(self, chat_id: int, stage: int):
        """
        Gera e envia uma mensagem independente (por conta própria) quando a pessoa
        fica sem responder enquanto o clone está online, simulando digitação humana real.
        """
        br_ctx = get_brasilia_time_context()
        recent_q = self.recent_moods.setdefault(chat_id, deque(maxlen=4))

        # Escolhe um tema e humor espontâneo variado de acordo com o estágio de silêncio e o Horário de Brasília
        if stage == 1:
            # 1ª mensagem espontânea (após ~45s sem resposta): continuar o assunto ou chamar com carinho/zoeira
            proactive_options = [
                (
                    "empolgado_amooo",
                    "oii lil meu bem lindo ❤️ ta fazendo oq",
                    "A pessoa ainda não respondeu sua última mensagem! Mande uma mensagem curta e carinhosa por conta própria (ex: perguntando o que ela tá fazendo agora, se tá tudo bem, ou chamando de 'lil' / 'lindo' / 'meu bem' / 'sumiu foi? ❤️') sem repetir exatamente o que você acabou de falar.",
                ),
                (
                    "chocado_fofoca",
                    "oxe sumiu do nada vei conta",
                    "A pessoa sumiu e não respondeu ainda! Mande uma mensagem curta e espontânea brincando que ela sumiu ('Oxe sumiu foi?', 'E aiii lil', 'Me deixou no vácuo msm kkkkk') ou puxando conversa.",
                ),
            ]
        else:
            # Mensagens espontâneas seguintes: puxa assuntos reais do Filipe (RADWIMPS/Paramore/Vocal, Astrofísica, Jogos, Afeto)
            proactive_options = [
                (
                    "empolgado_amooo",
                    "radwimps paramore vocal controle vocal cantar música hayley williams yojiro",
                    f"A pessoa está quieta e você resolveu puxar assunto POR CONTA PRÓPRIA agora ({br_ctx['hora_str']} - {br_ctx['periodo']}) falando sobre suas bandas favoritas (RADWIMPS e Paramore) ou sobre VOCAL e CONTROLE VOCAL! Comente que estava escutando ou cantando uma música do RADWIMPS ou do Paramore agora, reparando no controle vocal absurdo (belting, falsete, dinâmica da voz), e pergunte o que a pessoa tá ouvindo.",
                ),
                (
                    "reflexivo_pensativo",
                    "astrofísica universo buraco negro james webb teoria big bounce sonho",
                    f"A pessoa está quieta e você resolveu puxar assunto POR CONTA PRÓPRIA agora ({br_ctx['hora_str']} - {br_ctx['periodo']}) sobre sua grande paixão: ASTROFÍSICA, COSMOLOGIA e TEORIAS DO UNIVERSO! Compartilhe um pensamento espontâneo seu sobre buracos negros, galáxias do James Webb, Big Bounce, dilatação do tempo ou aquele sonho que você teve vendo a criação do universo, perguntando o que a pessoa acha.",
                ),
                (
                    "empolgado_amooo",
                    "lindo lindãooo meu bem lil te amo qualquer coisa me manda mensagem ❤️",
                    f"Você resolveu mandar uma mensagem espontânea e BEM AFETIVA por conta própria agora ({br_ctx['hora_str']} - {br_ctx['periodo']}), igual você faz com o Murilo Mariano! Diga algo doce e acolhedor ('Passando só pra dizer q to aqui viu ❤️', 'Como tá sendo sua noite lindãooo?', 'Saudade de conversar ctg :3').",
                ),
                (
                    "gamer_deboa",
                    "jogar fortnite vava minecraft pc bora amassando os cara",
                    f"Você resolveu puxar assunto por conta própria agora ({br_ctx['hora_str']} - {br_ctx['periodo']}) falando do que tá fazendo no PC ou chamando pra jogar (Fortnite 'amassando os cara', Minecraft 'Minecraftuss', Valorant/vava, Overwatch ou DBZ Sparking Zero).",
                ),
            ]

        # Evita repetir o mesmo humor seguido
        filtered = [opt for opt in proactive_options if opt[0] not in list(recent_q)[-1:]] or proactive_options
        mood_key, seed_keywords, instruction = random.choice(filtered)
        if self.forced_mood in FORCED_MODE_TO_KEY:
            mood_key = FORCED_MODE_TO_KEY[self.forced_mood]

        recent_q.append(mood_key)
        mood_title = MOOD_PROFILES[mood_key][0]

        reply_text = await self.generate_ai_reply(
            chat_id,
            seed_keywords,
            mood_key,
            extra_instruction=instruction,
        )
        if not reply_text:
            return

        # Se o usuário mandou mensagem enquanto gerávamos, cancela o envio espontâneo
        if chat_id in self.pending_buffers and self.pending_buffers[chat_id]:
            return

        bubbles = [clean_vei_style(b.strip()) for b in reply_text.splitlines() if b.strip()][:2]
        if not bubbles:
            return

        joined_reply = "\n".join(bubbles)
        self.append_history(chat_id, "assistant", joined_reply)
        update_mood_stats_file(mood_key, joined_reply)

        for idx, bubble in enumerate(bubbles):
            if idx > 0:
                await asyncio.sleep(random.uniform(0.35, 0.7))
            typing_duration = calc_human_typing_seconds(bubble)
            async with self.client.action(chat_id, "typing"):
                await asyncio.sleep(typing_duration)
            await self.client.send_message(chat_id, bubble)
            print(f"💬 [INICIATIVA PRÓPRIA #{stage} | {mood_title}] -> [{chat_id}]: {bubble}")

    async def proactive_loop(self):
        """
        Loop em background que monitora o tempo sem resposta e envia mensagens
        independentes por conta própria enquanto o bot estiver ONLINE.
        """
        await asyncio.sleep(5)
        print("💬 Loop de Iniciativa Própria ATIVO (Manda mensagens sozinho caso você não responda)!")
        while True:
            try:
                await asyncio.sleep(4)
                if not self.enabled or not self.proactive_enabled:
                    continue

                now = time.time()
                for chat_id in list(self.last_interaction.keys()):
                    # Não atropela se o usuário acabou de digitar algo
                    if self.pending_buffers.get(chat_id):
                        continue
                    task = self.debounce_tasks.get(chat_id)
                    if task and not task.done():
                        continue

                    stage = self.proactive_stage.get(chat_id, 0)
                    # Limita a até 5 iniciativas seguidas no vácuo para não fazer spam infinito;
                    # assim que você responder, o contador zera na hora!
                    if stage >= 5:
                        continue

                    elapsed = now - self.last_interaction.get(chat_id, now)
                    required_wait = (
                        PROACTIVE_FIRST_DELAY
                        if stage == 0
                        else PROACTIVE_NEXT_DELAY * stage
                    )

                    if elapsed >= required_wait:
                        self.proactive_stage[chat_id] = stage + 1
                        self.last_interaction[chat_id] = time.time()
                        await self.send_proactive_message(chat_id, stage + 1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Aviso no loop de iniciativa própria: {e}")

    async def start(self):
        @self.client.on(events.CallbackQuery)
        async def on_callback(event):
            data = event.data.decode("utf-8")
            self.last_interaction[event.chat_id] = time.time()
            if data == "clone_on":
                self.enabled = True
                text, buttons = self._build_control_panel_markup()
                try:
                    await event.edit(text, buttons=buttons)
                except Exception:
                    pass
                await event.answer("🟢 Clone LIGADO!")
            elif data == "clone_off":
                self.enabled = False
                text, buttons = self._build_control_panel_markup()
                try:
                    await event.edit(text, buttons=buttons)
                except Exception:
                    pass
                await event.answer("🔴 Clone DESLIGADO!")
            elif data == "clone_proactive_toggle":
                self.proactive_enabled = not self.proactive_enabled
                text, buttons = self._build_control_panel_markup()
                try:
                    await event.edit(text, buttons=buttons)
                except Exception:
                    pass
                status_msg = "🟢 Iniciativa Própria LIGADA!" if self.proactive_enabled else "🔴 Iniciativa Própria PAUSADA!"
                await event.answer(status_msg)
            elif data == "clone_proactive_now":
                await event.answer("⚡ Puxando assunto por conta própria agora!")
                stage = self.proactive_stage.get(event.chat_id, 0) + 1
                self.proactive_stage[event.chat_id] = stage
                self.last_interaction[event.chat_id] = time.time()
                await self.send_proactive_message(event.chat_id, max(2, stage))
            elif data == "clone_mood":
                chart_msg, chart_btns = format_telegram_mood_chart(self.forced_mood)
                await event.respond(chart_msg, buttons=chart_btns)
                await event.answer("📊 Gráfico de Humor gerado!")
            elif data.startswith("mood_"):
                new_mode = data.replace("mood_", "")
                self.forced_mood = new_mode
                chart_msg, chart_btns = format_telegram_mood_chart(self.forced_mood)
                try:
                    await event.edit(chart_msg, buttons=chart_btns)
                except Exception:
                    pass
                await event.answer("Modo de humor atualizado!")
            elif data == "clone_reset":
                self.histories.pop(str(event.chat_id), None)
                self._save_histories()
                await event.answer("🧹 Memória limpa!", alert=True)

        @self.client.on(events.NewMessage(incoming=True))
        async def on_new_message(event):
            # Registra interação imediatamente para zerar o contador de silêncio
            self.last_interaction[event.chat_id] = time.time()
            self.proactive_stage[event.chat_id] = 0

            text = (event.raw_text or "").strip()

            # Verifica se a pessoa enviou um áudio / mensagem de voz e escuta o conteúdo!
            audio_transcript = await self.transcribe_telegram_audio(event)
            if audio_transcript:
                print(f"🎙️ [Áudio escutado no chat {event.chat_id}]: {audio_transcript}")
                text = f"{text}\n{audio_transcript}".strip() if text else audio_transcript

            if not text:
                return

            low = text.lower()
            if low in ("/painel", "!painel", "/menu", "!menu", "/status", "!status"):
                panel_text, buttons = self._build_control_panel_markup()
                await event.reply(panel_text, buttons=buttons)
                return

            if low in ("/humor", "!humor"):
                chart_msg, chart_btns = format_telegram_mood_chart(self.forced_mood)
                await event.reply(chart_msg, buttons=chart_btns)
                return

            if low in ("/off", "!off", "!bot off"):
                self.enabled = False
                panel_text, buttons = self._build_control_panel_markup()
                await event.reply(panel_text, buttons=buttons)
                return

            if low in ("/on", "!on", "!bot on"):
                self.enabled = True
                panel_text, buttons = self._build_control_panel_markup()
                await event.reply(panel_text, buttons=buttons)
                return

            if low in ("/start", "!reset", "/reset"):
                self.histories.pop(str(event.chat_id), None)
                self._save_histories()
                if low in ("!reset", "/reset"):
                    await event.reply("🔄 Memória da conversa limpa! Bora começar do zero.")
                    return
                text = "Oii"

            if not self.enabled:
                return

            sender = await event.get_sender()
            contact_name = getattr(sender, "first_name", None) or "Contato"

            self.pending_buffers.setdefault(event.chat_id, []).append(text)

            existing_task = self.debounce_tasks.get(event.chat_id)
            if existing_task and not existing_task.done():
                existing_task.cancel()

            self.debounce_tasks[event.chat_id] = asyncio.create_task(
                self.process_debounced_reply(event.chat_id, contact_name)
            )

        print("🚀 Iniciando seu Clone Inteligente (Digitação Real + Áudios + Iniciativa Própria)...")
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.start(bot_token=BOT_TOKEN)
        me = await self.client.get_me()
        print("=" * 60)
        print(f"✅ Contato do seu Clone ONLINE: {me.first_name} (@{me.username})")
        print("⌨️ Digitação Humana Real: ATIVA (Tempo real proporcional a cada frase)")
        print("🎙️ Escuta de Áudios: ATIVA (Entende mensagens de voz e áudios)")
        print("🎸 Música & Vocal: RADWIMPS, Paramore & Controle Vocal integrados!")
        print(f"💬 Iniciativa Própria: ATIVA (1ª msg em {int(PROACTIVE_FIRST_DELAY)}s sem resposta)")
        print("=" * 60)
        asyncio.create_task(self.proactive_loop())
        await self.client.run_until_disconnected()


if __name__ == "__main__":
    bot = CloneContactBot()
    asyncio.run(bot.start())
