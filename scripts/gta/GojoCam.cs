using System;
using System.Windows.Forms;
using GTA;
using GTA.Math;

// Gojo Front Camera  (ScriptHookVDotNet v3 / Enhanced loose-source script)
//
// Locks the game camera IN FRONT of Gojo, looking back at his face, and follows
// him as he walks and turns -- the "NPC live" look (e.g. the Goku lives).
// Requested by the client 2026-11-02 for the TikTok stream.
//
//   * Toggle with F6. Default OFF while this is being tuned -- press F6 to enable.
//     Once the values below look right on the cloud PC, set `enabled = true` so
//     every live opens straight into the locked front view.
//   * The camera sits `Distance` m in front of the ped (his facing direction),
//     `Height` m up, and aims at a point `LookHeight` m above his feet.
//   * Position and aim are smoothed (lerp) so turns look cinematic, not snappy.
//
// HOST TUNING (do on the cloud PC -- values below are first guesses):
//   Distance / Height / LookHeight / Fov / PositionSmoothing / AimSmoothing.
//   - Camera too close/far or cutting off his head -> Distance / Height / LookHeight.
//   - Turns feel jerky -> lower PositionSmoothing / AimSmoothing (0..1, lower = smoother).
//   - Clips through walls indoors -> lower Distance, or add a raycast before v2.
//   - A gift power (Domain Expansion) fights this cam -> press F6 to drop to the
//     default camera for that moment, F6 again to relock.
//   Hot-reload after edits with the Insert key; no GTA relaunch needed.
public class GojoCam : Script
{
    private bool enabled = true; // ON by default so lives open in the locked front view (F6 to toggle off)
    private Camera cam = null;
    private Vector3 smoothedPos;
    private Vector3 smoothedAim;
    private bool primed = false;

    // --- tuning (host) ---
    private const float Distance = 2.6f;           // metres in front of Gojo
    private const float Height = 0.6f;             // camera height above his feet
    private const float LookHeight = 0.65f;        // aim point height above his feet
    private const float Fov = 50f;
    private const float PositionSmoothing = 0.15f; // 0..1 (higher = snappier follow)
    private const float AimSmoothing = 0.2f;

    public GojoCam()
    {
        Interval = 0; // every frame for smooth tracking
        Tick += OnTick;
        KeyDown += OnKeyDown;
        Aborted += OnAborted;
    }

    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (e.KeyCode != Keys.F6) return;
        enabled = !enabled;
        if (enabled)
        {
            primed = false; // rebuild the camera next tick
            GTA.UI.Notification.Show("Gojo Cam: ~g~ON");
        }
        else
        {
            Disable();
            GTA.UI.Notification.Show("Gojo Cam: ~r~OFF");
        }
    }

    private void OnTick(object sender, EventArgs e)
    {
        if (!enabled) return;
        Ped p = Game.Player.Character;
        if (p == null || !p.Exists() || p.IsDead) return;

        Vector3 feet = p.Position;
        Vector3 fwd = p.ForwardVector;
        Vector3 targetPos = feet + fwd * Distance + Vector3.WorldUp * Height;
        Vector3 targetAim = feet + Vector3.WorldUp * LookHeight;

        if (!primed || cam == null || !cam.Exists())
        {
            cam = World.CreateCamera(targetPos, Vector3.Zero, Fov);
            smoothedPos = targetPos;
            smoothedAim = targetAim;
            World.RenderingCamera = cam;
            primed = true;
        }

        smoothedPos = Vector3.Lerp(smoothedPos, targetPos, PositionSmoothing);
        smoothedAim = Vector3.Lerp(smoothedAim, targetAim, AimSmoothing);
        cam.Position = smoothedPos;
        cam.PointAt(smoothedAim);
    }

    private void Disable()
    {
        World.RenderingCamera = null; // hand rendering back to the gameplay camera
        if (cam != null && cam.Exists()) cam.Delete();
        cam = null;
        primed = false;
    }

    private void OnAborted(object sender, EventArgs e)
    {
        Disable();
    }
}
