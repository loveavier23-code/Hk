using System;
using UnityEngine;
using InternalModMenu.Utils;

namespace InternalModMenu.Features
{
    public class MenuUI : MonoBehaviour
    {
        public static bool Visible = false;

        private Rect _menuRect = new Rect(20, 60, 280, 520);
        private Vector2 _scrollPos;
        private int _tabIndex = 0;
        private readonly string[] _tabs = { "ESP", "Aimbot", "Misc" };

        private GUIStyle _windowStyle;
        private GUIStyle _tabStyle;
        private GUIStyle _tabStyleActive;
        private GUIStyle _toggleStyle;
        private GUIStyle _labelStyle;
        private GUIStyle _sliderStyle;
        private GUIStyle _buttonStyle;
        private bool _stylesReady;

        private float GUISpace => 4f;
        private float GUIHalfW => _menuRect.width * 0.52f;

        public void OnGUI()
        {
            if (!Visible) return;

            InitStyles();

            _menuRect = GUI.Window(0, _menuRect, DrawMenuWindow, "ENI Mod Menu", _windowStyle);
        }

        private void DrawMenuWindow(int id)
        {
            DrawTabs();

            _scrollPos = GUILayout.BeginScrollView(_scrollPos, GUILayout.ExpandHeight(true));
            {
                switch (_tabIndex)
                {
                    case 0: DrawESPTab(); break;
                    case 1: DrawAimbotTab(); break;
                    case 2: DrawMiscTab(); break;
                }
            }
            GUILayout.EndScrollView();

            GUI.DragWindow(new Rect(0, 0, _menuRect.width, 20));
        }

        private void DrawTabs()
        {
            GUILayout.BeginHorizontal();
            for (int i = 0; i < _tabs.Length; i++)
            {
                var style = (i == _tabIndex) ? _tabStyleActive : _tabStyle;
                if (GUILayout.Button(_tabs[i], style, GUILayout.Height(24)))
                    _tabIndex = i;
            }
            GUILayout.EndHorizontal();
            GUILayout.Space(4);
        }

        private void DrawESPTab()
        {
            ESP.Enabled = Toggle("ESP Enabled", ESP.Enabled);
            GUILayout.Space(GUISpace);

            ESP.BoxESP = Toggle("Box ESP", ESP.BoxESP);
            ESP.NameESP = Toggle("Name ESP", ESP.NameESP);
            ESP.HealthESP = Toggle("Health Bar", ESP.HealthESP);
            ESP.DistanceESP = Toggle("Distance", ESP.DistanceESP);
            ESP.Snaplines = Toggle("Snaplines", ESP.Snaplines);
            ESP.ShowTeammates = Toggle("Show Teammates", ESP.ShowTeammates);
            GUILayout.Space(GUISpace);

            GUILayout.BeginHorizontal();
            GUILayout.Label("Max Distance:", _labelStyle, GUILayout.Width(90));
            ESP.MaxESPDistance = (float)Math.Round(GUILayout.HorizontalSlider(ESP.MaxESPDistance, 10f, 1000f, GUILayout.Width(150)), 0);
            GUILayout.Label($"{ESP.MaxESPDistance:F0}m", _labelStyle, GUILayout.Width(50));
            GUILayout.EndHorizontal();

            GUILayout.Space(6);
            GUILayout.Label("Box Color:", _labelStyle);
            DrawColorPicker(ref ESP.BoxColor);
        }

        private void DrawAimbotTab()
        {
            Aimbot.Enabled = Toggle("Aimbot Enabled", Aimbot.Enabled);
            GUILayout.Space(GUISpace);

            Aimbot.IgnoreTeammates = Toggle("Ignore Teammates", Aimbot.IgnoreTeammates);
            Aimbot.VisibleCheck = Toggle("Visibility Check", Aimbot.VisibleCheck);
            Aimbot.IgnoreDowned = Toggle("Ignore Downed", Aimbot.IgnoreDowned);
            Aimbot.DrawFOV = Toggle("Draw FOV Circle", Aimbot.DrawFOV);
            GUILayout.Space(GUISpace);

            GUILayout.BeginHorizontal();
            GUILayout.Label("Aim Bone:", _labelStyle, GUILayout.Width(80));
            Aimbot.AimBone = GUILayout.Toolbar(Aimbot.AimBone, new[] { "Head", "Chest", "Pelvis" }, GUILayout.Height(22));
            GUILayout.EndHorizontal();

            GUILayout.Space(GUISpace);

            GUILayout.BeginHorizontal();
            GUILayout.Label("Aim Key:", _labelStyle, GUILayout.Width(80));
            Aimbot.AimKey = GUILayout.Toolbar(Aimbot.AimKey, new[] { "Always", "ADS" }, GUILayout.Height(22));
            GUILayout.EndHorizontal();

            GUILayout.Space(GUISpace);

            GUILayout.BeginHorizontal();
            GUILayout.Label("Aim FOV:", _labelStyle, GUILayout.Width(80));
            Aimbot.AimFOV = (float)Math.Round(GUILayout.HorizontalSlider(Aimbot.AimFOV, 10f, 360f, GUILayout.Width(130)), 0);
            GUILayout.Label($"{Aimbot.AimFOV:F0}", _labelStyle, GUILayout.Width(40));
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            GUILayout.Label("Smoothness:", _labelStyle, GUILayout.Width(80));
            Aimbot.AimSmoothness = (float)Math.Round(GUILayout.HorizontalSlider(Aimbot.AimSmoothness, 0.5f, 20f, GUILayout.Width(130)), 1);
            GUILayout.Label($"{Aimbot.AimSmoothness:F1}", _labelStyle, GUILayout.Width(40));
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            GUILayout.Label("Max Distance:", _labelStyle, GUILayout.Width(80));
            Aimbot.MaxAimDistance = (float)Math.Round(GUILayout.HorizontalSlider(Aimbot.MaxAimDistance, 10f, 1000f, GUILayout.Width(130)), 0);
            GUILayout.Label($"{Aimbot.MaxAimDistance:F0}m", _labelStyle, GUILayout.Width(50));
            GUILayout.EndHorizontal();
        }

