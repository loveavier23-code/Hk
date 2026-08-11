package com.eni.modmenu.utils;

import android.content.Context;
import android.content.SharedPreferences;

public class Prefs {
    private static final String NAME = "modmenu_prefs";
    private static final String KEY_SERVICE = "service_running";
    private static final String KEY_GODMODE = "mod_godmode";
    private static final String KEY_HIGHDAMAGE = "mod_highdamage";
    private static final String KEY_UNLIMAMMO = "mod_unlim_ammo";
    private static final String KEY_NORECOIL = "mod_norecoil";
    private static final String KEY_NOSPREAD = "mod_nospread";
    private static final String KEY_SPEEDHACK = "mod_speedhack";
    private static final String KEY_ESP = "mod_esp";
    private static final String KEY_AIMBOT = "mod_aimbot";
    private static final String KEY_RAPIDFIRE = "mod_rapidfire";

    private static SharedPreferences get(Context ctx) {
        return ctx.getSharedPreferences(NAME, Context.MODE_PRIVATE);
    }

    public static boolean isServiceRunning(Context ctx) {
        return get(ctx).getBoolean(KEY_SERVICE, false);
    }

    public static void setServiceRunning(Context ctx, boolean v) {
        get(ctx).edit().putBoolean(KEY_SERVICE, v).apply();
    }

    public static boolean isGodMode(Context ctx) { return get(ctx).getBoolean(KEY_GODMODE, false); }
    public static void setGodMode(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_GODMODE, v).apply(); }

    public static boolean isHighDamage(Context ctx) { return get(ctx).getBoolean(KEY_HIGHDAMAGE, false); }
    public static void setHighDamage(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_HIGHDAMAGE, v).apply(); }

    public static boolean isUnlimAmmo(Context ctx) { return get(ctx).getBoolean(KEY_UNLIMAMMO, false); }
    public static void setUnlimAmmo(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_UNLIMAMMO, v).apply(); }

    public static boolean isNoRecoil(Context ctx) { return get(ctx).getBoolean(KEY_NORECOIL, false); }
    public static void setNoRecoil(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_NORECOIL, v).apply(); }

    public static boolean isNoSpread(Context ctx) { return get(ctx).getBoolean(KEY_NOSPREAD, false); }
    public static void setNoSpread(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_NOSPREAD, v).apply(); }

    public static boolean isSpeedHack(Context ctx) { return get(ctx).getBoolean(KEY_SPEEDHACK, false); }
    public static void setSpeedHack(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_SPEEDHACK, v).apply(); }

    public static boolean isESP(Context ctx) { return get(ctx).getBoolean(KEY_ESP, false); }
    public static void setESP(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_ESP, v).apply(); }

    public static boolean isAimbot(Context ctx) { return get(ctx).getBoolean(KEY_AIMBOT, false); }
    public static void setAimbot(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_AIMBOT, v).apply(); }

    public static boolean isRapidFire(Context ctx) { return get(ctx).getBoolean(KEY_RAPIDFIRE, false); }
    public static void setRapidFire(Context ctx, boolean v) { get(ctx).edit().putBoolean(KEY_RAPIDFIRE, v).apply(); }
}
