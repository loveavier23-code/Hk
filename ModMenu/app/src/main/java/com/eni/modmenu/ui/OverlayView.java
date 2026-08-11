package com.eni.modmenu.ui;

import android.content.Context;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.CompoundButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import com.eni.modmenu.R;
import com.eni.modmenu.features.ModFeatures;
import com.eni.modmenu.utils.Logger;
import com.eni.modmenu.utils.Prefs;

public class OverlayView {

    private final Context context;
    private final WindowManager windowManager;
    private WindowManager.LayoutParams layoutParams;
    private View overlayRoot;
    private boolean attached = false;

    private TextView tvStatus;
    private Switch swGodMode, swHighDamage, swUnlimAmmo, swNoRecoil;
    private Switch swNoSpread, swSpeedHack, swRapidFire, swESP, swAimbot;
    private ModFeatures modFeatures;

    // Dragging support
    private float initialX, initialY;
    private float initialTouchX, initialTouchY;

    public OverlayView(Context context) {
        this.context = context;
        this.windowManager = (WindowManager) context.getSystemService(Context.WINDOW_SERVICE);
        createLayoutParams();
        createView();
    }

    private void createLayoutParams() {
        int type;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            type = WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY;
        } else {
            type = WindowManager.LayoutParams.TYPE_PHONE;
        }