        private void DrawMiscTab()
        {
            GUILayout.Label("Misc Features", _labelStyle);
            GUILayout.Space(GUISpace);

            if (GUILayout.Button("Crosshair Overlay", _buttonStyle, GUILayout.Height(28)))
                DrawCrosshair = !DrawCrosshair;

            GUILayout.Space(6);
            GUILayout.Label("Menu Key: Insert", _labelStyle);
            GUILayout.Label("Toggle with Insert key", _labelStyle);
        }

        private bool DrawCrosshair = false;

        private bool Toggle(string label, bool value)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(label, _labelStyle, GUILayout.Width(130));
            bool result = GUILayout.Toggle(value, "", _toggleStyle, GUILayout.Width(30));
            GUILayout.EndHorizontal();
            return result;
        }

        private void DrawColorPicker(ref Color color)
        {
            GUILayout.BeginHorizontal();

            GUILayout.Label("R:", _labelStyle, GUILayout.Width(15));
            float r = GUILayout.HorizontalSlider(color.r, 0f, 1f, GUILayout.Width(70));
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            GUILayout.Label("G:", _labelStyle, GUILayout.Width(15));
            float g = GUILayout.HorizontalSlider(color.g, 0f, 1f, GUILayout.Width(70));
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            GUILayout.Label("B:", _labelStyle, GUILayout.Width(15));
            float b = GUILayout.HorizontalSlider(color.b, 0f, 1f, GUILayout.Width(70));
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            GUILayout.Label("A:", _labelStyle, GUILayout.Width(15));
            float a = GUILayout.HorizontalSlider(color.a, 0f, 1f, GUILayout.Width(70));
            GUILayout.EndHorizontal();

            color = new Color(r, g, b, a);

            GUILayout.BeginHorizontal();
            GUILayout.Label("Preview:", _labelStyle, GUILayout.Width(60));
            GUI.color = color;
            GUILayout.Box("", GUILayout.Width(50), GUILayout.Height(18));
            GUI.color = Color.white;
            GUILayout.EndHorizontal();
        }

        private void InitStyles()
        {
            if (_stylesReady) return;

            _windowStyle = new GUIStyle(GUI.skin.window)
            {
                fontSize = 13,
                fontStyle = FontStyle.Bold,
                normal = { background = MakeTex(2, 2, new Color(0.08f, 0.08f, 0.12f, 0.92f)), textColor = Color.white },
                onNormal = { background = MakeTex(2, 2, new Color(0.1f, 0.1f, 0.14f, 0.92f)) }
            };

            _tabStyle = new GUIStyle(GUI.skin.button)
            {
                fontSize = 11,
                normal = { background = MakeTex(2, 2, new Color(0.15f, 0.15f, 0.2f, 0.9f)), textColor = Color.gray }
            };

            _tabStyleActive = new GUIStyle(_tabStyle)
            {
                normal = { background = MakeTex(2, 2, new Color(0.8f, 0.2f, 0.2f, 0.9f)), textColor = Color.white }
            };

            _toggleStyle = new GUIStyle(GUI.skin.toggle);

            _labelStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 11,
                normal = { textColor = Color.white }
            };

            _buttonStyle = new GUIStyle(GUI.skin.button)
            {
                fontSize = 11,
                normal = { background = MakeTex(2, 2, new Color(0.2f, 0.2f, 0.3f, 0.9f)), textColor = Color.white },
                hover = { background = MakeTex(2, 2, new Color(0.3f, 0.3f, 0.4f, 0.9f)) }
            };

            _stylesReady = true;
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
