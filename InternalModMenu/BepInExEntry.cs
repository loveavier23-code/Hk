using BepInEx;
using InternalModMenu;

namespace InternalModMenu
{
    [BepInPlugin("com.eni.internalmodmenu", "ENI Internal Mod Menu", "1.0.0")]
    public class BepInExEntry : BaseUnityPlugin
    {
        private void Awake()
        {
            Logger.LogInfo("ENI Mod Menu initializing...");
            Loader.Init();
            Logger.LogInfo("ENI Mod Menu ready. Press Insert to toggle.");
        }
    }
}
