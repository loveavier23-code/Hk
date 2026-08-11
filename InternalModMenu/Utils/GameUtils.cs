using System;
using System.Reflection;
using UnityEngine;

namespace InternalModMenu.Utils
{
    public static class GameUtils
    {
        private static Camera _mainCamera;
        private static Type _playerCameraType;
        private static MethodInfo _worldToScreenMethod;
        private static Type _pawnType;
        private static Type _localPlayerType;
        private static Type _brPlayerPawnType;
        private static Type _playerControllerType;

        public static Camera MainCamera
        {
            get
            {
                if (_mainCamera == null)
                    _mainCamera = Camera.main ?? Camera.current;
                return _mainCamera;
            }
        }

        public static Type PawnType
        {
            get
            {
                if (_pawnType == null)
                {
                    foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                    {
                        _pawnType = asm.GetType("GameEngine.Pawn") ?? asm.GetType("Pawn");
                        if (_pawnType != null) break;
                    }
                }
                return _pawnType;
            }
        }

        public static Type BRPlayerPawnType
        {
            get
            {
                if (_brPlayerPawnType == null)
                {
                    foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                    {
                        _brPlayerPawnType = asm.GetType("GameEngine.BRPlayerPawn") ?? asm.GetType("BRPlayerPawn");
                        if (_brPlayerPawnType != null) break;
                    }
                }
                return _brPlayerPawnType ?? PawnType;
            }
        }

        public static Type LocalPlayerType
        {
            get
            {
                if (_localPlayerType == null)
                {
                    foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                    {
                        _localPlayerType = asm.GetType("GameEngine.LocalPlayer") ?? asm.GetType("LocalPlayer");
                        if (_localPlayerType != null) break;
                    }
                }
                return _localPlayerType;
            }
        }

        public static Type PlayerControllerType
        {
            get
            {
                if (_playerControllerType == null)
                {
                    foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                    {
                        _playerControllerType = asm.GetType("GameEngine.PlayerController") ?? asm.GetType("PlayerController");
                        if (_playerControllerType != null) break;
                    }
                }
                return _playerControllerType;
            }
        }

        public static object LocalPlayerInstance
        {
            get
            {
                var t = LocalPlayerType;
                if (t == null) return null;

                var prop = t.GetProperty("Instance",
                    BindingFlags.Public | BindingFlags.Static | BindingFlags.NonPublic);

                if (prop != null) return prop.GetValue(null);

                var field = t.GetField("m_Instance",
                    BindingFlags.Public | BindingFlags.Static | BindingFlags.NonPublic);

                if (field != null) return field.GetValue(null);

                var objs = UnityEngine.Object.FindObjectsOfType(PawnType ?? BRPlayerPawnType ?? typeof(MonoBehaviour));
                foreach (var o in objs)
                {
                    var controller = GetFieldValue(o, "m_Controller");
                    if (controller != null)
                    {
                        var isLocal = GetFieldValue<bool>(controller, "m_IsLocalPlayer");
                        if (isLocal) return GetFieldValue(o, "m_PlayerInfo");
                    }
                }

                return null;
            }
        }

