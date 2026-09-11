package com.beatnova.app

import android.content.Context
import com.adivery.sdk.Adivery

/**
 * Ad abstraction for BeatNova. The UI talks only to this layer so the
 * advertising provider can be changed later without redesigning the app.
 */
object AdManager {
    private const val PREFS = "beatnova_monetization"
    private const val KEY_ADS_ENABLED = "ads_enabled"

    private var initialized = false
    private var adsEnabled = true

    fun initialize(context: Context) {
        if (initialized) return
        val appContext = context.applicationContext
        val prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        adsEnabled = prefs.getBoolean(KEY_ADS_ENABLED, true)

        Adivery.setLoggingEnabled(BuildConfig.DEBUG)
        Adivery.configure(appContext, BuildConfig.ADIVERY_APP_ID)

        initialized = true
    }

    fun isPremium(context: Context): Boolean = PremiumGate.isPremium(context)

    fun shouldShowAds(context: Context): Boolean = adsEnabled && !isPremium(context)

    fun setAdsEnabled(context: Context, enabled: Boolean) {
        adsEnabled = enabled
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_ADS_ENABLED, enabled).apply()
    }

    // Placement-specific UI is enabled after the corresponding Adivery placement IDs
    // are configured. The app key alone initializes the SDK safely.
    fun showBanner() = Unit
    fun showNative() = Unit
    fun showRewarded(onReward: () -> Unit) {
        // Never grant a reward until a real rewarded placement reports completion.
    }
}

object PremiumGate {
    private const val PREFS = "beatnova_premium"
    private const val KEY_PREMIUM = "premium"

    fun isPremium(context: Context): Boolean = context.applicationContext
        .getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        .getBoolean(KEY_PREMIUM, false)

    fun setPremium(context: Context, premium: Boolean) {
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_PREMIUM, premium).apply()
    }
}
