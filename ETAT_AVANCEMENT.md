# État d'avancement — Afriklang Voicemail Intelligence

> Document de reprise. Objectif du projet : bot WhatsApp qui transcrit des notes
> vocales **Twi / Wolof** via l'API **Afriklang ASR**, ajoute tags (urgence /
> catégorie) + indicateur de confiance 🟢🟠🔴, et rend l'historique cherchable
> (SQLite FTS5).

**Dernière mise à jour :** 2 juillet 2026 (soir — session reprise)
**Emplacement code :** `src/afriklang_vm/`

> **Session du 02/07 (soir) :** `.env` local créé, API lancée et **webhook testé
> en local** avec succès (`/help`, `/wo`, `/lang`, `/search`, texte libre) —
> persistance préférence + FTS5 OK. Reste le test **note vocale** qui exige de
> vrais credentials Twilio + appel ASR réel (voir §7).

---

## 1. Résumé de l'état

| Élément | État |
|---|---|
| Architecture (api → services → repositories → integrations) | ✅ En place |
| Tests (`pytest`) | ✅ **20 passés** |
| Lint (`ruff`) | ✅ All checks passed |
| Typecheck (`mypy --strict`) | ✅ No issues (34 fichiers) |
| Couverture globale | 🟠 **87 %** (viser 90 %+) |
| Fichier `.env` local | ✅ Créé (signature désactivée pour test local) |
| Webhook testé en local (commandes texte) | ✅ OK — réponses TwiML + persistance |
| Test end-to-end réel note vocale (Twilio + ngrok + ASR) | ❌ Pas encore fait (§7) |
| CI/CD GitHub Actions (`ci.yml`, `cd.yml`) | ⚠️ Présent, non vérifié en run réel |

**Verdict :** le cœur applicatif est **complet et vert**. Il reste surtout la
config live (Twilio/ngrok), le test bout-en-bout, et quelques trous de couverture
sur le code réseau.

---

## 2. Ce qui est FAIT ✅

- [x] **Factory FastAPI + lifespan** (`main.py`) : init DB, wiring des singletons.
- [x] **Config typée** (`config.py`) via pydantic-settings (12-factor, `.env`).
- [x] **Webhook WhatsApp** (`api/routes/whatsapp.py`) — 90 % couvert.
- [x] **Healthcheck** (`api/routes/health.py`).
- [x] **Service de transcription** (`services/transcription_service.py`) — 100 %.
- [x] **Commandes bot** `/twi /wo /lang /search /help` (`command_service.py`) — 86 %.
- [x] **Détection mots-clés** urgence/catégorie (`keyword_service.py`) — 100 %.
- [x] **Confiance heuristique** 🟢🟠🔴 (`confidence_service.py`) — 100 %.
- [x] **Recherche full-text** (`search_service.py`) — 100 %.
- [x] **Persistance** messages + préférences (`repositories/`) + **FTS5** (`db/engine.py`).
- [x] **Intégrations** : client Afriklang, client Twilio + validation signature, converter audio.
- [x] **Enums domaine** : Language (wo/twi), ConfidenceLevel, Urgency.
- [x] **Outillage** : `Makefile`, `Dockerfile`, `docker-compose.yml`, `scripts/seed_demo.py`, workflows CI/CD.

---

## 3. Ce qui RESTE à faire 🚧

### Priorité HAUTE — pour une démo qui marche
- [x] **Créer `.env`** (fait : signature désactivée en local, placeholders Twilio).
- [x] **Tester le webhook en local** (fait : commandes texte + persistance OK).
- [ ] **Test end-to-end réel note vocale** : besoin de vrais credentials Twilio →
      voir la procédure détaillée en **§7**.
- [ ] **Vérifier l'appel réel à l'ASR Afriklang** (endpoints `/transcribe/wo` et `/transcribe/twi`,
      format de réponse `{"text", "language", "model"}`).

### Priorité MOYENNE — qualité / robustesse
- [ ] **Remonter la couverture à 90 %+**. Zones faibles :
  - `integrations/audio/converter.py` — 58 %
  - `integrations/afriklang/client.py` — 67 % (mocker via `respx`)
  - `integrations/twilio/client.py` — 69 %
  - `repositories/message_repository.py` — 72 %
  - `api/routes/health.py` — 77 %
