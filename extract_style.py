import argparse
import asyncio
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "style_examples.json"


def clean_text(text: str) -> str:
    """Remove espaços repetidos e filtra textos vazios, mídia oculta ou apenas links."""
    if not text:
        return ""
    text = text.strip()
    if not text:
        return ""
    lower = text.lower()
    if (
        "<mídia oculta>" in lower
        or "media omitted" in lower
        or "mensagem apagada" in lower
        or "esta mensagem foi apagada" in lower
        or lower.startswith("http://")
        or lower.startswith("https://")
    ):
        return ""
    # Remove tag de mensagem editada do WhatsApp se houver
    text = re.sub(r"\s*<Mensagem editada>$", "", text, flags=re.IGNORECASE).strip()
    return text


def build_pairs_from_messages(messages: List[Dict[str, Any]], max_pairs: int = 120) -> Dict[str, Any]:
    """
    Agrupa mensagens consecutivas do mesmo autor e monta pares:
    (mensagem recebida -> sua resposta real).
    Quando você manda várias mensagens curtas seguidas, elas são unidas com '\\n'
    para que o bot aprenda a mandar múltiplas mensagens curtas igual a você!
    """
    grouped: List[Dict[str, Any]] = []
    my_single_msgs: List[str] = []
    burst_lengths: List[int] = []
    current_burst = 0

    for msg in messages:
        text = clean_text(msg.get("text", ""))
        if not text:
            continue

        if msg["from_me"]:
            my_single_msgs.append(text)
            current_burst += 1
        else:
            if current_burst > 0:
                burst_lengths.append(current_burst)
                current_burst = 0

        if grouped and grouped[-1]["from_me"] == msg["from_me"] and grouped[-1]["chat_name"] == msg["chat_name"]:
            # Limita o agrupamento a no máximo 5 mensagens seguidas por turno
            lines = grouped[-1]["text"].split("\n")
            if len(lines) < 5:
                grouped[-1]["text"] += "\n" + text
        else:
            grouped.append({
                "from_me": msg["from_me"],
                "text": text,
                "chat_name": msg.get("chat_name", "Chat"),
            })

    if current_burst > 0:
        burst_lengths.append(current_burst)

    pairs: List[Dict[str, str]] = []
    for i in range(len(grouped) - 1):
        curr_msg = grouped[i]
        next_msg = grouped[i + 1]
        if (
            not curr_msg["from_me"]
            and next_msg["from_me"]
            and curr_msg["chat_name"] == next_msg["chat_name"]
        ):
            if 2 <= len(curr_msg["text"]) <= 300 and 2 <= len(next_msg["text"]) <= 300:
                pairs.append({
                    "chat": curr_msg["chat_name"],
                    "recebido": curr_msg["text"],
                    "resposta": next_msg["text"],
                })

    # Analisa as últimas 20.000 mensagens suas para estatísticas fiéis ao seu estilo atual
    recent_my_msgs = my_single_msgs[-20000:] if len(my_single_msgs) > 20000 else my_single_msgs
    total_my_msgs = len(my_single_msgs)
    recent_count = len(recent_my_msgs)

    avg_len = round(sum(len(t) for t in recent_my_msgs) / recent_count, 1) if recent_count else 0
    lowercase_starts = sum(1 for t in recent_my_msgs if t and t[0].islower())
    lowercase_ratio = round((lowercase_starts / recent_count) * 100, 1) if recent_count else 0
    avg_burst = round(sum(burst_lengths[-5000:]) / len(burst_lengths[-5000:]), 1) if burst_lengths else 1.0

    # Palavras e gírias frequentes
    stopwords = {
        "de", "que", "do", "da", "em", "um", "uma", "para", "com", "não", "uma",
        "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "foi",
        "ao", "ele", "das", "tem", "seu", "sua", "ou", "ser", "quando", "muito",
        "há", "nos", "já", "está", "eu", "também", "só", "pelo", "pela", "até",
        "isso", "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter",
        "seus", "quem", "nas", "me", "esse", "eles", "estão", "você", "tinha",
        "foram", "essa", "num", "nem", "suas", "meu", "às", "minha", "têm",
        "numa", "pelos", "elas", "havia", "seja", "qual", "será", "nós", "tenho",
        "lhe", "deles", "essas", "esses", "pelas", "este", "fosse", "dele",
    }
    words = []
    laughs = []
    for t in recent_my_msgs:
        for w in re.findall(r"\b\w+\b", t.lower()):
            if len(w) >= 6 and (
                set(w).issubset({"k", "s", "a", "d", "j", "f", "h", "u", "w", "q", "e"})
                and ("kk" in w or "sk" in w or "ak" in w or "ha" in w or "au" in w)
            ):
                laughs.append(t if len(t) <= 30 else w.upper())
            elif len(w) >= 2 and w not in stopwords:
                words.append(w)

    common_words = [w for w, _ in Counter(words).most_common(40)]
    common_laughs = [l for l, _ in Counter(laughs).most_common(12)]

    # Pega os pares mais recentes (para refletir seu jeito atual de falar em 2026)
    selected_pairs = pairs[-max_pairs:]

    return {
        "estatisticas_estilo": {
            "total_mensagens_suas_no_historico": total_my_msgs,
            "tamanho_medio_por_mensagem_caracteres": avg_len,
            "media_mensagens_seguidas_por_resposta": avg_burst,
            "porcentagem_inicio_minuscula": lowercase_ratio,
            "palavras_e_girias_frequentes": common_words,
            "risadas_tipicas": common_laughs,
        },
        "exemplos_reais": selected_pairs,
    }