        public static int GetLocalCamp()
        {
            var lp = LocalPlayerInstance;
            if (lp == null) return -1;

            var camp = GetFieldValue<int>(lp, "Camp", 0x60);
            if (camp == 0) camp = GetFieldValue<int>(lp, "Camp_OB", 0x20);
            if (camp == 0)
            {
                var prop = lp.GetType().GetProperty("Camp",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (prop != null) camp = (int)prop.GetValue(lp);
            }
            return camp;
        }

        public static Vector3 WorldToScreen(Vector3 worldPos)
        {
            if (MainCamera != null)
                return MainCamera.WorldToScreenPoint(worldPos);

            if (_playerCameraType == null)
            {
                foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                {
                    _playerCameraType = asm.GetType("GameEngine.PlayerCamera");
                    if (_playerCameraType != null) break;
                }
            }

            if (_playerCameraType != null)
            {
                if (_worldToScreenMethod == null)
                {
                    _worldToScreenMethod = _playerCameraType.GetMethod("WorldToScreenPoint",
                        BindingFlags.Public | BindingFlags.Static);
                }

                if (_worldToScreenMethod != null)
                {
                    try
                    {
                        object[] args = new object[] { worldPos };
                        var result = _worldToScreenMethod.Invoke(null, args);
                        if (result is Vector3 v3) return v3;
                        if (args[0] is Vector3 outV3) return outV3;
                    }
                    catch { }
                }
            }

            return Vector3.zero;
        }

        public static Vector3 GetPawnPosition(object pawn)
        {
            if (pawn == null) return Vector3.zero;

            var pos = GetFieldValue<Vector3>(pawn, "m_Location", 0x5A4);
            if (pos == Vector3.zero)
            {
                var transform = GetPawnTransform(pawn);
                if (transform != null) pos = transform.position;
            }
            return pos;
        }

        public static Transform GetPawnTransform(object pawn)
        {
            if (pawn == null) return null;

            var headTransform = GetFieldValue<Transform>(pawn, "m_HeadTransform", 0x600);
            if (headTransform != null) return headTransform;

            var component = pawn as Component;
            if (component != null) return component.transform;

            var goProp = pawn.GetType().GetProperty("gameObject",
                BindingFlags.Public | BindingFlags.Instance);
            if (goProp != null)
            {
                var go = goProp.GetValue(pawn) as GameObject;
                if (go != null) return go.transform;
            }

            return null;
        }

        public static bool IsPawnAlive(object pawn)
        {
            if (pawn == null) return false;

            var alive = GetFieldValue<bool>(pawn, "m_IsAlive", 0x548);
            if (!alive)
            {
                var prop = pawn.GetType().GetProperty("isAlive",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (prop != null) alive = (bool)prop.GetValue(pawn);
            }
            return alive;
        }

        public static float GetPawnHealth(object pawn)
        {
            if (pawn == null) return 0f;

            var prop = pawn.GetType().GetProperty("Health",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (prop != null)
            {
                try { return (float)prop.GetValue(pawn); }
                catch { }
            }

            var method = pawn.GetType().GetMethod("get_Health",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (method != null)
            {
                try { return (float)method.Invoke(pawn, null); }
                catch { }
            }

            return 0f;
        }

        public static int GetPawnCamp(object pawn)
        {
            if (pawn == null) return -1;

            var camp = GetFieldValue<int>(pawn, "m_Camp");
            if (camp == 0) camp = GetFieldValue<int>(pawn, "Camp");
            if (camp == 0)
            {
                var prop = pawn.GetType().GetProperty("TeamId",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (prop != null)
                {
                    try { return (int)(uint)prop.GetValue(pawn); }
                    catch { try { return (int)prop.GetValue(pawn); } catch { } }
                }
            }
            return camp;
        }

        public static string GetPawnName(object pawn)
        {
            if (pawn == null) return "???";

            var prop = pawn.GetType().GetProperty("PlayerName",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (prop != null)
            {
                try { return prop.GetValue(pawn) as string ?? "???"; }
                catch { }
            }

            var field = GetFieldValue<string>(pawn, "m_PlayerName");
            if (!string.IsNullOrEmpty(field)) return field;

            var playerInfo = GetFieldValue<object>(pawn, "m_PlayerInfo", 0x5C0);
            if (playerInfo != null)
            {
                var nameProp = playerInfo.GetType().GetProperty("NickName",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (nameProp != null)
                {
                    try { return nameProp.GetValue(playerInfo) as string ?? "???"; }
                    catch { }
                }
            }

            return "???";
        }

        public static float GetPawnDistance(object pawn)
        {
            var localPawn = GetLocalPawn();
            if (localPawn == null || pawn == null) return float.MaxValue;
            return Vector3.Distance(GetPawnPosition(localPawn), GetPawnPosition(pawn));
        }

        public static object GetLocalPawn()
        {
            var lp = LocalPlayerInstance;
            if (lp == null) return null;

            var controller = GetFieldValue<object>(lp, "PlayerController", 0x70);
            if (controller == null) return null;

            var pawn = GetFieldValue<object>(controller, "m_Pawn");
            if (pawn != null) return pawn;

            var pawnProp = controller.GetType().GetProperty("Pawn",
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (pawnProp != null) return pawnProp.GetValue(controller);

            return null;
        }

        public static List<object> GetAllPawns()
        {
            var result = new List<object>();
            var pawnType = BRPlayerPawnType ?? PawnType;
            if (pawnType == null) return result;

            try
            {
                var allObjs = UnityEngine.Object.FindObjectsOfType(pawnType);
                foreach (var o in allObjs)
                {
                    if (o != null && o.GetType().IsSubclassOf(pawnType) || o.GetType() == pawnType)
                        result.Add(o);
                }
            }
            catch { }

            if (result.Count == 0)
            {
                try
                {
                    var allGos = UnityEngine.Object.FindObjectsOfType<GameObject>();
                    foreach (var go in allGos)
                    {
                        var comp = go.GetComponent(pawnType);
                        if (comp != null) result.Add(comp);
                    }
                }
                catch { }
            }

            return result;
        }

        public static object GetLocalPlayerController()
        {
            var lp = LocalPlayerInstance;
            if (lp == null) return null;
            return GetFieldValue<object>(lp, "PlayerController", 0x70);
        }

        public static Camera GetPlayerCamera(object controller)
        {
            if (controller == null) return MainCamera;

            var t = PlayerControllerType;
            if (t != null)
            {
                var camField = t.GetField("m_PlayerCamera",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (camField != null)
                {
                    var cam = camField.GetValue(controller);
                    if (cam != null)
                    {
                        var camComp = (cam as Component);
                        if (camComp != null) return camComp.GetComponent<Camera>();

                        var camProp = cam.GetType().GetProperty("Camera",
                            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                        if (camProp != null) return camProp.GetValue(cam) as Camera;
                    }
                }
            }

            return MainCamera;
        }

        public static T GetFieldValue<T>(object obj, string fieldName, int fallbackOffset = -1)
        {
            if (obj == null) return default;

            var t = obj.GetType();
            var fi = t.GetField(fieldName,
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (fi != null)
            {
                try { return (T)fi.GetValue(obj); }
                catch { }
            }

            if (fallbackOffset > 0)
            {
                try
                {
                    foreach (var f in t.GetFields(
                        BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
                    {
                        if (f.Name == fieldName)
                        {
                            return (T)f.GetValue(obj);
                        }
                    }
                }
                catch { }
            }

            return default;
        }

        public static object GetFieldValue(object obj, string fieldName, int fallbackOffset = -1)
        {
            if (obj == null) return null;

            var t = obj.GetType();
            var fi = t.GetField(fieldName,
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
            if (fi != null)
            {
                try { return fi.GetValue(obj); }
                catch { }
            }

            return null;
        }

        public static bool IsGameReady()
        {
            return LocalPlayerInstance != null && MainCamera != null;
        }

        public static bool IsTeammate(int camp1, int camp2)
        {
            return camp1 == camp2 && camp1 != -1 && camp1 != 0;
        }

        public static bool IsEnemy(int camp1, int camp2)
        {
            return !IsTeammate(camp1, camp2);
        }
    }
}
