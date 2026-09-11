package com.beatnova.app

import android.content.Context

/**
 * Ad abstraction for BeatNova. The app UI talks only to this layer so the
 * advertising provider can be changed later without redesigning the app.
 */
object AdManager {
    private const val PREFS = "beatnova_monetization"
    private const val KEY_ADS_ENABLED = "ads_enabled"

    private var initialized = false
    private var adsEnabled = true

    fun initialize(context: Context) {
        if (initialized) return
        val prefs = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        adsEnabled = prefs.getBoolean(KEY_ADS_ENABLED, true)
        initialized = true
    }

    fun isPremium(context: Context): Boolean = PremiumGate.isPremium(context)

    fun shouldShowAds(context: Context): Boolean = adsEnabled && !isPremium(context)

    fun setAdsEnabled(context: Context, enabled: Boolean) {
        adsEnabled = enabled
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_ADS_ENABLED, enabled).apply()
    }

    /** Provider-neutral entry points. A Tapsell/Yektanet/etc. adapter can be plugged in later. */
    fun showBanner() = Unit
    fun showNative() = Unit
    fun showRewarded(onReward: () -> Unit) {
        // Until a real rewarded SDK is connected, never grant a reward implicitly.
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
