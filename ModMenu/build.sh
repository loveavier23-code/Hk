#!/bin/bash
set -e

echo "=== ModMenu APK Builder ==="
echo ""

# Generate debug keystore if not present
KEYSTORE="app/debug.keystore"
if [ ! -f "$KEYSTORE" ]; then
    echo "[*] Generating debug keystore..."
    keytool -genkey -v \
        -keystore "$KEYSTORE" \
        -alias androiddebugkey \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -storepass android \
        -keypass android \
        -dname "CN=Android Debug,O=Android,C=US" \
        -noprompt 2>/dev/null || {
        echo "[!] keytool not found. Install Java JDK first."
        echo "    On Ubuntu: apt install openjdk-17-jdk-headless"
        echo "    On Mac: brew install openjdk"
        echo ""
        echo "    Or generate manually:"
        echo "    keytool -genkey -v -keystore app/debug.keystore -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 -storepass android -keypass android -dname 'CN=Android Debug,O=Android,C=US'"
        exit 1
    }
    echo "[+] Keystore generated"
fi

# Clean
echo "[*] Cleaning..."
rm -rf app/build app/.cxx

# Build
echo "[*] Building APK..."
./gradlew assembleRelease 2>&1 || {
    echo ""
    echo "[!] Build failed. Make sure you have:"
    echo "    1. Android SDK (API 36) installed"
    echo "    2. NDK 27+ installed"
    echo "    3. CMake 3.22+ installed"
    echo "    4. Java 17+ installed"
    echo ""
    echo "    Set ANDROID_HOME and ANDROID_NDK_HOME if needed."
    exit 1
}

echo ""
echo "[+] Build successful!"
echo "    APK: app/build/outputs/apk/release/app-release.apk"
echo ""
echo "    Sign with your own key for distribution:"
echo "    apksigner sign --ks your-key.keystore app/build/outputs/apk/release/app-release.apk"
