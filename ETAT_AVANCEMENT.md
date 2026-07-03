# État d'avancement — Afriklang Voicemail Intelligence

> Document de reprise. Objectif du projet : bot WhatsApp qui transcrit des notes
> vocales **Twi / Wolof** via l'API **Afriklang ASR**, ajoute tags (urgence /
> catégorie) + indicateur de confiance 🟢🟠🔴, et rend l'historique cherchable
> (SQLite FTS5).

**Dernière mise à jour :** 3 juillet 2026 (session déploiement + Twilio + décision Meta)
**Emplacement code :** `src/afriklang_vm/`

---

## 🔴 REPRISE RAPIDE (lis ça en premier)

**Où on en est :** l'app est **déployée et fonctionnelle en live** sur Vercel, le bot
WhatsApp **répond en réel via Twilio** (`/help`, `/wo`, `/lang` testés OK depuis
+221783128832). L'ASR Afriklang marche (modèles wo + twi chargés).

**Blocage actuel :** Twilio **Trial** a épuisé son **quota journalier de messages
(erreur `63038`)** → le bot traite tout correctement mais Twilio refuse de livrer
les réponses. Ça se réinitialise chaque jour (ou upgrade du compte pour lever la limite).

**Décision prise :** migrer le transport vers **Meta WhatsApp Cloud API** (officiel,
gratuit, sans limite journalière, compatible Vercel, aucun risque de ban).
OpenWA écarté (viole les CGU WhatsApp → risque de ban + serveur dédié requis).

**Prochaines étapes :**
1. **Créer l'app Meta** (côté utilisateur) : https://developers.facebook.com → My Apps
   → Create App (type *Business*) → Add Product **WhatsApp** → page *API Setup*.
   Y récupérer : **numéro test**, **Phone number ID**, **token**, **Add recipient**
   (vérifier +221783128832). **App Secret** : App settings → Basic.
   ⚠️ NE PAS confondre avec « Accounts Center » (= compte perso, mauvais endroit).
2. **3 décisions à trancher avant de coder :**
   - Token Meta : *temporaire 24h* ou **System User permanent** (recommandé) ?
   - Twilio : **garder en parallèle** (recommandé) ou remplacer ?
   - Version Graph API `v21.0` : OK ?
3. **Implémentation Meta** (agent, après feu vert) — voir §8 « Plan Meta Cloud API ».

**🔐 Sécurité À FAIRE :** régénérer l'Auth Token Twilio (`ae50…`, montré dans le chat)
→ console.twilio.com → Account → API keys & tokens → *Regenerate*. Le fichier
`.env.vercel` (local, gitignoré) contient les secrets Twilio — ne jamais le committer.

**Repères :** projet `/home/seydina/aiforgood` · local `make dev` / `make ci-local`
· redeploy `vercel --prod --yes` · live https://afriklang-voicemail-intelligence.vercel.app

---

> **Session du 02/07 (soir) :** `.env` local créé, API lancée et **webhook testé
> en local** avec succès (`/help`, `/wo`, `/lang`, `/search`, texte libre) —
> persistance préférence + FTS5 OK. Reste le test **note vocale** qui exige de
> vrais credentials Twilio + appel ASR réel (voir §7).
>
> **LIVRÉ :** dépôt GitHub public
> `https://github.com/SEYDINA04/afriklang-voicemail-intelligence`
> (git repo dédié + commit + push). Code prouvé **vert en local** (ruff, mypy
> strict, 20 tests). ⚠️ **GitHub Actions bloqué au niveau compte** (facturation /
> spending limit) : jobs échouent sans étape, logs vides. À débloquer dans
> *GitHub → Settings → Billing → Spending limit*, puis `git commit --allow-empty
> -m "ci: rerun" && git push` pour relancer.
>
> **DÉPLOYÉ (Vercel) :** produit live →
> **https://afriklang-voicemail-intelligence.vercel.app**
> Endpoints vérifiés en live : `/health` 200, `/docs` 200, webhook texte +
> persistance OK. 12 variables d'env injectées via `vercel env` (Production).
> Limite serverless : persistance SQLite éphémère (/tmp), pas de ffmpeg.

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

# CI/CD EN LOCAL (car GitHub Actions bloqué au niveau compte) :
make ci-local    # = scripts/ci.sh : ruff + ruff format + mypy + pytest (comme ci.yml)
make cd-local    # = scripts/cd.sh : build + push image GHCR (comme cd.yml)
./scripts/cd.sh --build-only   # build l'image sans push (aucun scope requis)

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

