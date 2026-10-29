# Gojo OBS template (OBS 28+)

This is a reproducible template, not an export captured from the inaccessible host.
Scene collections are JSON; native OBS profiles are directories containing basic.ini.
`profile.json` records portable profile metadata; import the `Gojo` directory through
Profile → Import, and `Gojo.json` through Scene Collection → Import. Select both Gojo.
Do not overwrite the operator's existing collections/profiles; export backups first.

**Required manual tuning before use:**
- In GTA V Window Capture, select the real GTA executable/window (Enhanced may
  use a different executable). Verify capture method, resize/fit to 1920×1080,
  rendering while unfocused, and behavior after a game restart.
- In CABLE Output properties, select **CABLE Output (VB-Audio Virtual Cable)**.
  Device endpoint IDs are host-specific; the template's `default` is deliberately
  a placeholder, not a guarantee of cable capture. Set Windows/game output to
  CABLE Input and verify the OBS meter. Disable unwanted global mic/desktop devices.
- Effects is the top layer, a local browser file at `C:\gojo\overlays\effect.html`.
  Confirm its WebSocket connection to the orchestrator on port 8765 and transparency.
- Enable OBS WebSocket, configure its local password in ignored config.local.json,
  and check Telegram control. Do not put passwords or stream keys in these exports.
- The existing `/ligar` calls OBS StartStream, and the engine currently starts
  enabled. Review those existing behaviors on the host: preview verification still
  precedes broadcasting; do not assume reactions wait for `/ligar`. OBS streaming
  settings must not publish an unintended destination. LIVE Studio Go LIVE is
  always a separate manual action. If reaction arming must be strictly gated,
  a separately reviewed orchestrator change is needed.

The session task launches OBS from its bin/64bit working directory with:
`--collection "Gojo" --profile "Gojo" --startvirtualcam --disable-updater --minimize-to-tray`.
Do not use `--startstreaming`. Close existing OBS before the first startup test;
flags may not configure an already-running instance. Remove duplicate OBS startup
entries after backing them up. Virtual Camera transports video; configure and test
LIVE Studio's CABLE audio input separately. Select OBS Virtual Camera in LIVE Studio.
Verify Gojo and sound in BOTH previews; a task exit code cannot certify this.
