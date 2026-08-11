using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;
using InternalModMenu.Features;
using InternalModMenu.Utils;

namespace InternalModMenu
{
    public class Loader : MonoBehaviour
    {
        public static GameObject ModObject;
        public static bool IsInitialized;

        public static void Init()
        {
            if (IsInitialized) return;

            ModObject = new GameObject("ENI_ModMenu");
            DontDestroyOnLoad(ModObject);
            ModObject.AddComponent<Loader>();
            ModObject.AddComponent<ESP>();
            ModObject.AddComponent<Aimbot>();
            ModObject.AddComponent<MenuUI>();

            IsInitialized = true;
        }

        private IEnumerator Start()
        {
            while (!GameUtils.IsGameReady())
                yield return new WaitForSeconds(2f);

            Debug.Log("[ENI] Mod initialized. Use Insert key to toggle menu.");
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Insert))
                MenuUI.Visible = !MenuUI.Visible;
        }
    }
}
