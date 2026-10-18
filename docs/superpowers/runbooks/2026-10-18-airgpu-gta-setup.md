# Runbook — AirGPU machine → GTA V "Gojo" live setup

> Operational checklist for standing up the cloud machine. Software that can run
> headless is built separately (see `docs/superpowers/plans/`); this covers the
> hands-on Windows/GTA/OBS steps that no browser or CLI can do remotely in a
> reliable way. **Do the steps in order.**

## 0. Current state (2026-10-18)

- **AirGPU machine already created:** `airgpu-679f1a97c4` — Quadro RTX 4000, 8 vCPU /
  32 GB, **250 GB SSD**, Windows 10 (BYO license), Europe (Amsterdam II). **Status: Off.**
- Account credit: **$25** (covers setup + first tests). Cost while running: **$0.75/h**;
  storage **$0.467/day** even when Off.
- **Honest monthly:** ~R$180–195 for ~1 h/day (the forced 250 GB disk is the driver).

## ⛔ Hard prerequisite before anything else

- **A GTA V license.** You must sign in to a **Steam, Epic, or Rockstar account that
  OWNS GTA V** to install it. If none exists, buy GTA V first (~R$50–90). Decide the
  store and have the login ready. **Without this the machine cannot run the game** — no
  automation changes that.
- Also keep ready: a **Parsec account** (free), and later the **TikTok RTMP stream key**
  (from the client's TikTok, when going live).

---

## Part A — Connect to the machine

1. **Install Parsec** on your own PC (parsec.app) and sign in. (AirGPU's first connection
   can also use Windows Remote Desktop; Parsec is smoother for a game.)
2. In the AirGPU console (app.airgpu.com → Machines), press **Start** on `airgpu-679f1a97c4`.
   Wait until Status = *Running* and an **IP** appears. *(Billing starts now — $0.75/h.)*
3. Follow AirGPU's connection panel to open the Windows desktop (Parsec peer / RDP details).
   You now see the cloud Windows desktop in a window.

> Windows 10 is "Bring your own license" — it runs unactivated (a watermark, no functional
> limit). Activate later with a key if you want the watermark gone; not required to work.

## Part B — Scriptable prerequisites (run the installer)

4. Copy this repo onto the machine (Parsec file transfer, or `git clone` if you push it to
   a private repo). Put it at `C:\gojo\TikTokavatar`.
5. Open **PowerShell as Administrator** and run:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass -Force
   cd C:\gojo\TikTokavatar\scripts\windows
   .\bootstrap.ps1
   ```
   This installs Python 3.12, Git, 7-Zip, OBS Studio, sets up the orchestrator venv, runs
   its tests, and stages ScriptHookVDotNet. (It does **not** touch GTA — that's manual.)

## Part C — GTA V + mods (manual GUI — the irreducible part)

6. Install the store client (Steam/Epic/Rockstar), sign in to the account that **owns GTA V**,
   and install GTA V. *(~100 GB; this is why the disk is 250 GB.)* **Play once in Story mode**
   to confirm it launches. **Never launch GTA Online on this modded install** (ban risk).
7. **ScriptHookV** — download the build matching your GTA version (dev-c.com), copy
   `ScriptHookV.dll` + `dinput8.dll` into the GTA V folder.
8. **ScriptHookVDotNet** — copy the `.asi` + `.dll` files from `C:\gojo\mods-staging` into
   the GTA V folder.
9. **The gift→action plugin** — build/place the forked `smeysu/GTA5-TikTok-Integration`
   plugin (its HTTP server listens on `127.0.0.1:6721`). *(Delivered by Phase 4.)*
10. **Gojo ped** — install **OpenIV**, enable edit mode, install **AddonPeds**, inject the
    Satoru Gojo add-on ped, and set it as the player model (via a trainer/Menyoo).

## Part D — Capture + audio + stream

11. Install **VB-CABLE** (vb-audio.com) — the GUI installer; reboot if asked. This is the
    virtual audio device the orchestrator plays Gojo's voice into, so OBS can capture it.
12. **OBS**: create a scene at **1080×1920** (vertical). Add a *Game Capture* of GTA
    (scaled/cropped into the vertical canvas), the browser-source **overlays** (gift menu +
    TOP-3 + daily ranking — delivered by Phase 5), and an *Audio Input Capture* on VB-CABLE.
13. **OBS → Settings → Stream**: service *Custom*, paste TikTok's **Server URL + Stream Key**
    (from TikTok LIVE Center). Enable **Tools → obs-websocket** and set a password (goes into
    `config.local.json`).

## Part E — Run

14. Fill `orchestrator/config/config.local.json` from `config.example.json` (Telegram token,
    obs-websocket password, GTA adapter URL, TikTok username — already `jailton.mma`).
15. Start the orchestrator; it connects to the TikTok live, drives the plugin + overlays +
    voice, and the **Telegram bot** controls stream on/off + VM auto-stop. *(Delivered by
    Phase 6; autostart wired in Phase 7.)*

## Cost hygiene

- **Stop the machine** (AirGPU → Stop) the moment you finish a session — storage still bills
  ($0.467/day) but the $0.75/h stops. Phase 6 automates this (`/desligar` + idle watchdog).

---

### Build-status legend
- ✅ Ready now: Part B installer, the orchestrator engine (Phase 1, tested).
- 🔜 Pending phases (I'm building, headless): GTA plugin/adapter (4), overlays (5),
  Telegram + auto-stop (6), autostart/integration (7), voice lines (2 — needs your Gojo
  reference clip).
