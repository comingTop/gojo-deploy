using System;
using System.Windows.Forms;
using GTA;
using GTA.Native;

// Gojo Auto-Walk  (ScriptHookVDotNet v2 loose-source script)
//
// Makes the player ped (Gojo) stroll around on his own like an ambient NPC so
// the live has constant movement instead of a statue, and can teleport him out
// to a busy plaza so his wander reads as a sidewalk on stream.
//
// Uses raw Function.Call natives throughout (the combination proven on this
// machine's SHVDN2).
//
// Behaviour:
//   * ON by default. Toggle with F7.
//   * F8 teleports Gojo to Legion Square (a flat, pedestrian-heavy downtown
//     plaza). The teleport is done the PROVEN robust way (Native Trainer
//     pattern): stream the target area with LOAD_SCENE + REQUEST_COLLISION,
//     FREEZE the ped so he can't fall through the un-streamed map, move him,
//     wait until collision has loaded around him, then un-freeze. Run on the
//     tick thread so Wait() is legal (it is NOT inside the key handler).
//   * Every few seconds, if Gojo is standing still, kick off a natural
//     TASK_WANDER_STANDARD so he walks around by himself.
//   * When a gift fires a Gojo power (keys H / J / U / Y / I), wandering is
//     paused and his tasks are cleared so the power reacts cleanly, then it
//     resumes a few seconds later.
//   * Never interferes while he is in a vehicle, ragdolled, in combat,
//     shooting, or dead.
public class AutoWalk : Script
{
    private bool enabled = true;
    private bool teleportRequested = false;
    private DateTime suspendUntil = DateTime.MinValue;
    private DateTime nextCheck = DateTime.MinValue;

    private const double PowerPauseSeconds = 6.0;
    private const double CheckEverySeconds = 3.0;

    // Legion Square, downtown Los Santos -- flat, open, lots of pedestrians.
    private const float TpX = 195.17f;
    private const float TpY = -933.77f;
    private const float TpZ = 30.69f;

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
            // Defer to the tick thread so the collision-load wait is legal.
            teleportRequested = true;
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
        if (teleportRequested)
        {
            teleportRequested = false;
            TeleportToSidewalk();
            return;
        }

        if (!enabled) return;
        if (DateTime.UtcNow < suspendUntil) return;
        if (DateTime.UtcNow < nextCheck) return;
        nextCheck = DateTime.UtcNow.AddSeconds(CheckEverySeconds);

        Ped p = Game.Player.Character;
        if (p == null || !p.Exists()) return;
        if (p.IsDead || p.IsInVehicle() || p.IsRagdoll) return;
        if (p.IsInCombat || p.IsShooting) return;

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

    // Proven Native-Trainer teleport: stream the destination, freeze so the ped
    // can't fall through un-streamed terrain, move him, wait for collision, then
    // release. Runs on the tick thread so Wait() is valid here.
    private void TeleportToSidewalk()
    {
        Ped p = Game.Player.Character;
        if (p == null || !p.Exists()) return;

        // Ask the engine to stream the destination's collision/map in.
        Function.Call(Hash.REQUEST_COLLISION_AT_COORD, TpX, TpY, TpZ);
        Function.Call(Hash.LOAD_SCENE, TpX, TpY, TpZ);

        // Hold him in place so he cannot fall through before it finishes.
        Function.Call(Hash.FREEZE_ENTITY_POSITION, p, true);
        Function.Call(Hash.SET_ENTITY_COORDS, p, TpX, TpY, TpZ, false, false, false, true);
        Function.Call(Hash.CLEAR_PED_TASKS, p);

        int tries = 0;
        while (!Function.Call<bool>(Hash.HAS_COLLISION_LOADED_AROUND_ENTITY, p) && tries < 40)
        {
            Function.Call(Hash.REQUEST_COLLISION_AT_COORD, TpX, TpY, TpZ);
            Wait(50);
            tries++;
        }

        Function.Call(Hash.FREEZE_ENTITY_POSITION, p, false);
        // Let him settle a beat before the auto-wander kicks back in.
        suspendUntil = DateTime.UtcNow.AddSeconds(1.5);
        UI.Notify("Gojo teleported to the plaza ~g~(sidewalk)");
    }
}