---

## 8. Plan Meta WhatsApp Cloud API (à implémenter)

### Principe
Ajouter un **2ᵉ transport (Meta)** à côté de Twilio, sans rien retirer. Chaque
transport a sa route webhook + son client ; ils partagent le même `BotService`
et le même pipeline ASR. L'archi est déjà transport-agnostique (`InboundMessage`,
`handle_text/handle_media`), le download média + l'envoi se font dans la route.

```
WhatsApp (numéro test Meta)
  → Meta Cloud API
  → POST /meta/webhook (JSON)      ← nouvelle route
  → download média via Graph API   ← nouveau client
  → [BotService + Afriklang : INCHANGÉS]
  → réponse via Graph API (POST /{phone_number_id}/messages)
  → 200 OK
```

### Différences Twilio → Meta gérées par l'adaptateur
- Webhook entrant : **JSON** (`entry[].changes[].value.messages[]`) au lieu de form-urlencoded.
- Vérif webhook : **GET handshake** (`hub.challenge` + `hub.verify_token`) + **HMAC SHA-256** (`X-Hub-Signature-256`, clé = App Secret, sur le body brut).
- Média : **2 étapes** — `GET /{media_id}` → URL → download (Bearer token).
- Réponse : **appel API séparé** (`send_message`) puis renvoyer `200` (pas de TwiML).

### Nouveaux fichiers
- `src/afriklang_vm/integrations/meta/client.py` — `MetaWhatsAppClient` :
  `download_media(media_id) -> (bytes, content_type)`, `send_message(to, body)`.
- `src/afriklang_vm/integrations/meta/security.py` — `MetaSignatureValidator` :
  `verify_challenge(mode, token, challenge)`, `is_valid(raw_body, signature)`.
- `src/afriklang_vm/api/routes/meta_whatsapp.py` — `GET /meta/webhook` (handshake)
  + `POST /meta/webhook` (parse → InboundMessage → bot → send_message → 200).
- `tests/unit/test_meta_security.py`, `tests/integration/test_meta_webhook.py` (mock via `respx`).

### Fichiers modifiés
- `config.py` : `whatsapp_provider`, `meta_access_token`, `meta_phone_number_id`,
  `meta_app_secret`, `meta_verify_token`, `meta_graph_version="v21.0"`, `meta_validate_signature=True`.
- `api/deps.py` + `main.py` (build_container) : instancier client + validator Meta,
  ajouter à `AppContainer` + accessors `get_meta`, `get_meta_validator`.
- `api/router.py` : `include_router(meta_whatsapp.router)`.
- `domain/schemas.py` : docstring `InboundMessage` (« Twilio » → « WhatsApp ») ; le
  `media_id` Meta est stocké dans `media_url` (le client Meta le résout).
- **Aucune modif** de `BotService`/`TranscriptionService`/`AfriklangClient`/repos/DB.

### Variables d'env Meta (à ajouter sur Vercel + `.env`)
```
WHATSAPP_PROVIDER=meta
META_ACCESS_TOKEN=...            # Bearer (temporaire 24h OU System User permanent)
META_PHONE_NUMBER_ID=...
META_APP_SECRET=...
META_VERIFY_TOKEN=un_secret_au_choix
META_GRAPH_VERSION=v21.0
META_VALIDATE_SIGNATURE=true
```

### Étapes côté Meta (utilisateur)
1. developers.facebook.com → Create App (Business) → Add Product WhatsApp.
2. WhatsApp → API Setup : numéro test, Phone number ID, token, Add recipient (+221783128832 + OTP).
3. App settings → Basic : App Secret.
4. Webhooks : Callback URL `https://afriklang-voicemail-intelligence.vercel.app/meta/webhook`,
   Verify token = `META_VERIFY_TOKEN`, s'abonner au champ **messages**.

### Note Vercel / serverless
Traitement **synchrone** (transcrit puis répond avant le 200). Vocal long ⇒ risque
de dépasser le délai ; Meta re-tente. Pour la démo OK ; sinon ack immédiat +
traitement async (évolution ultérieure).

### Décisions en attente (avant de coder)
1. Token Meta : temporaire 24h **ou** System User permanent (recommandé) ?
2. Twilio : garder en parallèle (recommandé) **ou** remplacer ?
3. Graph API `v21.0` OK ?


