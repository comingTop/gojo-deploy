# TikTok Interactive Live — "Gojo in GTA V" Gift-Reaction System

**Design spec** · 2026-10-18 · author: comingtop

> Scope: a complete, cloud-hosted TikTok LIVE system where a Gojo-style anime
> character inside GTA V reacts to viewer gifts with 5–7 distinct voice+animation
> reactions, controlled remotely via Telegram. Delivered turnkey to the end client
> so they only ever touch Telegram.

---

## 1. Context & commitments

**Project (freelance, escrow-funded, R$500 paid):** configure an interactive TikTok
LIVE for the client **@jailton.mma**. An anime character (**Gojo**, Jujutsu Kaisen
style) lives inside **GTA V running in the cloud** and reacts to **gifts** from the
live chat. The reference the client supplied (`assets/reference/`) is the well-known
genre: a Naruto model standing in the GTA V world, with an on-screen gift→action menu,
a TOP-3 gifter leaderboard, and a daily ranking composited into a vertical TikTok LIVE.

**What was promised to the client in the sales chat (these are now delivery obligations):**

1. Gojo character inside GTA V, in the cloud, stable.
2. **5–7 distinct reactions** triggered by specific gifts (voice line + simple animation each).
3. **Remote liga/desliga (on/off) from the phone via Telegram.**
4. **Turnkey:** the freelancer sets up the cloud + everything; the client touches nothing technical.
5. **Own PT-BR Gojo voice**, pre-recorded, **commercial-use OK, no ongoing subscription** (no ElevenLabs). Royalty-free music only; no original anime audio.
6. Cloud cost (paid by client, separate from the R$500) quoted as **R$80–150/month**.
7. Gift list for each reaction to be finalized together with the client.

**Success criteria.** A live session in which: the Gojo ped is on-screen in GTA V on a
cloud Windows machine; real TikTok gifts to @jailton.mma trigger the correct reaction
(in-game action + Gojo voice line + overlay feedback) within ~1–3 s; TOP-3 and daily
ranking overlays update live; the whole stream is turned on and off from a Telegram
chat on a phone; and the client does not have to operate any PC software directly.

### 1.1 Honest corrections to the sales promises (must be reconciled with the client)

These came out of the research (see `§9`) and the freelancer should align the client
before/at kickoff — they do not block the build but they change expectations:

- **LIVE access is an unverified hard prerequisite.** PC→TikTok streaming needs the
  account to have LIVE + PC/RTMP access (~1,000 followers, 18+, good standing). The chat
  only gave us the handle. **If @jailton.mma cannot PC-stream, nothing streams.** → `§11 P1`.
- **Realistic cloud cost is ~R$150–205/month**, above the quoted R$80–150. Shadow PC is a
  flat ≈R$194/mo; metered AWS GPU ≈R$150–180/mo. Correct this with the client to avoid a
  billing surprise. → `§9 R6`.
- **"Low risk" is optimistic; the honest level is low–medium** and stackable (GTA mods
  must be non-commercial + no third-party IP; Gojo is third-party IP; gifts are
  monetization; runs from a datacenter). Manageable with the mitigations in `§9`.
- **True "one tap, zero PC touch, go fully live"** has a TikTok RTMP key-refresh wrinkle
  (`§4.9`). Telegram gives genuine remote on/off of the *stream + engine*; the key step is
  documented, not magic.

---

## 2. Decisions locked in brainstorming (2026-10-18)

| Decision | Choice | Rationale |
|---|---|---|
| Character engine | **Core-first, renderer-agnostic engine + GTA V backend** | Honors the client's explicit GTA V requirement; the gift→reaction→voice→overlay→Telegram engine is identical regardless of renderer, so it is built once and GTA is a pluggable "body". Custom-avatar renderer kept as a documented fallback if GTA proves too fragile/expensive. |
| GTA gift bridge | **Custom Python orchestrator** → HTTP → forked `smeysu/GTA5-TikTok-Integration` in-game plugin | One codebase we own; voice, overlays, ranking, Telegram, combo logic all live together. TikFinity kept only as a no-code capture fallback. |
| Streaming + remote control | **OBS + TikTok RTMP**, driven by Telegram via **obs-websocket** | Programmatic start/stop = genuine remote liga/desliga. Key-refresh documented. |
| Voice | **Chatterbox Multilingual (Resemble AI)**, self-hosted | MIT license → unrestricted commercial use, pt-BR fine-tune, zero-shot cloning for an **original** Gojo voice, generate once / own forever / no subscription. |
| Cloud host | **Shadow PC (primary)** / AWS g4dn Windows (alternative) | Flat-rate persistent Windows gaming PC with admin + mod persistence is the simplest turnkey host. |

