import sys
import httpx
import os
from dotenv import load_dotenv
from bot import load_system_instruction

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def main():
    sys_prompt = load_system_instruction()
    messages = [{"role": "system", "content": sys_prompt}]

    print("=" * 60)
    print("🤖 TESTE DO SEU CLONE (Digite mensagens como se fosse um amigo seu!)")
    print("Digite 'sair' para fechar.")
    print("=" * 60)

    while True:
        try:
            user_msg = input("\n👤 Amigo: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_msg or user_msg.lower() == "sair":
            break

        messages.append({"role": "user", "content": user_msg})

        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 1024,
            },
            timeout=30.0,
        )
        reply = resp.json()["choices"][0]["message"]["content"].strip()
        messages.append({"role": "assistant", "content": reply})

        print("\n🤖 Seu Clone (balões enviados):")
        for line in [l.strip() for l in reply.splitlines() if l.strip()][:5]:
            print(f"   💬 {line}")


if __name__ == "__main__":
    main()
