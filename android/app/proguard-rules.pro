# Add project specific ProGuard rules here.
-keepattributes *Annotation*
-dontwarn okhttp3.**
-dontwarn okio.**
-dontwarn javax.annotation.**
-keep class com.pawfect.app.data.model.** { *; }

