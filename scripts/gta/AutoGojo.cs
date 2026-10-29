using System;
using System.Windows.Forms;
using GTA;
using GTA.Native;

// SHVDN v3 / Enhanced loose-source script. Manual host test REQUIRED:
// tune SettleSeconds; verify death/respawn, F9 and JJK H/J/U/Y/I with AutoWalk.
// SET_PLAYER_MODEL replaces the ped: never keep using the old Character.
public class AutoGojo : Script
{
    private const int GojoModel = 0x18CE9868; // knivesout_gojosatoru
    private const double SettleSeconds = 8;
    private bool pending = true;
    private bool loading = false;
    private bool wasDead = false;
    private int lastPed = 0;
    private DateTime readyAt = DateTime.UtcNow.AddSeconds(SettleSeconds);
    private DateTime deadline;

    public AutoGojo()
    {
        Interval = 200;
        Tick += OnTick;
        KeyDown += OnKeyDown;
    }

    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (e.KeyCode != Keys.F9) return;
        pending = true;
        readyAt = DateTime.UtcNow.AddSeconds(1);
    }

    private void OnTick(object sender, EventArgs e)
    {
        Ped p = Game.Player.Character;
        if (p == null || !p.Exists()) return;
        if (p.IsDead) { wasDead = true; return; }
        if (wasDead || (lastPed != 0 && lastPed != p.Handle))
        {
            pending = true;
            readyAt = DateTime.UtcNow.AddSeconds(SettleSeconds);
        }
        wasDead = false;
        lastPed = p.Handle;
        if (!pending || DateTime.UtcNow < readyAt) return;
        if (Function.Call<int>(Hash.GET_ENTITY_MODEL, p) == GojoModel)
        {
            pending = false;
            return;
        }
        if (!loading)
        {
            if (!Function.Call<bool>(Hash.IS_MODEL_IN_CDIMAGE, GojoModel) ||
                !Function.Call<bool>(Hash.IS_MODEL_VALID, GojoModel))
            {
                pending = false;
                GTA.UI.Notification.Show("AutoGojo: ~r~model missing~s~; install ped, then F9");
                return;
            }
            Function.Call(Hash.REQUEST_MODEL, GojoModel);
            deadline = DateTime.UtcNow.AddSeconds(30);
            loading = true;
        }
        if (!Function.Call<bool>(Hash.HAS_MODEL_LOADED, GojoModel))
        {
            if (DateTime.UtcNow < deadline) return;
            loading = false;
            pending = false; // no endless retries; operator can press F9
            Function.Call(Hash.SET_MODEL_AS_NO_LONGER_NEEDED, GojoModel);
            GTA.UI.Notification.Show("AutoGojo: ~r~load timeout~s~; F9 to retry");
            return;
        }
        Function.Call(Hash.SET_PLAYER_MODEL, Game.Player.Handle, GojoModel);
        p = Game.Player.Character; // SET_PLAYER_MODEL invalidated the old ped
        Function.Call(Hash.SET_PED_DEFAULT_COMPONENT_VARIATION, p);
        p.Health = p.MaxHealth;
        lastPed = p.Handle;
        Function.Call(Hash.SET_MODEL_AS_NO_LONGER_NEEDED, GojoModel);
        loading = false;
        pending = false;
        GTA.UI.Notification.Show("AutoGojo: ~g~ready~s~ (F9 to re-apply)");
    }
}
