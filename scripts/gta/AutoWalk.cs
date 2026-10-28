using System;
using System.Windows.Forms;
using GTA;
using GTA.Native;

// Gojo Auto-Walk  (ScriptHookVDotNet v3 / Enhanced loose-source script)
//
// Makes the player ped (Gojo) stroll around on his own like an ambient NPC, and
// can teleport him to a busy plaza so his wander reads as a sidewalk on stream.
//
// IMPORTANT: uses ONLY the three natives confirmed to exist on this machine's
// SHVDN2 -- TASK_WANDER_STANDARD, CLEAR_PED_TASKS and SET_ENTITY_COORDS. (The
// richer teleport helpers like HAS_COLLISION_LOADED_AROUND_ENTITY / LOAD_SCENE /
// FREEZE_ENTITY_POSITION are NOT in this older enum and break compilation.)
//
// Behaviour:
//   * ON by default. Toggle with F7.
//   * F8 teleports the player to Legion Square (flat, pedestrian-heavy plaza).
//     To stop him falling through un-streamed terrain we simply re-assert the
//     coordinate every tick for ~2s (a "hold"), which pins him in place until
//     the area's collision has streamed in -- no exotic natives needed.
//   * Every few seconds, if he is standing still, start a natural
//     TASK_WANDER_STANDARD so he walks around by himself.
//   * On a Gojo power key (H / J / U / Y / I) wandering pauses so the reaction
//     plays cleanly, then resumes.
public class AutoWalk : Script
{
    private bool enabled = true;
    private bool teleportRequested = false;
    private DateTime holdUntil = DateTime.MinValue;
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
        Interval = 200;
        Tick += OnTick;
        KeyDown += OnKeyDown;
    }

    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (e.KeyCode == Keys.F7)
        {
            enabled = !enabled;
            GTA.UI.Notification.Show("Gojo Auto-Walk: " + (enabled ? "~g~ON" : "~r~OFF"));
            if (!enabled) ClearTasks();
            return;
        }

        if (e.KeyCode == Keys.F8)
        {
            teleportRequested = true;
            return;
        }

        if (e.KeyCode == Keys.H || e.KeyCode == Keys.J || e.KeyCode == Keys.U ||
            e.KeyCode == Keys.Y || e.KeyCode == Keys.I)
        {
            suspendUntil = DateTime.UtcNow.AddSeconds(PowerPauseSeconds);
            ClearTasks();
        }
    }

    private void OnTick(object sender, EventArgs e)
    {
        Ped p = Game.Player.Character;
        if (p == null || !p.Exists()) return;

        // --- Teleport handling (highest priority) ---
        if (teleportRequested)
        {
            teleportRequested = false;
            SetCoords(p);
            Function.Call(Hash.CLEAR_PED_TASKS, p);
            holdUntil = DateTime.UtcNow.AddSeconds(2.0);   // pin while area streams
            suspendUntil = DateTime.UtcNow.AddSeconds(3.0); // don't wander mid-teleport
            GTA.UI.Notification.Show("Gojo teleported to the plaza ~g~(sidewalk)");
            return;
        }
        if (DateTime.UtcNow < holdUntil)
        {
            SetCoords(p);   // keep snapping him to the spot so he can't fall through
            return;
        }

        // --- Auto-wander ---
        if (!enabled) return;
        if (DateTime.UtcNow < suspendUntil) return;
        if (DateTime.UtcNow < nextCheck) return;
        nextCheck = DateTime.UtcNow.AddSeconds(CheckEverySeconds);

        if (p.IsDead || p.IsInVehicle() || p.IsRagdoll) return;
        if (p.IsInCombat || p.IsShooting) return;

        if (p.Speed < 0.5f)
        {
            Function.Call(Hash.TASK_WANDER_STANDARD, p, 10f, 10);
        }
    }

    private void SetCoords(Ped p)
    {
        Function.Call(Hash.SET_ENTITY_COORDS, p, TpX, TpY, TpZ, false, false, false, true);
    }

    private void ClearTasks()
    {
        Ped p = Game.Player.Character;
        if (p != null && p.Exists())
            Function.Call(Hash.CLEAR_PED_TASKS, p);
    }
}
