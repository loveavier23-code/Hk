package com.eni.modmenu.features;

import com.eni.modmenu.native.NativeLib;
import com.eni.modmenu.utils.Logger;

public class ModFeatures {
    private final int pid;
    private final long unityBase;
    private final long gameAssemblyBase;
    private boolean godMode = false;
    private boolean highDamage = false;
    private boolean unlimAmmo = false;
    private boolean noRecoil = false;
    private boolean noSpread = false;
    private boolean speedHack = false;
    private boolean esp = false;
    private boolean aimbot = false;
    private boolean rapidFire = false;

    // Typical offsets (to be updated via AOB scan per game version)
    private long offsetHealth = -1;
    private long offsetMaxHealth = -1;
    private long offsetDamageMultiplier = -1;
    private long offsetAmmo = -1;
    private long offsetRecoilX = -1;
    private long offsetRecoilY = -1;
    private long offsetSpread = -1;
    private long offsetSpeed = -1;
    private long offsetFireRate = -1;

    private volatile boolean running = false;
    private Thread modThread;

    public ModFeatures(int pid, long unityBase, long gameAssemblyBase) {
        this.pid = pid;
        this.unityBase = unityBase;
        this.gameAssemblyBase = gameAssemblyBase;
    }

    public void findOffsets() {
        Logger.i("Scanning for mod offsets...");

        // AOB pattern for health (typical: access to MonoBehaviour health field)
        // These patterns vary per game version; run dump analysis
        byte[] healthPattern = {
            (byte)0x00, (byte)0x00, (byte)0x80, (byte)0x3F  // float 1.0 (often used as health multiplier)
        };
        String healthMask = "xxxx";

        // Scan for damage multiplier patterns
        byte[] damagePattern = {
            (byte)0x00, (byte)0x00, (byte)0x00, (byte)0x00,
            (byte)0x00, (byte)0x00, (byte)0x80, (byte)0x3F
        };
        String damageMask = "xxxxxxxx";

        // Scan in libil2cpp.so or Assembly-CSharp memory range
        long scanStart = gameAssemblyBase > 0 ? gameAssemblyBase : unityBase;
        long scanEnd = NativeLib.getModuleEnd(pid, "libil2cpp.so");
        if (scanEnd <= 0) {
            scanEnd = NativeLib.getModuleEnd(pid, "libunity.so");
        }
        if (scanEnd <= 0) {
            scanEnd = scanStart + 0x4000000; // 64MB default scan range
        }

        long result = NativeLib.aobScan(pid, scanStart, scanEnd, healthPattern, healthMask);
        if (result > 0) {
            offsetHealth = result - scanStart;
            Logger.i("Health offset found: 0x" + Long.toHexString(offsetHealth));
        }

        result = NativeLib.aobScan(pid, scanStart, scanEnd, damagePattern, damageMask);
        if (result > 0) {
            offsetDamageMultiplier = result - scanStart;
            Logger.i("Damage offset found: 0x" + Long.toHexString(offsetDamageMultiplier));
        }

        Logger.i("Offset scan complete");
    }

    public void startModLoop() {
        running = true;
        modThread = new Thread(() -> {
            Logger.i("Mod loop started");
            while (running) {
                try {
                    applyMods();
                    Thread.sleep(100); // 10x per second
                } catch (Exception e) {
                    Logger.e("Mod loop error: " + e.getMessage());
                }
            }
        }, "ModLoop-Thread");
        modThread.setDaemon(true);
        modThread.start();
    }

    public void stopModLoop() {
        running = false;
        if (modThread != null) {
            modThread.interrupt();
        }
    }

    private void applyMods() {
        if (pid <= 0) return;

        if (godMode && offsetHealth > 0) {
            // Freeze health at max value
            long healthAddr = gameAssemblyBase + offsetHealth;
            NativeLib.writeFloat(pid, healthAddr, 9999.0f);
        }

        if (highDamage && offsetDamageMultiplier > 0) {
            long damageAddr = gameAssemblyBase + offsetDamageMultiplier;
            NativeLib.writeFloat(pid, damageAddr, 100.0f);
        }

        if (unlimAmmo && offsetAmmo > 0) {
            long ammoAddr = gameAssemblyBase + offsetAmmo;
            NativeLib.writeInt(pid, ammoAddr, 999);
        }

        if (noRecoil && offsetRecoilX > 0 && offsetRecoilY > 0) {
            long recoilXAddr = gameAssemblyBase + offsetRecoilX;
            long recoilYAddr = gameAssemblyBase + offsetRecoilY;
            NativeLib.writeFloat(pid, recoilXAddr, 0.0f);
            NativeLib.writeFloat(pid, recoilYAddr, 0.0f);
        }

        if (noSpread && offsetSpread > 0) {
            long spreadAddr = gameAssemblyBase + offsetSpread;
            NativeLib.writeFloat(pid, spreadAddr, 0.0f);
        }

        if (speedHack && offsetSpeed > 0) {
            long speedAddr = gameAssemblyBase + offsetSpeed;
            NativeLib.writeFloat(pid, speedAddr, 30.0f);
        }

        if (rapidFire && offsetFireRate > 0) {
            long fireRateAddr = gameAssemblyBase + offsetFireRate;
            NativeLib.writeFloat(pid, fireRateAddr, 0.01f);
        }
    }

    // Toggle controls
    public void setGodMode(boolean v) { this.godMode = v; }
    public void setHighDamage(boolean v) { this.highDamage = v; }
    public void setUnlimAmmo(boolean v) { this.unlimAmmo = v; }
    public void setNoRecoil(boolean v) { this.noRecoil = v; }
    public void setNoSpread(boolean v) { this.noSpread = v; }
    public void setSpeedHack(boolean v) { this.speedHack = v; }
    public void setESP(boolean v) { this.esp = v; }
    public void setAimbot(boolean v) { this.aimbot = v; }
    public void setRapidFire(boolean v) { this.rapidFire = v; }

    public boolean isRunning() { return running; }
}
