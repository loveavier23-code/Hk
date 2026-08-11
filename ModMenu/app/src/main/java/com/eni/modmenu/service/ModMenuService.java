package com.eni.modmenu.service;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import androidx.core.app.NotificationCompat;
import com.eni.modmenu.R;
import com.eni.modmenu.features.GameMemoryManager;
import com.eni.modmenu.features.ModFeatures;
import com.eni.modmenu.ui.MainActivity;
import com.eni.modmenu.ui.OverlayView;
import com.eni.modmenu.utils.Logger;

public class ModMenuService extends Service {

    private static final String CHANNEL_ID = "modmenu_channel";
    private static final int NOTIFICATION_ID = 1;

    private OverlayView overlayView;
    private GameMemoryManager memoryManager;
    private ModFeatures modFeatures;
    private Thread monitorThread;
    private volatile boolean running = false;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        memoryManager = new GameMemoryManager(this);
        overlayView = new OverlayView(this);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Logger.i("ModMenuService started");

        Notification notification = buildNotification();
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIFICATION_ID, notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        } else {
            startForeground(NOTIFICATION_ID, notification);
        }

        overlayView.show();
        startMonitorThread();

        return START_STICKY;
    }

    private void startMonitorThread() {
        running = true;
        monitorThread = new Thread(() -> {
            while (running) {
                try {
                    // Poll for target game every 2 seconds
                    if (modFeatures == null || !modFeatures.isRunning()) {
                        if (memoryManager.findTargetProcess()) {
                            Logger.i("Game found: " + memoryManager.getTargetPackage());
                            startModding();
                        }
                    }

                    // Verify target game is still running
                    if (modFeatures != null && modFeatures.isRunning()) {
                        if (!isProcessAlive(memoryManager.getTargetPid())) {
                            Logger.i("Target game closed, stopping mods");
                            stopModding();
                        }
                    }

                    Thread.sleep(2000);
                } catch (InterruptedException e) {
                    break;
                }
            }
        }, "Monitor-Thread");
        monitorThread.setDaemon(true);
        monitorThread.start();
    }

    private void startModding() {
        if (modFeatures != null) {
            modFeatures.stopModLoop();
        }

        modFeatures = new ModFeatures(
            memoryManager.getTargetPid(),
            memoryManager.getUnityModuleBase(),
            memoryManager.getGameAssemblyBase()
        );

        modFeatures.findOffsets();
        modFeatures.startModLoop();

        overlayView.setModFeatures(modFeatures);
        overlayView.updateStatus("Connected: " + memoryManager.getTargetPackage());
    }

    private void stopModding() {
        if (modFeatures != null) {
            modFeatures.stopModLoop();
            modFeatures = null;
        }
        overlayView.setModFeatures(null);
        overlayView.updateStatus("Waiting for game...");
    }

    private boolean isProcessAlive(int pid) {
        if (pid <= 0) return false;
        try {
            java.io.File procDir = new java.io.File("/proc/" + pid);
            return procDir.exists();
        } catch (Exception e) {
            return false;
        }
    }

    @Override
    public void onDestroy() {
        running = false;
        if (monitorThread != null) monitorThread.interrupt();
        if (modFeatures != null) modFeatures.stopModLoop();
        if (overlayView != null) overlayView.hide();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Mod Menu Service",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Mod menu is running");
            NotificationManager manager = getSystemService(NotificationManager.class);
            manager.createNotificationChannel(channel);
        }
    }

    private Notification buildNotification() {
        Intent intent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
        );

        return new NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Mod Menu Active")
            .setContentText("Tap to open settings")
            .setSmallIcon(R.drawable.ic_notification)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build();
    }
}
