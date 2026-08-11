using System;
using System.Collections.Generic;
using UnityEngine;
using InternalModMenu.Utils;

namespace InternalModMenu.Features
{
    public class ESP : MonoBehaviour
    {
        public static bool Enabled = true;
        public static bool BoxESP = true;
        public static bool NameESP = true;
        public static bool HealthESP = true;
        public static bool DistanceESP = true;
        public static bool Snaplines = true;
        public static bool ShowTeammates = false;
        public static float MaxESPDistance = 500f;
        public static Color BoxColor = Color.red;
        public static Color TeamBoxColor = Color.cyan;

        private static readonly Color _healthHigh = Color.green;
        private static readonly Color _healthMid = Color.yellow;
        private static readonly Color _healthLow = Color.red;

        private static Texture2D _lineTex;
        private static Texture2D _whiteTex;

        private GUIStyle _nameStyle;
        private GUIStyle _distStyle;

        public void Awake()
        {
            _whiteTex = new Texture2D(1, 1);
            _whiteTex.SetPixel(0, 0, Color.white);
            _whiteTex.Apply();

            _lineTex = new Texture2D(1, 1);
            _lineTex.SetPixel(0, 0, Color.white);
            _lineTex.Apply();
        }

        public void OnGUI()
        {
            if (!Enabled) return;
            if (!GameUtils.IsGameReady()) return;

            InitStyles();

            var localCamp = GameUtils.GetLocalCamp();
            var localPawn = GameUtils.GetLocalPawn();
            var pawns = GameUtils.GetAllPawns();
            var camera = Camera.main ?? Camera.current;
            if (camera == null) return;

            foreach (var pawn in pawns)
            {
                if (pawn == null) continue;
                if (pawn == localPawn) continue;
                if (!GameUtils.IsPawnAlive(pawn)) continue;

                var camp = GameUtils.GetPawnCamp(pawn);
                bool isEnemy = GameUtils.IsEnemy(localCamp, camp);
                bool isTeammate = GameUtils.IsTeammate(localCamp, camp);

                if (!isEnemy && !isTeammate) continue;
                if (isTeammate && !ShowTeammates) continue;

                var headPos = GetHeadWorldPosition(pawn);
                var footPos = GameUtils.GetPawnPosition(pawn);
                var distance = GameUtils.GetPawnDistance(pawn);

                if (distance > MaxESPDistance) continue;

                var headScreen = camera.WorldToScreenPoint(headPos);
                var footScreen = camera.WorldToScreenPoint(footPos);

                if (headScreen.z < 0.01f) continue;

                float height = Mathf.Abs(headScreen.y - footScreen.y);
                float width = height * 0.55f;

                float x = headScreen.x - width * 0.5f;
                float y = Screen.height - headScreen.y;
                float w = width;
                float h = height;

                var color = isEnemy ? BoxColor : TeamBoxColor;

                if (Snaplines)
                    DrawLine(new Vector2(Screen.width * 0.5f, Screen.height),
                              new Vector2(footScreen.x, Screen.height - footScreen.y),
                              new Color(color.r, color.g, color.b, 0.4f), 1f);

                if (BoxESP)
                    DrawBox(x, y, w, h, color, 1.5f);

                if (HealthESP)
                {
                    float health = GameUtils.GetPawnHealth(pawn);
                    float maxHealth = 100f;
                    float healthPct = Mathf.Clamp01(health / maxHealth);

                    Color healthColor;
                    if (healthPct > 0.6f) healthColor = _healthHigh;
                    else if (healthPct > 0.3f) healthColor = _healthMid;
                    else healthColor = _healthLow;

                    float barX = x - 6f;
                    float barY = y;
                    float barW = 3f;
                    float barH = h;

                    DrawBox(barX, barY, barW, barH, new Color(0f, 0f, 0f, 0.5f), 0f);
                    DrawBox(barX, barY + barH * (1f - healthPct), barW, barH * healthPct, healthColor, 0f);
                }

                if (NameESP)
                {
                    string name = GameUtils.GetPawnName(pawn);
                    var nameRect = new Rect(x, y - 18f, w + 10f, 16f);
                    GUI.Label(nameRect, name, _nameStyle);
                }

                if (DistanceESP)
                {
                    string distText = $"{distance:F0}m";
                    var distRect = new Rect(x, y + h + 2f, w + 10f, 16f);
                    GUI.Label(distRect, distText, _distStyle);
                }
            }
        }

        private Vector3 GetHeadWorldPosition(object pawn)
        {
            var headTransform = GameUtils.GetFieldValue<Transform>(pawn, "m_HeadTransform", 0x600);
            if (headTransform != null)
                return headTransform.position;

            var footPos = GameUtils.GetPawnPosition(pawn);
            footPos.y += 1.8f;
            return footPos;
        }

        private void DrawBox(float x, float y, float w, float h, Color color, float thickness)
        {
            if (thickness <= 0f)
            {
                GUI.color = color;
                GUI.DrawTexture(new Rect(x, y, w, h), _whiteTex);
                GUI.color = Color.white;
                return;
            }

            DrawLine(new Vector2(x, y), new Vector2(x + w, y), color, thickness);
            DrawLine(new Vector2(x + w, y), new Vector2(x + w, y + h), color, thickness);
            DrawLine(new Vector2(x + w, y + h), new Vector2(x, y + h), color, thickness);
            DrawLine(new Vector2(x, y + h), new Vector2(x, y), color, thickness);
        }

        private void DrawLine(Vector2 start, Vector2 end, Color color, float thickness)
        {
            GUI.color = color;
            float angle = Mathf.Atan2(end.y - start.y, end.x - start.x) * Mathf.Rad2Deg + 90f;
            float length = Vector2.Distance(start, end);
            GUIUtility.RotateAroundPivot(angle, start);
            GUI.DrawTexture(new Rect(start.x, start.y - thickness * 0.5f, length, thickness), _lineTex);
            GUIUtility.RotateAroundPivot(-angle, start);
            GUI.color = Color.white;
        }

        private void InitStyles()
        {
            if (_nameStyle == null)
            {
                _nameStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = 12,
                    fontStyle = FontStyle.Bold,
                    alignment = TextAnchor.MiddleCenter,
                    normal = { textColor = Color.white }
                };
                _nameStyle.normal.background = MakeTex(1, 1, new Color(0, 0, 0, 0.4f));
            }

            if (_distStyle == null)
            {
                _distStyle = new GUIStyle(GUI.skin.label)
                {
                    fontSize = 11,
                    alignment = TextAnchor.MiddleCenter,
                    normal = { textColor = Color.white }
                };
                _distStyle.normal.background = MakeTex(1, 1, new Color(0, 0, 0, 0.4f));
            }
        }

        private Texture2D MakeTex(int w, int h, Color col)
        {
            var pix = new Color[w * h];
            for (int i = 0; i < pix.Length; i++) pix[i] = col;
            var tex = new Texture2D(w, h);
            tex.SetPixels(pix);
            tex.Apply();
            return tex;
        }
    }
}
