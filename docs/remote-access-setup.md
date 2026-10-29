# Client phone access and automatic session startup

Implementation of plan §2; **not tested on the Windows cloud PC**. AnyDesk is
already installed with unattended access configured. Connection details and
passwords belong only in the operator's secure channel/vault, never this repo.
Use AnyDesk on the phone to attach to the existing console desktop. Plain RDP
can create a different session and break GTA/camera capture. Moonlight with a
paired host or a client-owned Parsec account is an optional console alternative.

## Operator deployment and tuning (plan §§4–5)

1. Arrange limited AirGPU startup access or an intentional schedule. Starting a
   powered-off PC cannot be automated from inside it. Agree on shutdown/billing;
   do not share the master account or leave the paid machine on indefinitely.
2. Keep the console user signed in as needed; tasks run **at logon**, not before
   sign-in. Configure automatic console sign-in only after reviewing its security
   implications. Use the same admin Windows account for Epic, GTA, OBS and tasks;
   the one-time installer requires UAC approval. Do not enter another user's
   admin credentials and expect that user's profile to capture this desktop.
3. Confirm Epic/Rockstar authentication and a free-roam save past the Prologue.
   If launch stops at STORY MODE, make the one-time manual selection; only add
   minimal, separately tested menu automation if necessary. No Go LIVE automation.
4. After merge, download BOTH deploy-autostart.cmd and deploy-autostart.ps1 from
   scripts/autostart on main into the same local folder. Run the CMD. Confirm
   the GTA scripts directory; use the PS1 `-GtaScripts` override if it differs.
   Stop existing Gojo tasks/game/orchestrator before deployment. Downloads stage
   before copying and existing targets are backed up under C:\gojo\backups.
   A copy failure can leave a partial deployment: restore backups before retrying.
   Existing d.cmd remains available for its separate application updates.
5. Confirm the application checkout at C:\gojo\src\gojo-deploy-main\orchestrator,
   Python 3.11+, and its live/control/voice extras are installed for the task user.
   Preserve ignored config.local.json; securely configure Telegram, OBS, allowed
   chat IDs and other runtime settings on the machine only. Confirm existing idle
   watchdog/shutdown behavior is appropriate for the client's session.
6. Import and tune OBS using [obs/README.md](../obs/README.md). Verify Window
   Capture, CABLE audio and browser overlay; do not blindly overwrite current
   settings. Open LIVE Studio manually and select OBS Virtual Camera plus the
   correct audio input. Store its login only on the machine, never share it.
7. Run C:\gojo\autostart\install-autostart.cmd. It recreates Gojo-Session and
   Gojo-Orchestrator as highest-privilege interactive logon tasks for this user.
   Reinstalling stops existing tasks; do it off-air. OBS auto-launch is owned by
   Gojo-Session, avoiding a competing OBS task. Remove duplicate startup entries.
8. Log off/on or reboot and sign in. Inspect Task Scheduler history and
   C:\gojo\autostart.log. Tune TimeoutSeconds/SettleSeconds in start-session.ps1,
   the worker's readiness wait/15-second settle and AutoGojo's SettleSeconds on
   the host. Health + window checks are prerequisites, not proof of free-roam.
   Confirm Epic/GTA/OBS/Python launch elevated without later UAC prompts.
9. Test AutoGojo load, already-Gojo load, death/respawn, missing model and F9
   retry. SET_PLAYER_MODEL creates a new ped; verify AutoWalk resumes and JJK
   H/J/U/Y/I powers still fire via Telegram. Tune settle delay if the mod retains
   the previous ped; investigate mod rebind support if delay is insufficient.
10. Kill only the Python child while off-air; verify a 10-second restart and
    30-second process heartbeat. Verify Telegram /status and real gift reactions,
    OBS browser cue and audio. Process heartbeats are not application health.
    See OBS README for existing /ligar streaming and initial reaction-state caveats.

## AnyDesk recreation, rotation and security

On the console, install/update AnyDesk from its official signed installer and
configure its service/unattended access in Security settings. Set a fresh unique
client-specific password locally; restrict permissions and allowed connecting
clients where supported, enable account 2FA, and test reconnection after reboot
from the phone. Grant only permissions needed for mouse/keyboard and preview;
disable clipboard/file transfer if unnecessary. Review AnyDesk session history.
To rotate/revoke: change unattended password, revoke remembered authorization
and account sessions, update the client's secure record, then test that old
access fails and new phone access succeeds. Never record the address/password in
commits, PRs, screenshots or logs. Do not enable router port forwarding for RDP.

Never share AirGPU master credentials, TikTok login, Telegram token/chat IDs,
OBS passwords or config.local.json. Use client-specific access and an agreed
revocation procedure. Secure the admin console: remote access can control the
whole machine. Backups stay local and must be protected like the originals.

## Client's minimal steps

1. Start the machine through the agreed limited-access method; wait for logon/startup.
2. Connect with AnyDesk. Open LIVE Studio if needed. Check OBS AND LIVE Studio:
   **Gojo is visible, picture is not black/frozen, and audio works**. If anything
   is wrong, do not broadcast; contact the operator.
3. Click LIVE Studio **Go LIVE** yourself.
4. Click the GTA window to focus it, then Telegram `/status` → `/ligar`.

## Acceptance record (plan §6; operator must fill after deployment)

- [ ] Reboot + console logon reaches free-roam/Gojo, orchestrator and non-black
      OBS camera hands-off within approximately 5–8 minutes (record elapsed time).
- [ ] No recurring UAC prompt; missing GTA/health times out with useful logs.
- [ ] Restart/respawn/F9/AutoWalk and all five powers pass on the installed mods.
- [ ] Phone preview, manual Go LIVE, GTA focus, Telegram and sound pass end to end.
- [ ] No secrets committed; credentials rotated and client access revocable.

To disable: stop/unregister Gojo-Session and Gojo-Orchestrator in Task Scheduler,
stop their Python child explicitly, close OBS/GTA, and remove AutoGojo.cs if needed.
Restore backed-up files/OBS exports. Never perform rollback during a live session.
