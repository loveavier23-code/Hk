using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;
using InternalModMenu.Utils;

namespace InternalModMenu.Features
{
    public class Aimbot : MonoBehaviour
    {
        public static bool Enabled = false;
        public static bool VisibleCheck = true;
        public static bool IgnoreTeammates = true;
        public static bool IgnoreDowned = true;
        public static float AimFOV = 120f;
        public static float AimSmoothness = 5f;
        public static int AimBone = 0;
        public static int AimKey = 1;
        public static float MaxAimDistance = 300f;
        public static bool DrawFOV = true;

        private static readonly string[] _boneNames = { "Head", "Chest", "Pelvis" };
        private static readonly string[] _aimKeyNames = { "Always", "ADS Only" };

        private static Texture2D _fovTex;

        public void Awake()
        {
            _fovTex = new Texture2D(1, 1);
            _fovTex.SetPixel(0, 0, Color.white);
            _fovTex.Apply();
        }

        public void Update()
        {
            if (!Enabled) return;
            if (!GameUtils.IsGameReady()) return;

            bool shouldAim = AimKey == 0;
            if (AimKey == 1)
            {
                try
                {
                    shouldAim = Input.GetKey(KeyCode.Mouse1) || Input.GetMouseButton(1);
                    if (!shouldAim)
                        shouldAim = Input.touchCount == 2;
                }
                catch { }
            }

            if (!shouldAim) return;

            var target = FindBestTarget();
            if (target == null) return;

            AimAtTarget(target);
        }

        public void OnGUI()
        {
            if (!Enabled || !DrawFOV) return;

            Color fovColor = new Color(1f, 0f, 0f, 0.15f);
            float radius = AimFOV * 3f;

            GUI.color = fovColor;
            var centerX = Screen.width * 0.5f;
            var centerY = Screen.height * 0.5f;
            var rect = new Rect(centerX - radius, centerY - radius, radius * 2f, radius * 2f);

            DrawCircle(rect, fovColor);

            GUI.color = Color.white;
        }

        private object FindBestTarget()
        {
            var localCamp = GameUtils.GetLocalCamp();
            var localPawn = GameUtils.GetLocalPawn();
            var camera = Camera.main ?? Camera.current;
            if (camera == null || localPawn == null) return null;

            var pawns = GameUtils.GetAllPawns();
            var screenCenter = new Vector2(Screen.width * 0.5f, Screen.height * 0.5f);

            object bestTarget = null;
            float bestScore = float.MaxValue;

            foreach (var pawn in pawns)
            {
                if (pawn == null) continue;
                if (pawn == localPawn) continue;
                if (!GameUtils.IsPawnAlive(pawn)) continue;

                if (IgnoreTeammates)
                {
                    var camp = GameUtils.GetPawnCamp(pawn);
                    if (GameUtils.IsTeammate(localCamp, camp)) continue;
                }

                var distance = GameUtils.GetPawnDistance(pawn);
                if (distance > MaxAimDistance) continue;

                var targetPos = GetBonePosition(pawn, AimBone);
                var screenPos = camera.WorldToScreenPoint(targetPos);
                if (screenPos.z < 0.01f) continue;

                var screenPoint = new Vector2(screenPos.x, Screen.height - screenPos.y);
                float distFromCenter = Vector2.Distance(screenPoint, screenCenter);

                if (distFromCenter > AimFOV * 3f) continue;

                if (VisibleCheck)
                {
                    var localPos = GetBonePosition(localPawn, 0);
                    var dir = targetPos - localPos;
                    if (Physics.Raycast(localPos, dir.normalized, out var hit, dir.magnitude))
                    {
                        if (hit.collider != null)
                        {
                            var hitPawn = hit.collider.GetComponent(GameUtils.BRPlayerPawnType ?? GameUtils.PawnType ?? typeof(MonoBehaviour));
                            if (hitPawn == null || hitPawn != pawn) continue;
                        }
                    }
                }

                float score = distFromCenter + distance * 0.01f;
                if (score < bestScore)
                {
                    bestScore = score;
                    bestTarget = pawn;
                }
            }

            return bestTarget;
        }

        private void AimAtTarget(object target)
        {
            var localPawn = GameUtils.GetLocalPawn();
            var controller = GameUtils.GetLocalPlayerController();
            if (localPawn == null || controller == null) return;

            var targetPos = GetBonePosition(target, AimBone);
            var localPos = GetBonePosition(localPawn, 0);

            var aimDir = (targetPos - localPos).normalized;
            var aimRotation = Quaternion.LookRotation(aimDir);

            if (AimSmoothness > 0.5f)
            {
                var currentAim = GetCurrentAimRotation(controller, localPawn);
                if (currentAim != Quaternion.identity)
                {
                    aimRotation = Quaternion.Slerp(currentAim, aimRotation, Time.deltaTime * AimSmoothness * 10f);
                }
            }

            SetAimRotation(controller, localPawn, aimRotation);
        }