def extract_from_whatsapp_txt(txt_path: str, my_name: str, max_pairs: int = 120):
    """Extrai pares de conversa de um arquivo .txt exportado do WhatsApp."""
    path = Path(txt_path)
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {txt_path}")
        return

    pattern = re.compile(
        r"^(?:\[?\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?\]?\s*(?:-\s*)?)([^:]+):\s*(.+)$"
    )

    all_messages: List[Dict[str, Any]] = []
    chat_name = path.stem
    my_name_clean = my_name.strip().lower()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if match:
                sender, text = match.group(1).strip(), match.group(2).strip()
                cleaned = clean_text(text)
                if not cleaned:
                    continue
                sender_clean = sender.lower()
                if len(my_name_clean) <= 2:
                    from_me = sender_clean == my_name_clean
                else:
                    from_me = sender_clean == my_name_clean or my_name_clean in sender_clean
                all_messages.append({
                    "from_me": from_me,
                    "text": cleaned,
                    "chat_name": chat_name,
                })

    result = build_pairs_from_messages(all_messages, max_pairs=max_pairs)
    save_result(result)


def save_result(result: Dict[str, Any]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    stats = result["estatisticas_estilo"]
    exemplos = result["exemplos_reais"]
    print("\n" + "=" * 60)
    print(f"✨ Estilo extraído com sucesso para: {OUTPUT_FILE}")
    print(f"📊 Total de mensagens suas analisadas: {stats['total_mensagens_suas_no_historico']}")
    print(f"📏 Tamanho médio por mensagem: {stats['tamanho_medio_por_mensagem_caracteres']} caracteres")
    print(f"💬 Média de mensagens seguidas por vez: {stats['media_mensagens_seguidas_por_resposta']}")
    print(f"🔤 Começa com letra minúscula: {stats['porcentagem_inicio_minuscula']}% das vezes")
    print(f"😂 Risadas típicas: {', '.join(stats['risadas_tipicas'][:6])}")
    print(f"🗣️ Palavras/gírias mais usadas: {', '.join(stats['palavras_e_girias_frequentes'][:15])}")
    print(f"📝 Exemplos reais de diálogo salvos: {len(exemplos)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Extrator de estilo de escrita e histórico real para o seu Clone no Telegram."
    )
    parser.add_argument(
        "--whatsapp-txt",
        type=str,
        help="Caminho para o arquivo .txt de conversa exportada do WhatsApp",
    )
    parser.add_argument(
        "--meu-nome",
        type=str,
        default="L",
        help="Seu nome como aparece no export do WhatsApp (padrão: L)",
    )
    parser.add_argument(
        "--max-exemplos",
        type=int,
        default=120,
        help="Quantidade máxima de pares de exemplo para salvar (padrão: 120)",
    )

    args = parser.parse_args()

    if args.whatsapp_txt:
        extract_from_whatsapp_txt(args.whatsapp_txt, my_name=args.meu_nome, max_pairs=args.max_exemplos)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
