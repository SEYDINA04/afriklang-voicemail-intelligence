# Afriklang Voicemail Intelligence — WhatsApp Bot

Transcribe **Twi** and **Wolof** WhatsApp voice notes into searchable, tagged
text using the [Afriklang ASR API](https://asr.afriklang.com/docs). Record a
voice note directly in the chat, get the transcription back in seconds — with an
urgency tag and a traffic-light confidence indicator.

> Hackathon demo of the *Afriklang Voicemail Intelligence* design document:
> turning an opaque voice channel into a searchable database.

## Features

- 🎙️ **Record-in-chat → transcription**: send a WhatsApp voice note, get text back.
- 🌍 **Twi & Wolof** via the fine-tuned Afriklang ASR models (per-user language preference).
- 🏷️ **Deterministic tagging**: urgency + category detection (rule-based, multilingual).
- 🚦 **Confidence traffic-light**: 🟢/🟠/🔴 heuristic reliability indicator.
- 🔎 **Full-text search** over transcription history (SQLite FTS5).
- 🧱 **Layered architecture**: api → services → repositories → integrations.

## Architecture

```
WhatsApp voice note
  → Twilio → POST /whatsapp/webhook (FastAPI)
  → download media (Twilio) → normalize audio (optional ffmpeg)
  → language = per-user preference (default: Twi)
  → Afriklang ASR /transcribe/{wo|twi}
  → keyword tags + confidence → persist (SQLite + FTS5)
  → reply in-chat (text + tags + 🟢🟠🔴)
```

```
src/afriklang_vm/
├── api/            # FastAPI routers, DI, webhook
├── services/       # transcription, commands, keywords, confidence, search
├── integrations/   # afriklang, twilio, audio
├── repositories/   # message + preference persistence
├── domain/         # models, schemas, enums
└── db/             # async engine + FTS5 schema
```

## Requirements

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/)
- A **Twilio** account with the **WhatsApp Sandbox** enabled
- (optional) `ffmpeg` — only if you enable `AUDIO_CONVERT_TO_WAV=true`
- [ngrok](https://ngrok.com/) (or any public tunnel) to expose the webhook locally

## Quickstart

```bash
# 1. Install dependencies
make install            # uv sync --all-extras

# 2. Configure environment
cp .env.example .env    # fill in TWILIO_* values

# 3. Run the API
make dev                # uvicorn on :8000

# 4. Expose it publicly (separate terminal)
ngrok http 8000
```

Then in the [Twilio Console](https://console.twilio.com) → *Messaging → Try it
out → Send a WhatsApp message → Sandbox settings*, set:

- **When a message comes in**: `https://<your-ngrok-subdomain>.ngrok.io/whatsapp/webhook` (POST)

Join the sandbox from your phone (send `join <code>` to the sandbox number),
then:

1. Send `/twi` or `/wo` to pick a language (default: Twi).
2. Record and send a voice note → receive the transcription.
3. Send `/search <word>` to search your history.

> **Local signature validation**: Twilio signs webhooks against the public URL.
> If validation fails behind a tunnel, set `TWILIO_VALIDATE_SIGNATURE=false` in
> `.env` for local testing (keep it `true` in production).

## Bot commands

| Command        | Action                                   |
| -------------- | ---------------------------------------- |
| *(voice note)* | Transcribe in the current language       |
| `/twi`         | Set language to Twi (default)            |
| `/wo`          | Set language to Wolof                    |
| `/lang`        | Show current language                    |
| `/search <q>`  | Full-text search your transcriptions     |
| `/help`        | Show help                                |

## Development

```bash
make check       # ruff + mypy + pytest
make test        # tests with coverage
make lint        # ruff check
make fmt         # ruff format
make typecheck   # mypy
make seed        # load demo data
```

## Docker

```bash
docker build -t afriklang-voicemail:local .
docker run --env-file .env -p 8000:8000 afriklang-voicemail:local
# or:
docker compose up --build
```

## Notes on the ASR API

The Afriklang API response is `{"text": ..., "language": ..., "model": ...}` and
does **not** include a confidence score, so confidence is estimated
heuristically from lexical diversity (see `services/confidence_service.py`).
This is presented as an explainable indicator, never a guarantee of accuracy.

## License

MIT