---

## 3. Architecture overview

```
                 TikTok LIVE  (@jailton.mma)
                      │ gifts / likes / follows
                      │ (TikTokLive lib + EulerStream signing)
                      ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  ORCHESTRATOR  —  Python, async  (BUILT 100% BY CLAUDE CODE)   │
 │                                                               │
 │  gift_listener ──► reaction_engine ──► renderer_adapter ──────┼──► GTA adapter ─┐
 │       │               │  (gift→reaction map, combos,          │  (HTTP POST     │
 │       │               │   cooldowns, queue, anti-spam)        │  127.0.0.1:6721)│
 │       │               ├──► voice_player (pre-made wav) ────────┼──► VB-CABLE ───┐│
 │       │               ├──► overlay_hub (WebSocket push) ───────┼──► OBS browser ││
 │       │               └──► state_store (TOP-3, daily ranking)  │     sources    ││
 │                                                               │                ││
 │  telegram_bot ──► control (stream on/off via obs-websocket,   │                ││
 │                   engine on/off, status, test-reaction)       │                ││
 └──────────────────────────────────────────────────────────────┘                ││
                                                                                   ▼▼
          GTA V (Story mode) + ScriptHookV + ScriptHookVDotNet                 OBS Studio
          + forked smeysu plugin (HTTP cmd server) + Gojo add-on ped     (1080×1920 vertical:
                      │ renders Gojo + executes actions                   game capture + overlays
                      └──────────── game video ─────────────────────────► + VB-CABLE audio)
                                                                                   │ RTMP
                                                                                   ▼
                                                                            TikTok LIVE
```

**Design principle — renderer-agnostic core.** The orchestrator emits abstract
`Reaction` objects. A thin **renderer adapter** translates a reaction into concrete
effects. Two adapters are specified: `GtaAdapter` (ships now, HTTP→plugin) and a
`MockAdapter` (for headless dev/test). A future `AvatarAdapter` (fallback path) would
drop in without touching the engine.

**Design principle — fully testable headless.** Development and automated testing use a
`SimulatedGiftSource` (replays fake/recorded gift events) + `MockAdapter` + a fake OBS,
so the **entire engine, overlays, Telegram bot and voice pipeline are built and tested by
Claude Code with no TikTok live, no GTA, and no cloud.** Only final integration needs the
Windows box.

---

## 4. Components

Each component is a module with one responsibility, a typed interface, and explicit
dependencies — so it can be built and tested in isolation.

### 4.1 `gift_listener`
- **Purpose:** connect to @jailton.mma's live and emit normalized events.
- **Impl:** `TikTokLive` (Python, v7.x) with EulerStream signing. Subscribes to
  `GiftEvent`, `LikeEvent`, `FollowEvent`, `ConnectEvent`, `DisconnectEvent`.
- **Normalizes** combos: streakable gifts emit until `repeat_end`; only the terminal
  event (final `repeat_count`) is counted, to avoid firing a reaction per tick.
- **Output:** `GiftEvent{user, gift_id, gift_name, coins, count, is_combo_end}` onto an
  async queue consumed by the reaction engine.
