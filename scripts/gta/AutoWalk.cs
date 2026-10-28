using System;
using System.Windows.Forms;
using GTA;
using GTA.Native;

// Gojo Auto-Walk  (ScriptHookVDotNet v2 loose-source script)
//
// Makes the player ped (Gojo) stroll around on his own like an ambient NPC so
// the live has constant movement instead of a statue standing in one spot.
//
// Uses ONLY raw Function.Call natives (the combination proven to compile and
// run on this machine's SHVDN2) -- the high-level Task.WanderAround()/ClearAll()
// helpers are NOT available here and break compilation of the whole script.
//
// Behaviour:
//   * ON by default. Toggle with F7 (on-screen notify).
//   * F8 teleports Gojo out to a flat, pedestrian-heavy plaza (Legion Square)
//     so his wander reads as a busy sidewalk on stream instead of a house.
//   * Every few seconds, if Gojo is standing still, kick off a natural
//     TASK_WANDER_STANDARD so he walks around by himself.
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

    private const double PowerPauseSeconds = 6.0;
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

        // Standing still -> start a natural NPC-style wander (raw native).
        if (p.Speed < 0.5f)
        {
            Function.Call(Hash.TASK_WANDER_STANDARD, p, 10f, 10);
        }
    }

    private void StopWalking()
    {
        Ped p = Game.Player.Character;
        if (p != null && p.Exists())
            Function.Call(Hash.CLEAR_PED_TASKS, p);
    }

    // Teleport Gojo to Legion Square -- a flat, open, pedestrian-heavy downtown
    // plaza that reads as a busy sidewalk on stream. SET_ENTITY_COORDS is the
    // proven native (last arg clears the area so he lands cleanly).
    private void TeleportToSidewalk()
    {
        Ped p = Game.Player.Character;
        if (p == null || !p.Exists()) return;

        Function.Call(Hash.SET_ENTITY_COORDS, p,
            195.17f, -933.77f, 30.69f, false, false, false, true);
        Function.Call(Hash.CLEAR_PED_TASKS, p);
        suspendUntil = DateTime.UtcNow.AddSeconds(2.0);
        UI.Notify("Gojo teleported to the plaza ~g~(sidewalk)");
    }
}
