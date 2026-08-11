package com.eni.modmenu.ui;

import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import com.eni.modmenu.R;
import com.eni.modmenu.service.ModMenuService;
import com.eni.modmenu.utils.Prefs;

public class MainActivity extends AppCompatActivity {

    private Button btnStart, btnStop;
    private TextView tvStatus;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        btnStart = findViewById(R.id.btn_start);
        btnStop = findViewById(R.id.btn_stop);
        tvStatus = findViewById(R.id.tv_status);

        if (!Settings.canDrawOverlays(this)) {
            tvStatus.setText("Overlay permission required");
            btnStart.setText("Grant Permission");
            btnStop.setEnabled(false);
        } else if (Prefs.isServiceRunning(this)) {
            updateUI(true);
        } else {
            updateUI(false);
        }

        btnStart.setOnClickListener(v -> {
            if (!Settings.canDrawOverlays(this)) {
                Intent intent = new Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName())
                );
                startActivity(intent);
            } else {
                Intent serviceIntent = new Intent(this, ModMenuService.class);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    startForegroundService(serviceIntent);
                } else {
                    startService(serviceIntent);
                }
                Prefs.setServiceRunning(this, true);
                updateUI(true);
            }
        });

        btnStop.setOnClickListener(v -> {
            Intent serviceIntent = new Intent(this, ModMenuService.class);
            stopService(serviceIntent);
            Prefs.setServiceRunning(this, false);
            updateUI(false);
        });
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (!Settings.canDrawOverlays(this)) {
            tvStatus.setText("Overlay permission required");
            btnStart.setText("Grant Permission");
        } else if (Prefs.isServiceRunning(this)) {
            updateUI(true);
        }
    }

    private void updateUI(boolean running) {
        if (running) {
            tvStatus.setText("Mod Menu Active");
            btnStart.setEnabled(false);
            btnStop.setEnabled(true);
        } else {
            tvStatus.setText("Mod Menu Stopped");
            btnStart.setEnabled(true);
            btnStop.setEnabled(false);
        }
    }
}