- **Depends on:** network, EulerStream (free tier; residential proxy configurable, `§9 R2`).
- **Fallback:** a `TikFinityGiftSource` (reads TikFinity's local WebSocket) if direct
  capture is throttled from the cloud IP. Same output contract.

### 4.2 `reaction_engine`
- **Purpose:** decide which reaction a gift triggers and govern pacing.
- **Logic:** look up gift in the **config map** (`§6`); apply per-reaction **cooldown**,
  a global **min-interval**, and a **queue** so simultaneous big gifts play in sequence
  rather than overlapping; **anti-spam** (collapse combos, cap rate). Updates `state_store`.
- **Output:** `Reaction{id, action, params, voice_clip, overlay_cue}` to the renderer
  adapter + voice player + overlay hub.
- **Pure and deterministic** (clock injected) → unit-testable with no I/O.

### 4.3 `renderer_adapter` (interface) + `GtaAdapter`
- **Interface:** `play(reaction) -> None`, `health() -> bool`.
- **`GtaAdapter`:** translates `reaction.action` into the forked smeysu plugin's HTTP
  command vocabulary (`POST http://127.0.0.1:6721/<command>:<param>`). Known supported
  actions from the base project: explode (radius), spawn/attack NPCs, skydive/free-fall,
  weather/storm, teleport, god-mode/health, time-scale, spawn vehicle, wanted level,
  money. Exact command strings are confirmed by reading the forked repo in Phase 1.
- **`MockAdapter`:** records calls for assertions; used in all headless tests.

### 4.4 `voice` subsystem (two parts)
- **(a) Offline generation (`voice/generate.py`), run once by Claude Code:** uses
  **Chatterbox Multilingual** (MIT) with the pt-BR fine-tune and a single reference clip
  that defines an **original** Gojo-style voice (NOT the real dub actor — `§9 R4`).
  Produces one wav per line into `voice/output/`. Inputs: `voice/lines.pt-br.json`
  (editable script of the 7+ lines). Deterministic, re-runnable; outputs are owned by the
  client forever, no subscription.
- **(b) Runtime playback (`voice_player`):** on a reaction, plays the matching wav to the
  **VB-CABLE virtual audio device**, which OBS captures as a stream audio source. (Primary
  route; alternative: trigger an OBS media source via obs-websocket. VB-CABLE install is a
  one-time manual step in the runbook.)

### 4.5 `overlay_hub` + OBS browser sources
- **Purpose:** render, as OBS **browser-source overlays**, the three on-screen widgets
  seen in the reference: the **gift→action menu** (highlights the triggered action), the
  **TOP-3 gifter leaderboard**, and the **daily ranking**.
- **Impl:** orchestrator runs a small local web server (FastAPI + WebSocket). Static
  HTML/CSS/JS overlay pages connect and update live. OBS loads them as browser sources
  positioned on the 1080×1920 vertical canvas.
- **Data:** fed from `state_store`; a `reaction` also sends an "action fired" cue to flash
  the menu. Overlays degrade gracefully if the socket drops (last state stays on screen).

### 4.6 `telegram_bot`
- **Purpose:** the client's only control surface. Commands (PT-BR):
  `/ligar` (start OBS stream via obs-websocket + enable engine), `/desligar` (stop),
  `/status` (connection, viewers if available, uptime, last gift), `/testar <reação>`
  (fire a reaction for setup testing), `/ranking` (current TOP-3).
- **Impl:** `python-telegram-bot` (or `aiogram`). **Auth:** restrict to allowed chat IDs
  (client + freelancer) from config; ignore everyone else.
- **Depends on:** obs-websocket client, orchestrator control API.

### 4.7 `state_store`
- **Purpose:** persist gifter totals, TOP-3, and the **daily ranking with automatic reset**
  (configurable TZ, default America/São_Paulo midnight). Persist config + last-known state
  so a restart resumes cleanly.
- **Impl:** SQLite (file) + in-memory cache. Simple, no server.

### 4.8 GTA side — forked plugin + Gojo ped (human-installed, Claude-prepared)
- **Forked `smeysu/GTA5-TikTok-Integration`** (MIT, C#, ScriptHookVDotNet3): Claude Code
  forks it, adds/renames the commands our 7 reactions need, tunes params (explosion radius,
  storm type, slow-mo factor), and documents the HTTP vocabulary the `GtaAdapter` targets.
  (Code edits are Claude's; **compiling/placing it into the game dir is a runbook step**.)
- **Gojo as player model:** an existing **Satoru Gojo add-on ped** (gta5-mods ecosystem),
  injected via OpenIV + AddonPeds and set as the player model. **Manual GUI step** —
  documented in the runbook; cannot be scripted headlessly.

### 4.9 OBS + RTMP streaming + key handling
- **OBS** canvas 1080×1920; scene = GTA game capture (scaled/cropped into vertical) +
  the three browser overlays + VB-CABLE audio. **obs-websocket v5** enabled so the Telegram
  bot can start/stop streaming.
- **TikTok RTMP:** server URL + stream key obtained from TikTok LIVE Center when going
  live. **Wrinkle:** keys are short-lived (~2 h, per-session). The runbook documents the
  key-refresh step; where the account/region allows, a helper fetches the key so `/ligar`
  is closer to one-tap. Otherwise `/ligar` streams to the current key and the key is
  refreshed at session start (a ~30 s freelancer step, not a client step).

---

## 5. End-to-end data flow

**Gift → reaction (happy path):**
1. Viewer sends gift → `gift_listener` receives Webcast event(s); on combo end emits one
   normalized `GiftEvent`.
2. `reaction_engine` maps gift→reaction; checks cooldown/queue; updates `state_store`.
3. Engine dispatches in parallel: `GtaAdapter.play()` (HTTP→plugin fires the in-game
   action), `voice_player` (plays Gojo wav → VB-CABLE → OBS), `overlay_hub` (flash menu +
   push new TOP-3/ranking).
4. OBS composites game + overlays + audio → RTMP → visible on the TikTok LIVE in ~1–3 s.

**Telegram on/off:** client sends `/ligar` → bot authenticates chat id → obs-websocket
`StartStream` + engine `enable()` → `/status` confirms. `/desligar` reverses it.

**Failure handling:** adapter/EulerStream/OBS failures are caught, logged, surfaced via
`/status` and a Telegram alert; the engine keeps running and retries the listener with
backoff so one dropped gift or reconnect never takes down the stream.

---

## 6. Config-driven gift → reaction mapping

A single JSON (`config/reactions.json`) is the source of truth, so gifts can be
reassigned with the client **without code changes**. Schema (per reaction):

```jsonc
{
  "id": "hollow_purple",
  "label": "Roxo — Hollow Purple",
  "gift": { "name": "Rose", "id": 5655, "min_coins": 1 },  // match by name/id/coin-tier
  "action": { "command": "explode", "params": { "radius": 15 } },
  "voice_clip": "voice/output/hollow_purple.wav",
  "overlay_cue": "menu.hollow_purple",
  "cooldown_s": 8
}
```

**Proposed default set (7 reactions, Gojo-themed; final gift mapping fixed with the client):**

| # | Reaction | In-game action (smeysu natives) | Gift tier |
|---|---|---|---|
| 1 | Flash / Teleporte | teleport / superman-fly | small |
| 2 | Azul — atração | pull + ragdoll nearby NPCs | small |
| 3 | Vermelho — repulsão | launch NPCs away (force) | medium |
| 4 | Roxo — Hollow Purple | large explosion | medium |
| 5 | Infinito / Limitless | invincibility + slow-mo | large |
| 6 | Seis Olhos | bullet-time / time-scale | large |
| 7 | Expansão de Domínio | storm + screen FX + spawn attackers | top |

Each reaction has one short original PT-BR Gojo line (script in `voice/lines.pt-br.json`).

---

## 7. Deployment & turnkey delivery model

**Host:** Shadow PC (primary) — a persistent Windows 11 cloud PC with admin rights; mods
and the game survive across sessions; flat monthly fee. (Alt: AWS g4dn.xlarge Windows +
persistent EBS.) The **freelancer performs the one-time setup on this machine** so the
client receives a working system.

**Autostart:** the orchestrator + OBS + GTA launch-helpers are registered to start on
login (Task Scheduler / startup scripts Claude provides), so after a reboot the machine
comes back to a ready state and the client just uses Telegram.

**Config & secrets:** `.env` + `config/*.json` on the host hold the TikTok username,
Telegram token + allowed chat ids, obs-websocket password, EulerStream key (if used), and
proxy settings. Never committed (see `.gitignore`).

---

## 8. Boundary — what Claude Code builds vs. one-time human steps

**Claude Code builds and tests end-to-end (headless, no cloud/TikTok/GTA needed):**
orchestrator, gift listener (+ simulator), reaction engine, config schema + default
mappings, GTA adapter + mock adapter, the Chatterbox voice-generation pipeline + the
generated lines, the three OBS overlays, the Telegram bot, the state/ranking store, the
forked GTA plugin's C# source, autostart scripts, the full runbook, and the test suite.

**One-time human (freelancer) steps — GUI/account/payment, documented in the runbook,
not automatable headless:** create the cloud + provider account and pay; install GTA V via
the launcher; install ScriptHookV + SHVDN + the compiled plugin; inject the Gojo ped via
OpenIV/AddonPeds; install VB-CABLE; configure OBS scenes + stream key; confirm TikTok LIVE
access and perform the first go-live. Claude provides exact steps + scripts to minimize
clicks, but a human executes these once.

---

## 9. Risk register & mitigations

| # | Risk | Level | Mitigation |
|---|---|---|---|
| R1 | TikTok automation ToS (unofficial gift capture) | med | Read-only of a public live; no official API exists; genre-standard. Accept IP-ban risk; keep capture swappable (TikFinity fallback). |
| R2 | Cloud/datacenter IP blocked for gift capture | med | Residential/mobile proxy configurable in `gift_listener`; or run capture via TikFinity; or capture from a residential link and forward. |
| R3 | ScriptHookV breaks on GTA updates | med | Pin GTA version / disable auto-update on the host; document the "wait for SHV update + re-copy" recovery. |
| R4 | Voice/likeness IP (Gojo = Shueisha/MAPPA) | low–med | **Original** AI voice (never clone the dub actor); "inspired-by" framing; no official logos/art/soundtrack; royalty-free music; keep license records; be ready to rebrand. |
| R5 | GTA EULA: mods must be non-commercial + no 3rd-party IP; monetized modded stream is a gray zone | low–med | SP only (never GTA Online on the modded install); no selling mods; document the gray zone; not legal advice — advise the client to confirm. |
| R6 | Cloud cost above quote (R$150–205 vs R$80–150) | — | Correct with the client up front; pick flat-rate Shadow or cost-capped metered AWS. |
| R7 | TikTok RTMP key short-lived → remote go-live friction | low | Document key-refresh; helper where allowed; `/ligar` controls stream+engine via obs-websocket. |
| R8 | Datacenter login flags the TikTok account | low–med | Prefer a stable residential-like path for the account login; keep 2FA recovery with the client; avoid rapid geo changes. |

**Nothing here is legal advice.** For a monetized operation, the client should confirm the
current Rockstar EULA and consider a Brazilian IP lawyer before scaling.

---

## 10. Tech stack & repo layout

- **Orchestrator:** Python 3.11+, async. `TikTokLive`, `python-telegram-bot`/`aiogram`,
  `obsws-python` (obs-websocket v5), `FastAPI`+`uvicorn`+`websockets` (overlays),
  `pydantic` (config), `simpleaudio`/`ffplay` (playback), `SQLite`.
- **Voice:** `chatterbox` (Resemble, MIT) pt-BR; offline script.
- **GTA plugin:** C#, ScriptHookVDotNet3 (forked smeysu project).
- **Overlays:** static HTML/CSS/JS.
- **Tests:** `pytest`, gift-event simulator, mock adapters, fake OBS.

```
/orchestrator        # python package: listener, engine, adapters, voice, overlays, telegram, state
/gta-plugin          # forked C# SHVDN plugin (source + build notes)
/overlays            # OBS browser-source pages (gift menu, top3, ranking)
/voice               # generate.py, lines.pt-br.json, output/ (gitignored)
/config              # reactions.json, config.example.json
/scripts             # autostart, obs setup, key-refresh helper
/tests               # engine/adapter/telegram/overlay tests + recorded gift fixtures
/docs                # this spec, the runbook, the implementation plan
```

---

## 11. Prerequisites & open items (confirm with client; do not block the build)

- **P1 — LIVE access (blocking for go-live only):** confirm @jailton.mma has TikTok LIVE +
  PC/RTMP access (~1,000 followers, 18+, good standing). #1 thing to verify.
- **P2 — Final gift→reaction list:** the client picks which gift maps to which of the 7
  reactions (chat said they'd decide together). Config-driven, changeable anytime.
- **P3 — Cloud provider + payment:** who owns the account and card (client, per chat).
- **P4 — TikTok credentials for the host login** (handled securely; account stays client's).
- **P5 — Gojo reference voice clip** approved by the client for the original voice.

---

## 12. Milestones (detail lives in the implementation plan)

1. **Engine core (headless):** listener + simulator, reaction engine, config, mock adapter, tests.
2. **Voice:** Chatterbox pipeline + 7 PT-BR lines.
3. **GTA adapter + forked plugin** (source + adapter; HTTP vocabulary verified).
4. **Overlays** (gift menu, TOP-3, daily ranking) + overlay hub.
5. **Telegram control** + obs-websocket stream on/off.
6. **Integration + runbook** (cloud, GTA, OBS, go-live) — freelancer executes once.

The next artifact is a phased implementation plan (one phase per milestone, each with
concrete tasks Claude Code executes and verifies).
