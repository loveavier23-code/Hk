package com.eni.modmenu.features;

import android.app.ActivityManager;
import android.content.Context;
import com.eni.modmenu.native.NativeLib;
import com.eni.modmenu.utils.Logger;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.List;

public class GameMemoryManager {
    private final Context context;
    private int targetPid = -1;
    private long unityModuleBase = -1;
    private long gameAssemblyBase = -1;
    private String targetPackage = "";

    // Common game package names to try
    private static final String[] KNOWN_GAMES = {
        "com.tencent.ig",           // PUBG Mobile
        "com.pubg.imobile",         // PUBG Mobile KR
        "com.dts.freefireth",       // Free Fire
        "com.dts.freefiremax",      // Free Fire MAX
        "com.activision.callofduty.shooter", // COD Mobile
        "com.garena.game.codm",     // COD Mobile Garena
    };

    public GameMemoryManager(Context context) {
        this.context = context;
    }

    public boolean findTargetProcess() {
        Logger.i("Searching for target game process...");

        // Check running processes for known games
        ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
        List<ActivityManager.RunningAppProcessInfo> processes = am.getRunningAppProcesses();
        if (processes != null) {
            for (ActivityManager.RunningAppProcessInfo process : processes) {
                for (String known : KNOWN_GAMES) {
                    if (process.processName.startsWith(known)) {
                        targetPid = process.pid;
                        targetPackage = known;
                        Logger.i("Found target: " + known + " PID: " + targetPid);
                        scanModules();
                        return true;
                    }
                }
            }
        }

        // Fallback: try /proc scan
        return scanProcForGame();
    }

    private boolean scanProcForGame() {
        try {
            java.io.File proc = new java.io.File("/proc");
            String[] dirs = proc.list();
            if (dirs == null) return false;

            for (String dir : dirs) {
                try {
                    int pid = Integer.parseInt(dir);
                    String cmdline = readFile("/proc/" + pid + "/cmdline");
                    for (String known : KNOWN_GAMES) {
                        if (cmdline.contains(known)) {
                            targetPid = pid;
                            targetPackage = known;
                            Logger.i("Found target in /proc: " + known + " PID: " + pid);
                            scanModules();
                            return true;
                        }
                    }
                } catch (NumberFormatException ignored) {}
            }
        } catch (Exception e) {
            Logger.e("Proc scan error: " + e.getMessage());
        }
        return false;
    }

    private void scanModules() {
        if (targetPid <= 0) return;

        Logger.i("Scanning modules for PID: " + targetPid);

        // Find libil2cpp.so (IL2CPP) or libunity.so (Mono) base addresses
        unityModuleBase = NativeLib.getModuleBase(targetPid, "libunity.so");
        if (unityModuleBase > 0) {
            Logger.i("libunity.so base: 0x" + Long.toHexString(unityModuleBase));
        }

        gameAssemblyBase = NativeLib.getModuleBase(targetPid, "libil2cpp.so");
        if (gameAssemblyBase > 0) {
            Logger.i("libil2cpp.so base: 0x" + Long.toHexString(gameAssemblyBase));
        }

        // For Mono Unity games, also check libmono.so
        if (gameAssemblyBase <= 0) {
            gameAssemblyBase = NativeLib.getModuleBase(targetPid, "libmono.so");
            if (gameAssemblyBase > 0) {
                Logger.i("libmono.so base: 0x" + Long.toHexString(gameAssemblyBase));
            }
        }

        // Fallback: try to find any relevant module
        if (gameAssemblyBase <= 0) {
            String maps = readMaps(targetPid);
            if (maps.contains("libil2cpp.so")) {
                gameAssemblyBase = parseBaseFromMaps(maps, "libil2cpp.so");
            } else if (maps.contains("libunity.so")) {
                gameAssemblyBase = parseBaseFromMaps(maps, "libunity.so");
            }
        }
    }

    private String readMaps(int pid) {
        try {
            StringBuilder sb = new StringBuilder();
            BufferedReader br = new BufferedReader(new FileReader("/proc/" + pid + "/maps"));
            String line;
            while ((line = br.readLine()) != null) {
                if (line.contains(".so") || line.contains(".dll")) {
                    sb.append(line).append("\n");
                }
            }
            br.close();
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }

    private long parseBaseFromMaps(String maps, String libName) {
        for (String line : maps.split("\n")) {
            if (line.contains(libName)) {
                String addr = line.split("-")[0].trim();
                return Long.parseLong(addr, 16);
            }
        }
        return -1;
    }

    private String readFile(String path) {
        try {
            StringBuilder sb = new StringBuilder();
            BufferedReader br = new BufferedReader(new FileReader(path));
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line);
            }
            br.close();
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }

    public int getTargetPid() { return targetPid; }
    public long getUnityModuleBase() { return unityModuleBase; }
    public long getGameAssemblyBase() { return gameAssemblyBase; }
    public String getTargetPackage() { return targetPackage; }
    public boolean isGameFound() { return targetPid > 0; }

    public void refresh() {
        targetPid = -1;
        unityModuleBase = -1;
        gameAssemblyBase = -1;
        targetPackage = "";
        findTargetProcess();
    }
}
