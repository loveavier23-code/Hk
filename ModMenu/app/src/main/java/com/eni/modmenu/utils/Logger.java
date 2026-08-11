package com.eni.modmenu.utils;

import android.util.Log;

public class Logger {
    private static final String TAG = "ModMenu";
    private static boolean debug = true;

    public static void d(String msg) {
        if (debug) Log.d(TAG, msg);
    }

    public static void e(String msg) {
        Log.e(TAG, msg);
    }

    public static void i(String msg) {
        Log.i(TAG, msg);
    }
}
