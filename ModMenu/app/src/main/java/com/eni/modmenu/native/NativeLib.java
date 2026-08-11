package com.eni.modmenu.native;

public class NativeLib {
    static {
        System.loadLibrary("modmenu");
    }

    // Process operations
    public static native int findProcess(String packageName);
    public static native long getModuleBase(int pid, String moduleName);
    public static native long getModuleEnd(int pid, String moduleName);

    // Memory read
    public static native byte[] readMemory(int pid, long address, int size);
    public static native int readInt(int pid, long address);
    public static native long readLong(int pid, long address);
    public static native float readFloat(int pid, long address);
    public static native double readDouble(int pid, long address);

    // Memory write
    public static native boolean writeInt(int pid, long address, int value);
    public static native boolean writeLong(int pid, long address, long value);
    public static native boolean writeFloat(int pid, long address, float value);
    public static native boolean writeDouble(int pid, long address, double value);
    public static native boolean writeBytes(int pid, long address, byte[] data);

    // Pattern scan (AOB scan)
    public static native long aobScan(int pid, long start, long end, byte[] pattern, String mask);

    // Virtual protect
    public static native boolean makeWritable(int pid, long address, long size);

    // Force write through ptrace (bypasses memory protection)
    public static native boolean ptraceWrite(int pid, long address, long value, int size);
    public static native boolean ptraceAttach(int pid);
    public static native boolean ptraceDetach(int pid);
}
