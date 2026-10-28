using System;
using System.Windows.Forms;
using GTA;
using GTA.Native;

// Gojo Auto-Walk  (ScriptHookVDotNet v2 loose-source script)
//
// Makes the player ped (Gojo) stroll around on his own like an ambient NPC so
// the live has constant movement instead of a statue standing in one spot.
//
// Behaviour:
//   * ON by default. Toggle with F7 (on-screen notify).
//   * F8 teleports Gojo out to a flat, pedestrian-heavy plaza (Legion Square)
//     so his wander reads as a busy sidewalk on stream instead of a house.
//   * Every few seconds, if Gojo is just standing still, kick off a natural
//     TASK_WANDER_STANDARD so he walks the sidewalks by himself.
//   * When a gift fires a Gojo power (keys H / J / U / Y / I -- same keys the
//     orchestrator presses), wandering is paused and his tasks are cleared so
//     the power reacts cleanly, then wandering resumes a few seconds later.
//   * Never interferes while he is in a vehicle, ragdolled, in combat,
//     shooting, or dead.
public class AutoWalk : Script
{
    private bool enabled = true;
    private DateTime suspendUntil = DateTime.MinValue;
    private DateTime nextCheck = DateTime.MinValue;

    // How long to stop wandering after a power so the reaction can play out.
    private const double PowerPauseSeconds = 6.0;
    // How often we re-check whether he needs a new wander task.
    private const double CheckEverySeconds = 3.0;

    public AutoWalk()
    {
        Interval = 300;
        Tick += OnTick;
        KeyDown += OnKeyDown;
    }

    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (e.KeyCode == Keys.F7)
        {
            enabled = !enabled;
            UI.Notify("Gojo Auto-Walk: " + (enabled ? "~g~ON" : "~r~OFF"));
            if (!enabled) StopWalking();
            return;
        }

        if (e.KeyCode == Keys.F8)
        {
            TeleportToSidewalk();
            return;
        }

        if (e.KeyCode == Keys.H || e.KeyCode == Keys.J || e.KeyCode == Keys.U ||
            e.KeyCode == Keys.Y || e.KeyCode == Keys.I)
        {
            // A power is being triggered -- pause the stroll so it reacts cleanly.
            suspendUntil = DateTime.UtcNow.AddSeconds(PowerPauseSeconds);
            StopWalking();
        }
    }

    private void OnTick(object sender, EventArgs e)
    {
        if (!enabled) return;
        if (DateTime.UtcNow < suspendUntil) return;
        if (DateTime.UtcNow < nextCheck) return;
        nextCheck = DateTime.UtcNow.AddSeconds(CheckEverySeconds);

        Ped p = Game.Player.Character;
        if (p == null || !p.Exists()) return;
        if (p.IsDead || p.IsInVehicle() || p.IsRagdoll) return;
        if (p.IsInCombat || p.IsShooting) return;

        // Standing still -> start a natural NPC-style wander.
        // Task.WanderAround() is the SHVDN high-level wrapper over the
        // TASK_WANDER_STANDARD native (proven to work on the player ped --
        // see GTAForums "Bots in GTA V: automating player character walking").
        // Player control can cancel it, so we simply re-issue whenever he has
        // come to a stop, which keeps him strolling continuously.
        if (p.Speed < 0.5f)
        {
            p.Task.WanderAround();
        }
    }

    private void StopWalking()
    {
        Ped p = Game.Player.Character;
        if (p != null && p.Exists())
            p.Task.ClearAll();
    }

    // Proven SHVDN teleport: assign a new Vector3 to the ped's Position
    // (ScriptHookVDotNet How-Tos wiki). Legion Square -- a flat, open,
    // pedestrian-heavy downtown plaza that reads as a busy sidewalk on stream.
    private void TeleportToSidewalk()
    {
        Ped p = Game.Player.Character;
        if (p == null || !p.Exists()) return;

        p.Position = new GTA.Math.Vector3(195.17f, -933.77f, 30.69f);
        p.Task.ClearAll();
        // Pause the auto-wander briefly while the plaza streams in.
        suspendUntil = DateTime.UtcNow.AddSeconds(2.0);
        UI.Notify("Gojo teleported to the plaza ~g~(sidewalk)");
    }
}