        private Quaternion GetCurrentAimRotation(object controller, object pawn)
        {
            try
            {
                var aimRot = GameUtils.GetFieldValue<Quaternion>(pawn, "m_AimRotation");
                if (aimRot != Quaternion.identity) return aimRot;

                var prop = pawn.GetType().GetProperty("AimRotation",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (prop != null)
                {
                    var val = prop.GetValue(pawn);
                    if (val is Quaternion q) return q;
                }
            }
            catch { }

            try
            {
                if (controller != null)
                {
                    var prop = controller.GetType().GetProperty("Rotation",
                        BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                    if (prop != null)
                    {
                        var val = prop.GetValue(controller);
                        if (val is Quaternion q) return q;
                    }
                }
            }
            catch { }

            return Quaternion.identity;
        }

        private void SetAimRotation(object controller, object pawn, Quaternion targetRotation)
        {
            try
            {
                var field = pawn.GetType().GetField("m_AimRotation",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (field != null)
                {
                    field.SetValue(pawn, targetRotation);
                    return;
                }
            }
            catch { }

            try
            {
                if (controller != null)
                {
                    var method = controller.GetType().GetMethod("SetControlRotation",
                        BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                    if (method != null)
                    {
                        var euler = targetRotation.eulerAngles;
                        method.Invoke(controller, new object[] { euler.y, euler.x });
                        return;
                    }
                }
            }
            catch { }

            try
            {
                var simField = pawn.GetType().GetField("m_SimulatedAimRotation",
                    BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if (simField != null)
                {
                    simField.SetValue(pawn, targetRotation);
                }
            }
            catch { }
        }

        private Vector3 GetBonePosition(object pawn, int boneIndex)
        {
            switch (boneIndex)
            {
                case 0:
                {
                    var head = GameUtils.GetFieldValue<Transform>(pawn, "m_HeadTransform", 0x600);
                    if (head != null) return head.position;
                    var pos = GameUtils.GetPawnPosition(pawn);
                    pos.y += 1.75f;
                    return pos;
                }
                case 1:
                {
                    var pos = GameUtils.GetPawnPosition(pawn);
                    pos.y += 1.2f;
                    var spineBone = GameUtils.GetFieldValue<Transform>(pawn, "m_SpineBone");
                    if (spineBone != null) return spineBone.position;
                    return pos;
                }
                case 2:
                {
                    var pos = GameUtils.GetPawnPosition(pawn);
                    pos.y += 0.9f;
                    var hipsBone = GameUtils.GetFieldValue<Transform>(pawn, "m_HipsBone");
                    if (hipsBone != null) return hipsBone.position;
                    return pos;
                }
                default:
                    return GetBonePosition(pawn, 0);
            }
        }

        private void DrawCircle(Rect rect, Color color)
        {
            int segments = 64;
            float centerX = rect.x + rect.width * 0.5f;
            float centerY = rect.y + rect.height * 0.5f;
            float radius = rect.width * 0.5f;

            for (int i = 0; i < segments; i++)
            {
                float angle1 = (float)i / segments * Mathf.PI * 2f;
                float angle2 = (float)(i + 1) / segments * Mathf.PI * 2f;

                float x1 = centerX + Mathf.Cos(angle1) * radius;
                float y1 = centerY + Mathf.Sin(angle1) * radius;
                float x2 = centerX + Mathf.Cos(angle2) * radius;
                float y2 = centerY + Mathf.Sin(angle2) * radius;

                DrawThinLine(x1, y1, x2, y2, color);
            }
        }

        private void DrawThinLine(float x1, float y1, float x2, float y2, Color color)
        {
            GUI.color = color;
            float angle = Mathf.Atan2(y2 - y1, x2 - x1) * Mathf.Rad2Deg;
            float dist = Vector2.Distance(new Vector2(x1, y1), new Vector2(x2, y2));
            GUIUtility.RotateAroundPivot(angle, new Vector2(x1, y1));
            GUI.DrawTexture(new Rect(x1, y1, dist, 1f), _fovTex);
            GUIUtility.RotateAroundPivot(-angle, new Vector2(x1, y1));
            GUI.color = Color.white;
        }
    }
}
