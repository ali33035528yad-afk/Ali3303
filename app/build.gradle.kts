plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.beatnova.app"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.beatnova.app"
        minSdk = 24
        targetSdk = 35
        versionCode = 10
        versionName = "1.6.0"

        val fallbackSupabaseUrl = "https://fwowpkiivliyzaebzpvw.supabase.co"
        val fallbackSupabasePublishableKey = "sb_publishable_rEQEUxwxVSjVOsEzB9A7wA_IGH9V5X6"
        val supabaseUrl = System.getenv("SUPABASE_URL")?.takeIf { it.isNotBlank() } ?: fallbackSupabaseUrl
        val supabasePublishableKey = System.getenv("SUPABASE_ANON_KEY")?.takeIf { it.isNotBlank() } ?: fallbackSupabasePublishableKey
        val adiveryAppId = System.getenv("ADIVERY_APP_ID")?.takeIf { it.isNotBlank() } ?: "6b50ebd8-e979-4738-b986-a8e90172a8c2"
        val adiveryBannerPlacementId = System.getenv("ADIVERY_BANNER_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: "129de33c-9f73-45f8-a411-b0262faff3f9"
        val adiveryInterstitialPlacementId = System.getenv("ADIVERY_INTERSTITIAL_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: "fe68f200-abe4-4773-9ed2-a48e59883a76"
        val adiveryAppOpenPlacementId = System.getenv("ADIVERY_APP_OPEN_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: "3fb1f6a3-6aab-404b-9813-01a2c94682bc"

        buildConfigField("String", "SUPABASE_URL", "\"$supabaseUrl\"")
        buildConfigField("String", "SUPABASE_ANON_KEY", "\"$supabasePublishableKey\"")
        buildConfigField("String", "ADIVERY_APP_ID", "\"$adiveryAppId\"")
        buildConfigField("String", "ADIVERY_BANNER_PLACEMENT_ID", "\"$adiveryBannerPlacementId\"")
        buildConfigField("String", "ADIVERY_INTERSTITIAL_PLACEMENT_ID", "\"$adiveryInterstitialPlacementId\"")
        buildConfigField("String", "ADIVERY_APP_OPEN_PLACEMENT_ID", "\"$adiveryAppOpenPlacementId\"")
    }
    signingConfigs {
        create("release") {
            val keystorePath = System.getenv("CM_KEYSTORE_PATH")
            if (!keystorePath.isNullOrBlank()) {
                storeFile = file(keystorePath)
                storePassword = System.getenv("CM_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("CM_KEY_ALIAS")
                keyPassword = System.getenv("CM_KEY_PASSWORD")
            } else initWith(signingConfigs.getByName("debug"))
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true; buildConfig = true }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    androidTestImplementation(composeBom)
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.10.0")
    implementation("androidx.fragment:fragment-ktx:1.8.9")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3:1.3.1")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.media3:media3-exoplayer:1.5.1")
    implementation("androidx.media3:media3-ui:1.5.1")
    implementation("androidx.media3:media3-datasource:1.5.1")
    implementation("androidx.media3:media3-database:1.5.1")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("com.adivery:sdk:4.9.0")
    implementation("com.google.android.gms:play-services-ads-identifier:18.0.1")
}
