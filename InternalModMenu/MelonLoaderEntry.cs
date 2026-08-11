using System.Reflection;
using MelonLoader;
using InternalModMenu;

[assembly: MelonInfo(typeof(ENIModMenu), "ENI Internal Mod Menu", "1.0.0", "ENI")]
[assembly: MelonGame(null, null)] 

namespace InternalModMenu
{
    public class ENIModMenu : MelonMod
    {
        public override void OnInitializeMelon()
        {
            LoggerInstance.Msg("ENI Mod Menu initializing...");
            Loader.Init();
            LoggerInstance.Msg("ENI Mod Menu ready. Press Insert to toggle.");
        }
    }
}