- [ ] **Vérifier la CI GitHub Actions** sur un push (lint + typecheck + tests).
- [ ] **Gestion d'erreurs** : timeouts ASR, média Twilio indisponible, audio non supporté.

### Priorité BASSE — améliorations
- [ ] Rejouer/valider les exigences du design doc `Afriklang_..._Design_Document_EN.docx`.
- [ ] (Optionnel) activer `AUDIO_CONVERT_TO_WAV=true` si l'ASR exige WAV 16k mono (nécessite `ffmpeg`).
- [ ] Seed de données de démo (`make seed`) pour préparer une présentation.

---

## 4. Commandes utiles (reprise rapide)

```bash
cd /home/seydina/aiforgood

make install     # uv sync --all-extras
make check       # ruff + mypy + pytest (tout vérifier)
make test        # tests + couverture
make dev         # API en local sur :8000 (autoreload)

# Démo live :
cp .env.example .env      # puis remplir les TWILIO_*
make dev
ngrok http 8000           # dans un 2e terminal
```

---

## 5. Notes de reprise (contexte machine)

- La RAM avait saturé → machine plantée. Coupable principal : **Firefox** (~10 Gi, 29 process).
- Conteneurs Docker d'autres projets arrêtés pour libérer la RAM :
  `dekkal-*`, `digba-*`, `n8n-n8n-1` (les relancer avec `docker start <nom>` si besoin).
- **Pour rester modéré en ressources** pendant le dev :
  - Lancer l'API en **1 worker** : `uvicorn afriklang_vm.main:app --workers 1`.
  - Éviter `--reload` si inutile (garde un watcher en mémoire).
  - Fermer/décharger les onglets Firefox (`about:unloads`, `about:processes`).

---

## 6. Décisions techniques à retenir

- L'API Afriklang **ne renvoie pas de score de confiance** → confiance estimée
  heuristiquement (diversité lexicale) dans `confidence_service.py`. Indicateur
  explicable, **pas** une garantie d'exactitude.
- Tagging **déterministe** (règles multilingues), pas de ML côté tags.
- Persistance **SQLite + FTS5** (async via `aiosqlite`), pas de service externe.

---

## 7. Procédure de test end-to-end réel (note vocale)

Le chemin « note vocale » ne peut PAS être testé en local sans Twilio réel :
le webhook doit **télécharger le média** depuis l'URL Twilio (auth requise) puis
**appeler l'ASR Afriklang**. Étapes :

**1. Credentials Twilio** — Console Twilio → *Messaging → Try it out → WhatsApp*.
Récupérer `ACCOUNT SID` + `AUTH TOKEN`, puis dans `.env` :
```env
TWILIO_ACCOUNT_SID=AC...            # ta vraie valeur
TWILIO_AUTH_TOKEN=...               # ta vraie valeur
TWILIO_VALIDATE_SIGNATURE=true      # garder true en test réel (Twilio signe)
```

**2. Lancer l'API (léger, 1 worker) :**
```bash
cd /home/seydina/aiforgood
uv run uvicorn afriklang_vm.main:app --host 0.0.0.0 --port 8000 --workers 1
```

**3. Exposer via tunnel (2e terminal) :**
```bash
ngrok http 8000
# → copier l'URL https publique, ex: https://xxxx.ngrok-free.app
```

**4. Configurer le webhook Twilio :**
Console Twilio → Sandbox settings → *When a message comes in* :
`https://xxxx.ngrok-free.app/whatsapp/webhook` (méthode **POST**).

**5. Rejoindre le sandbox depuis WhatsApp :** envoyer `join <code-sandbox>` au
numéro sandbox, puis :
- `/twi` ou `/wo` pour choisir la langue,
- **enregistrer et envoyer une note vocale** → transcription + tags + 🟢🟠🔴,
- `/search <mot>` pour retrouver dans l'historique.

**Astuce debug :** logs API dans le terminal uvicorn (`webhook.received`,
`webhook.error`). Si l'ASR échoue, vérifier `AFRIKLANG_BASE_URL` et le format
de réponse attendu `{"text","language","model"}`.

**Rappel ressources :** couper ngrok + l'API quand le test est fini
(`Ctrl+C`), et ne pas relancer les conteneurs Docker inutiles.

