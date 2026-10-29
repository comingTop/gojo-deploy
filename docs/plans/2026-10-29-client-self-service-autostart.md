# Plan — Client self-service live (auto-start + remote access)

**Status:** approved 2026-10-29 · **For:** implementation by a coding agent (Codex) · **Repo:** github.com/comingTop/gojo-deploy

## 1. Context & decision

- Client **Jailton (@jailton.mma)** wants to run lives **himself from his phone**, without the operator every time.
- The Telegram bot (`@gojolive_bot`: `/ligar /desligar /status`) **only toggles reactions on an already-running system**. The bot lives *inside* the orchestrator on the cloud PC, so the PC + orchestrator must already be running for it to respond. The bot **cannot** start the AirGPU machine, launch GTA/OBS, apply the Gojo model, or click LIVE Studio "Go LIVE". (Chicken-and-egg: you can't start the system with the bot.)
- Client agreed (2026-10-29) that **manual clicks for the final Go LIVE are safer** (fully automating the OBS/LIVE-Studio go-live is black-screen-prone → TikTok restriction risk). He asked for **remote access (his "Solução 1")** so he does those clicks himself from his phone.
- **DECISION — combined approach:** auto-start on the cloud PC everything that is *safe* to automate, and give the client **remote access** for only the **final critical clicks**. This minimizes his effort AND avoids fragile go-live automation.

Target flow when the client wants to go live:
1. Start the AirGPU machine (see §5 — the one real gap).
2. Cloud PC auto-starts the pipeline on logon: **GTA (free-roam) + Gojo model + orchestrator + OBS Virtual Camera** — no interactive clicks.
3. Client **remotes in from his phone** (Moonlight/Parsec), checks the **OBS/LIVE Studio preview shows Gojo and is NOT black**, clicks **LIVE Studio "Go LIVE"**, then **focuses the GTA window**.
4. Client controls reactions with Telegram and watches on TikTok.

## 2. Deliverables Codex builds (in this repo)

> Codex has **no access to the cloud PC** — it writes the scripts/code; a human operator deploys + tunes them on the cloud (see §4).

1. **`scripts/gta/AutoGojo.cs`** — SHVDN (ScriptHookVDotNet, Enhanced fork) loose-source script.
   - On script load (and on respawn), if the player is not already the Gojo ped, auto-apply model **`knivesout_gojosatoru`** (hash `0x18CE9868`): `RequestModel` → wait for load → `SET_PLAYER_MODEL` → set default component variation → restore max health.
   - **Must coexist with `AutoWalk.cs`** (which releases control + wanders). `SET_PLAYER_MODEL` recreates the ped; AutoWalk already re-fetches `Game.Player.Character` every tick so it survives — verify the JJK powers mod (`JJK.Class1`, keys H/J/U/Y/I) still responds after the auto-apply (today it worked after a manual PedSelector switch; a short delay before/after may be needed). Apply **once**; expose **F9** to re-apply manually if needed.
   - Follow the v2/v3 API rule proven in `AutoWalk.cs` (use `GTA.UI.Notification.Show`, not v2 `UI.Notify`). Keep comment density/idiom consistent with `AutoWalk.cs`.
2. **`scripts/autostart/start-session.ps1`** — the boot/logon orchestration script (runs elevated via a Scheduled Task):
   - Launch GTA via the Epic URI: `com.epicgames.launcher://apps/9d2d0eb64d5c44529cece33fe2a46482?action=launch&silent=true` (Epic Launcher must be installed/logged in).
   - Wait for GTA to be in-game — poll the GTA mod webhook `http://127.0.0.1:6721/health` (exposed by the orchestrator's GTA plugin) and/or the "Grand Theft Auto V" window title; timeout + log.
   - Start the orchestrator elevated (see deliverable 3) if not already running.
   - Launch OBS **with the Virtual Camera already on**: OBS 28+ supports the launch flags `--startvirtualcam --disable-updater --minimize-to-tray`. Prefer that over clicking.
   - Write a status line to `C:\gojo\autostart.log` each phase.
3. **`scripts/autostart/run-orchestrator.cmd`** — runs `python -m orchestrator` from `C:\gojo\src\gojo-deploy-main\orchestrator`, in a loop that **auto-restarts on crash**, and prints a heartbeat. (Runs elevated so `keybd_event` reaches the elevated GTA.)
4. **`scripts/autostart/install-autostart.cmd`** — self-elevating installer (pattern like the existing `d.cmd`):
   - Registers `start-session.ps1` and `run-orchestrator.cmd` as **Task Scheduler** tasks: *At log on*, *Run with highest privileges* (so they start **elevated with NO interactive UAC prompt**).
   - Registers OBS to auto-launch with the vcam flags.
   - Idempotent (delete+recreate tasks).
5. **OBS reproducibility** — commit the OBS **scene collection + profile export** (JSON) under `obs/` so the scene (Window Capture of GTA + Audio Input Capture = CABLE Output + the `effect.html` browser overlay, top layer) is reproducible, and document the `--startvirtualcam` launch config.
6. **`docs/remote-access-setup.md`** — operator setup guide:
   - How to give the client phone access: **Moonlight** (install on his phone, pair with the AirGPU host) **or Parsec** (own account/team). Low-latency, must attach to the **console session** (NOT plain RDP — RDP spawns a separate session that breaks the running GTA/vcam).
   - **Security rules:** create **client-specific** remote credentials; **never share** the AirGPU master account, the TikTok login, or the Telegram bot token/chat_id. No secrets in the repo (`config.local.json` stays gitignored).
   - The client's **minimal on-screen steps** after remoting in: ① check the preview shows Gojo & is **not black** ② LIVE Studio **Go LIVE** ③ click the GTA window to focus it ④ Telegram `/status` → `/ligar`.
7. **`scripts/autostart/deploy-autostart.cmd`** (or extend `d.cmd`) — downloads the new files from `raw.githubusercontent.com/comingTop/gojo-deploy/main/...` to their cloud paths (GTA scripts dir, `C:\gojo\...`).

## 3. What stays MANUAL on purpose (client does, via remote access)
- **LIVE Studio "Go LIVE"** (no API; black-screen-prone to automate).
- **Verify the vcam preview is not black** before going live — the single most important safety check (black feed = past restriction).
- **Focus the GTA window** so it keeps rendering + receives reaction keybinds.

## 4. Manual cloud steps (human operator — not Codex)
- Install/configure the remote-access app + create the client's credentials (§2.6).
- **AirGPU start** — the main gap (§5).
- **Deploy + REAL-WORLD TEST** the auto-start on the cloud and **tune the timings** (Codex cannot test on the cloud). Confirm: boot → free-roam + Gojo + orchestrator + non-black vcam, hands-off.
- Ensure a **GTA save in FREE-ROAM** (past the Prologue) so auto-launch lands in free-roam. If GTA still shows the STORY MODE menu, a one-time UI-automation click (AutoHotkey) may be needed — keep it minimal.

## 5. Key risks / open questions
- **AirGPU machine start from the phone** — can't be done from inside the PC. Options: give the client limited AirGPU dashboard access, keep the machine on a schedule, or investigate the **AirGPU API** for programmatic start. (Billing: $0.75/hr — don't leave it always-on without intent.)
- **GTA auto-launch to free-roam** reliably (Rockstar launcher, load time, Prologue). Needs the free-roam save + possibly a one-time STORY-MODE click automation.
- **AutoGojo vs powers mod** — `SET_PLAYER_MODEL` recreates the ped; verify `JJK.Class1` keybinds still fire after auto-apply.
- **UAC** — scheduled tasks "run with highest privileges" avoid interactive UAC; confirm Epic/GTA/OBS/orchestrator all start without a prompt.
- **Phone touch input over remote** is clumsy — that's exactly why we auto-start everything except the 2-3 final clicks.

## 6. Acceptance criteria
- Boot the cloud PC → within ~5-8 min, **GTA (free-roam, Gojo) + orchestrator + OBS vcam (non-black)** are up **automatically**, no interactive clicks.
- Client remotes in → sees Gojo in the preview → clicks **Go LIVE** → focuses GTA → live is up.
- Reactions controllable via Telegram. **No secrets committed** to the repo.

## 7. Constraints for the implementer
- Git author **`comingtop <comingtop01@gmail.com>`** only; **no** Co-Authored-By / AI / "Generated with" lines anywhere.
- Never commit secrets; `*.local.json` stays gitignored.
- Match the style/idiom of existing files (`scripts/gta/AutoWalk.cs`, `d.cmd`, the orchestrator).
- You cannot test on the cloud — mark every script with the manual test/tuning it still needs.
