# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified
# in C:\Users\Shahr\AppData\Local\Android\Sdk/tools/proguard/proguard-android.txt
# You can edit the include path and order by changing the proguardFiles
# directive in build.gradle.

# For Glide
-keep public class * extends com.bumptech.glide.module.AppGlideModule
-keep public class * extends com.bumptech.glide.module.LibraryGlideModule
-keep class com.bumptech.glide.GeneratedAppGlideModuleImpl { *; }

# For Firebase
-keep class com.google.firebase.** { *; }

# For Media3/ExoPlayer
-keep class androidx.media3.** { *; }

# Keep models for JSON serialization if needed
-keep class com.shahriyarsojibhasan.shahriyarlivetv.model.** { *; }
