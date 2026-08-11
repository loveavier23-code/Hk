#include <jni.h>
#include <android/log.h>
#include "memory.h"
#include "process.h"
#include "aob_scanner.h"

#define TAG "ModMenuNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

extern "C" {

JNIEXPORT jint JNICALL
Java_com_eni_modmenu_native_NativeLib_findProcess(JNIEnv *env, jclass, jstring packageName) {
    const char *pkg = env->GetStringUTFChars(packageName, nullptr);
    int pid = find_process(pkg);
    env->ReleaseStringUTFChars(packageName, pkg);
    LOGI("findProcess(%s) = %d", pkg, pid);
    return pid;
}

JNIEXPORT jlong JNICALL
Java_com_eni_modmenu_native_NativeLib_getModuleBase(JNIEnv *env, jclass, jint pid, jstring moduleName) {
    const char *mod = env->GetStringUTFChars(moduleName, nullptr);
    long base = get_module_base(pid, mod);
    env->ReleaseStringUTFChars(moduleName, mod);
    LOGI("getModuleBase(%d, %s) = 0x%lx", pid, mod, base);
    return base;
}

JNIEXPORT jlong JNICALL
Java_com_eni_modmenu_native_NativeLib_getModuleEnd(JNIEnv *env, jclass, jint pid, jstring moduleName) {
    const char *mod = env->GetStringUTFChars(moduleName, nullptr);
    long end = get_module_end(pid, mod);
    env->ReleaseStringUTFChars(moduleName, mod);
    return end;
}

JNIEXPORT jbyteArray JNICALL
Java_com_eni_modmenu_native_NativeLib_readMemory(JNIEnv *env, jclass, jint pid, jlong address, jint size) {
    if (size <= 0 || size > 4096) return nullptr;
    uint8_t *buffer = new uint8_t[size];
    bool ok = read_memory(pid, address, buffer, size);
    if (!ok) {
        delete[] buffer;
        return nullptr;
    }
    jbyteArray result = env->NewByteArray(size);
    env->SetByteArrayRegion(result, 0, size, (const jbyte*)buffer);
    delete[] buffer;
    return result;
}

JNIEXPORT jint JNICALL
Java_com_eni_modmenu_native_NativeLib_readInt(JNIEnv *, jclass, jint pid, jlong address) {
    int value = 0;
    read_memory(pid, address, &value, sizeof(value));
    return value;
}

JNIEXPORT jlong JNICALL
Java_com_eni_modmenu_native_NativeLib_readLong(JNIEnv *, jclass, jint pid, jlong address) {
    long value = 0;
    read_memory(pid, address, &value, sizeof(value));
    return value;
}

JNIEXPORT jfloat JNICALL
Java_com_eni_modmenu_native_NativeLib_readFloat(JNIEnv *, jclass, jint pid, jlong address) {
    float value = 0.0f;
    read_memory(pid, address, &value, sizeof(value));
    return value;
}

JNIEXPORT jdouble JNICALL
Java_com_eni_modmenu_native_NativeLib_readDouble(JNIEnv *, jclass, jint pid, jlong address) {
    double value = 0.0;
    read_memory(pid, address, &value, sizeof(value));
    return value;
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_writeInt(JNIEnv *, jclass, jint pid, jlong address, jint value) {
    return write_memory(pid, address, &value, sizeof(value));
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_writeLong(JNIEnv *, jclass, jint pid, jlong address, jlong value) {
    return write_memory(pid, address, &value, sizeof(value));
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_writeFloat(JNIEnv *, jclass, jint pid, jlong address, jfloat value) {
    return write_memory(pid, address, &value, sizeof(value));
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_writeDouble(JNIEnv *, jclass, jint pid, jlong address, jdouble value) {
    return write_memory(pid, address, &value, sizeof(value));
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_writeBytes(JNIEnv *env, jclass, jint pid, jlong address, jbyteArray data) {
    jsize len = env->GetArrayLength(data);
    jbyte *bytes = env->GetByteArrayElements(data, nullptr);
    bool ok = write_memory(pid, address, bytes, len);
    env->ReleaseByteArrayElements(data, bytes, JNI_ABORT);
    return ok;
}

JNIEXPORT jlong JNICALL
Java_com_eni_modmenu_native_NativeLib_aobScan(JNIEnv *env, jclass, jint pid, jlong start, jlong end,
                                               jbyteArray patternBytes, jstring maskStr) {
    jsize patLen = env->GetArrayLength(patternBytes);
    jbyte *pat = env->GetByteArrayElements(patternBytes, nullptr);
    const char *mask = env->GetStringUTFChars(maskStr, nullptr);

    long result = aob_scan(pid, start, end, (const uint8_t*)pat, mask, patLen);

    env->ReleaseByteArrayElements(patternBytes, pat, JNI_ABORT);
    env->ReleaseStringUTFChars(maskStr, mask);
    return result;
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_makeWritable(JNIEnv *, jclass, jint pid, jlong address, jlong size) {
    return make_writable(pid, address, size);
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_ptraceWrite(JNIEnv *, jclass, jint pid, jlong address, jlong value, jint size) {
    return ptrace_write(pid, address, value, size);
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_ptraceAttach(JNIEnv *, jclass, jint pid) {
    return ptrace_attach(pid);
}

JNIEXPORT jboolean JNICALL
Java_com_eni_modmenu_native_NativeLib_ptraceDetach(JNIEnv *, jclass, jint pid) {
    return ptrace_detach(pid);
}

} // extern "C"
