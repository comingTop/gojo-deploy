using System;
using System.Windows.Forms;
using GTA;
using GTA.Native;

// Gojo Auto-Walk  (ScriptHookVDotNet v3 / Enhanced loose-source script)
//
// Makes the player ped (Gojo) stroll around on his own like an ambient NPC.
//
// Two proven rules (from GTA modding + testing):
//   1. A player-controlled ped only plays the walk ANIMATION in place
//      (treadmill). You must release player control (SET_PLAYER_CONTROL = false)
//      so the AI actually translates him.
//   2. Do NOT re-issue TASK_WANDER_STANDARD every tick -- that resets the task
//      and he never moves. Issue it ONCE, then only re-issue if he has been
//      stuck (not translating) for a few seconds.
//
//   * ON by default. Toggle with F7.
//   * F8 teleports the player to Legion Square (flat, pedestrian-heavy plaza).
//   * On a Gojo power key (H / J / U / Y / I) control is handed back so the
//     gift reaction plays cleanly, wandering pauses, then resumes afterward.
public class AutoWalk : Script
{
    private bool enabled = true;
    private bool teleportRequested = false;
    private bool wandering = false;
    private DateTime holdUntil = DateTime.MinValue;
    private DateTime suspendUntil = DateTime.MinValue;
    private DateTime nextCheck = DateTime.MinValue;
    private DateTime movedAt = DateTime.MinValue;

    private const double PowerPauseSeconds = 6.0;
    private const double CheckEverySeconds = 2.0;
    private const double StuckSeconds = 5.0;

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
            if (!enabled)
            {
                // Restore control so toggling OFF leaves Gojo playable.
                Function.Call(Hash.SET_PLAYER_CONTROL, Game.Player.Handle, true, 0);
                ClearTasks();
                wandering = false;
            }
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
            // Hand control back so the gift power plays on a normal ped; wander
            // (and the control release) resumes after the pause.
            suspendUntil = DateTime.UtcNow.AddSeconds(PowerPauseSeconds);
            Function.Call(Hash.SET_PLAYER_CONTROL, Game.Player.Handle, true, 0);
            ClearTasks();
            wandering = false;
        }
    }

    private void OnTick(object sender, EventArgs e)
    {
        Ped p = Game.Player.Character;
        if (p == null || !p.Exists()) return;

        // --- Teleport (highest priority) ---
        if (teleportRequested)
        {
            teleportRequested = false;
            wandering = false;
            SetCoords(p);
            Function.Call(Hash.CLEAR_PED_TASKS, p);
            holdUntil = DateTime.UtcNow.AddSeconds(2.0);    // pin while area streams
            suspendUntil = DateTime.UtcNow.AddSeconds(3.0); // don't wander mid-teleport
            GTA.UI.Notification.Show("Gojo teleported to the plaza ~g~(sidewalk)");
            return;
        }
        if (DateTime.UtcNow < holdUntil)
        {
            SetCoords(p);   // keep snapping him so he can't fall through un-streamed terrain
            return;
        }

        // --- Auto-wander ---
        if (!enabled) return;
        if (DateTime.UtcNow < suspendUntil) { wandering = false; return; } // power playing
        if (DateTime.UtcNow < nextCheck) return;
        nextCheck = DateTime.UtcNow.AddSeconds(CheckEverySeconds);

        if (p.IsDead || p.IsInVehicle() || p.IsRagdoll || p.IsInCombat || p.IsShooting)
        {
            wandering = false;
            return;
        }

        if (p.Speed > 0.5f) movedAt = DateTime.UtcNow;  // he's actually translating

        bool stuck = wandering && (DateTime.UtcNow - movedAt).TotalSeconds > StuckSeconds;
        if (!wandering || stuck)
        {
            // Release control so the AI MOVES him for real, then task ONCE.
            Function.Call(Hash.SET_PLAYER_CONTROL, Game.Player.Handle, false, 0);
            Function.Call(Hash.CLEAR_PED_TASKS, p);
            Function.Call(Hash.TASK_WANDER_STANDARD, p, 10f, 10);
            wandering = true;
            movedAt = DateTime.UtcNow;
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
