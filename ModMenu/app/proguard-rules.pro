# Add project specific ProGuard rules here.
-keep class com.eni.modmenu.native.NativeLib { *; }
-keep class com.eni.modmenu.features.** { *; }
-keepclassmembers class * {
    native <methods>;
}