        layoutParams = new WindowManager.LayoutParams(
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.WRAP_CONTENT,
            type,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
            PixelFormat.TRANSLUCENT
        );
        layoutParams.gravity = Gravity.TOP | Gravity.START;
        layoutParams.x = 50;
        layoutParams.y = 200;
    }

    private void createView() {
        // Root container
        LinearLayout root = new LinearLayout(context);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(16, 12, 16, 12);
        root.setBackground(createBackground());

        // Header - draggable
        LinearLayout header = new LinearLayout(context);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setPadding(4, 8, 4, 8);

        tvStatus = new TextView(context);
        tvStatus.setText("Waiting for game...");
        tvStatus.setTextColor(Color.WHITE);
        tvStatus.setTextSize(11);

        LinearLayout headerBtn = new LinearLayout(context);
        TextView btnClose = new TextView(context);
        btnClose.setText("✕");
        btnClose.setTextColor(Color.RED);
        btnClose.setTextSize(16);
        btnClose.setPadding(24, 0, 0, 0);
        btnClose.setOnClickListener(v -> {
            if (modFeatures != null) modFeatures.stopModLoop();
            context.stopService(new android.content.Intent(context,
                com.eni.modmenu.service.ModMenuService.class));
        });

        headerBtn.addView(btnClose);
        header.addView(tvStatus);
        header.addView(headerBtn);
        root.addView(header);

        // Divider
        View divider = new View(context);
        divider.setLayoutParams(new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 2));
        divider.setBackgroundColor(Color.parseColor("#444444"));
        root.addView(divider);

        // Scrollable toggle list
        ScrollView scroll = new ScrollView(context);
        LinearLayout toggleContainer = new LinearLayout(context);
        toggleContainer.setOrientation(LinearLayout.VERTICAL);
        toggleContainer.setPadding(0, 8, 0, 0);

        swGodMode = createToggle("God Mode",
            Prefs.isGodMode(context), (btn, on) -> {
                Prefs.setGodMode(context, on);
                if (modFeatures != null) modFeatures.setGodMode(on);
            });
        toggleContainer.addView(swGodMode.getParent());

        swHighDamage = createToggle("High Damage",
            Prefs.isHighDamage(context), (btn, on) -> {
                Prefs.setHighDamage(context, on);
                if (modFeatures != null) modFeatures.setHighDamage(on);
            });
        toggleContainer.addView(swHighDamage.getParent());

        swUnlimAmmo = createToggle("Unlimited Ammo",
            Prefs.isUnlimAmmo(context), (btn, on) -> {
                Prefs.setUnlimAmmo(context, on);
                if (modFeatures != null) modFeatures.setUnlimAmmo(on);
            });
        toggleContainer.addView(swUnlimAmmo.getParent());

        swNoRecoil = createToggle("No Recoil",
            Prefs.isNoRecoil(context), (btn, on) -> {
                Prefs.setNoRecoil(context, on);
                if (modFeatures != null) modFeatures.setNoRecoil(on);
            });
        toggleContainer.addView(swNoRecoil.getParent());

        swNoSpread = createToggle("No Spread",
            Prefs.isNoSpread(context), (btn, on) -> {
                Prefs.setNoSpread(context, on);
                if (modFeatures != null) modFeatures.setNoSpread(on);
            });
        toggleContainer.addView(swNoSpread.getParent());

        swSpeedHack = createToggle("Speed Hack",
            Prefs.isSpeedHack(context), (btn, on) -> {
                Prefs.setSpeedHack(context, on);
                if (modFeatures != null) modFeatures.setSpeedHack(on);
            });
        toggleContainer.addView(swSpeedHack.getParent());

        swRapidFire = createToggle("Rapid Fire",
            Prefs.isRapidFire(context), (btn, on) -> {
                Prefs.setRapidFire(context, on);
                if (modFeatures != null) modFeatures.setRapidFire(on);
            });
        toggleContainer.addView(swRapidFire.getParent());

        swESP = createToggle("ESP / Wallhack",
            Prefs.isESP(context), (btn, on) -> {
                Prefs.setESP(context, on);
                if (modFeatures != null) modFeatures.setESP(on);
            });
        toggleContainer.addView(swESP.getParent());

        swAimbot = createToggle("Aimbot",
            Prefs.isAimbot(context), (btn, on) -> {
                Prefs.setAimbot(context, on);
                if (modFeatures != null) modFeatures.setAimbot(on);
            });
        toggleContainer.addView(swAimbot.getParent());

        scroll.addView(toggleContainer);
        root.addView(scroll);

        // Drag handler on header
        header.setOnTouchListener((v, event) -> {
            switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN:
                    initialX = layoutParams.x;
                    initialY = layoutParams.y;
                    initialTouchX = event.getRawX();
                    initialTouchY = event.getRawY();
                    return true;
                case MotionEvent.ACTION_MOVE:
                    layoutParams.x = (int) (initialX + event.getRawX() - initialTouchX);
                    layoutParams.y = (int) (initialY + event.getRawY() - initialTouchY);
                    if (attached) {
                        windowManager.updateViewLayout(overlayRoot, layoutParams);
                    }
                    return true;
            }
            return false;
        });

        overlayRoot = root;
    }

    private Switch createToggle(String label, boolean initialState,
                                CompoundButton.OnCheckedChangeListener listener) {
        LinearLayout row = new LinearLayout(context);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setPadding(4, 6, 4, 6);
        row.setGravity(Gravity.CENTER_VERTICAL);

        TextView labelView = new TextView(context);
        labelView.setText(label);
        labelView.setTextColor(Color.WHITE);
        labelView.setTextSize(12);
        LinearLayout.LayoutParams labelParams = new LinearLayout.LayoutParams(
            0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.0f);
        labelView.setLayoutParams(labelParams);

        Switch sw = new Switch(context);
        sw.setChecked(initialState);
        sw.setOnCheckedChangeListener(listener);

        row.addView(labelView);
        row.addView(sw);
        return sw;
    }

    private GradientDrawable createBackground() {
        GradientDrawable bg = new GradientDrawable();
        bg.setShape(GradientDrawable.RECTANGLE);
        bg.setCornerRadius(16);
        bg.setColor(Color.parseColor("#CC1A1A2E"));
        bg.setStroke(2, Color.parseColor("#555555"));
        return bg;
    }

    public void show() {
        if (!attached && overlayRoot != null) {
            windowManager.addView(overlayRoot, layoutParams);
            attached = true;
            restoreToggleStates();
            Logger.i("Overlay shown");
        }
    }

    public void hide() {
        if (attached && overlayRoot != null) {
            windowManager.removeView(overlayRoot);
            attached = false;
            Logger.i("Overlay hidden");
        }
    }

    public void setModFeatures(ModFeatures mf) {
        this.modFeatures = mf;
        if (mf != null) {
            // Apply current toggle states to new mod session
            mf.setGodMode(swGodMode.isChecked());
            mf.setHighDamage(swHighDamage.isChecked());
            mf.setUnlimAmmo(swUnlimAmmo.isChecked());
            mf.setNoRecoil(swNoRecoil.isChecked());
            mf.setNoSpread(swNoSpread.isChecked());
            mf.setSpeedHack(swSpeedHack.isChecked());
            mf.setRapidFire(swRapidFire.isChecked());
            mf.setESP(swESP.isChecked());
            mf.setAimbot(swAimbot.isChecked());
        }
    }

    public void updateStatus(String status) {
        if (tvStatus != null && attached) {
            tvStatus.post(() -> tvStatus.setText(status));
        }
    }

    private void restoreToggleStates() {
        swGodMode.setChecked(Prefs.isGodMode(context));
        swHighDamage.setChecked(Prefs.isHighDamage(context));
        swUnlimAmmo.setChecked(Prefs.isUnlimAmmo(context));
        swNoRecoil.setChecked(Prefs.isNoRecoil(context));
        swNoSpread.setChecked(Prefs.isNoSpread(context));
        swSpeedHack.setChecked(Prefs.isSpeedHack(context));
        swRapidFire.setChecked(Prefs.isRapidFire(context));
        swESP.setChecked(Prefs.isESP(context));
        swAimbot.setChecked(Prefs.isAimbot(context));
    }
}
