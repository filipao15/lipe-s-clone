# 🧠 Meu Clone no Telegram — IA Híbrida (RTX 5070 + 120B) & Benchmark de 7 Humores

Um clone neural de personalidade para o Telegram desenvolvido em **Python + Telethon + RAG**, treinado em **462.605 linhas reais de conversas do WhatsApp** e equipado com um **Painel Desktop de Benchmark & Gráficos de Humor em Tempo Real**.

---

## ✨ Funcionalidades Principais

- **🎭 Detector Contextual de 7 Humores em Tempo Real:**
  Analisa como a pessoa digitou (palavras-chave, tamanho da frase, pontuação, emojis e histórico recente) para equilibrar dinamicamente 7 camadas de humor:
  1. `🥰 Afetivo / Carinhoso` *(Elogios, acolhimento, cuidado e carinho)*
  2. `😂 Zoeira / Rindo` *(Risadas autênticas `SKAKDAKDA`, gírias de Salvador e resenha)*
  3. `🌌 Astrofísica, Cosmologia & Reflexivo` *(Paixão pelo universo, James Webb, Big Bounce, buracos negros, matéria/energia escura e conversas profundas)*
  4. `🎮 Gamer / Parceiro` *(Fortnite, Minecraft, Valorant, Overwatch, Zelda e papo de parceria)*
  5. `😱 Chocado / Fofoca` *(Reações espontâneas: `OXE`, `Ixiii`, `Foi como??`)*
  6. `🌧️ Depressivo / Crise` *(Sinceridade emocional, empatia e desabafos sem respostas robóticas)*
  7. `😤 Revoltado / Indignado` *(Desabafos de indignação: `AFFFFF`, `Tá caro saporra`)*

- **⚡ Motor de IA Híbrido (Cloud 120B + Servidor Local GPU):**
  - Combina modelos de alta capacidade (`120B` / `27B`) com servidor local **Ollama (`qwen2.5:7b` / `meu-clone`)** rodando diretamente na **NVIDIA GeForce RTX 5070** (zero limites de requisição).
- **💬 Multi-Balões Naturais + Simulação de Digitação (`typing`):**
  - Responde enviando de 1 a 4 mensagens curtas seguidas (média de 22 caracteres por balão), simulando o tempo real de digitação no Telegram.
- **🖥️ Painel Desktop (`painel_bot.py`) — Benchmark & Gráficos de Humor:**
  - Botão **ON / OFF** instantâneo (liga/desliga o clone e libera a VRAM da placa de vídeo).
  - **Gráfico Radar Neural (7 Eixos)** + **Gráfico Rosca (Donut)** + **Barras de Benchmark**.
  - **Botão `🚀 RODAR BENCHMARK DE HUMOR`** para testar os 7 eixos neurais ao vivo e simulador interativo de frases.
- **📱 Controle pelo próprio Telegram (`/painel` e `/humor`):**
  - Botões interativos inline dentro da conversa do Telegram para ligar/desligar, ver o gráfico de humor e forçar humores específicos.

---

## 🛠️ Estrutura do Projeto

- [`bot.py`](bot.py) — Motor principal do Clone no Telegram, detector contextual de 7 humores, busca RAG e integração híbrida (Cloud + Ollama Local).
- [`painel_bot.py`](painel_bot.py) — Aplicativo Desktop (`Tkinter` + `Pillow`) com botão ON/OFF, avatar customizável, Radar Neural de 7 eixos, Donut Gauge e Benchmark de Humor.
- [`perfil.yaml`](perfil.yaml) — Configuração de identidade, estilo de escrita, gírias de Salvador, lado afetivo e conhecimentos de Astrofísica/Cosmologia.
- [`extract_style.py`](extract_style.py) & [`update_brain_with_vendell_and_astro.py`](update_brain_with_vendell_and_astro.py) — Scripts de mineração e classificação de conversas exportadas do WhatsApp (`.txt`).
- [`Modelfile`](Modelfile) — Definição do modelo customizado para o servidor local Ollama.

---

## 🚀 Como Executar

1. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt pillow
   ```
2. **Configure as variáveis de ambiente:**
   Copie o arquivo `.env.example` para `.env` e preencha seu `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_BOT_TOKEN` e `GROQ_API_KEY`.
3. **Abra o Painel Desktop com Benchmark:**
   ```bash
   python painel_bot.py
   ```
   Ou inicie o bot diretamente no terminal:
   ```bash
   python bot.py
   ```
