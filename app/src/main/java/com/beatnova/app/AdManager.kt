package com.beatnova.app

import android.app.Activity
import android.app.Application
import android.content.Context
import android.os.Bundle
import com.adivery.sdk.Adivery

/** Centralized ad handling for BeatNova. */
object AdManager {
    private const val PREFS = "beatnova_monetization"
    private const val KEY_ADS_ENABLED = "ads_enabled"
    private var initialized = false
    private var adsEnabled = true
    private var pendingAfterInterstitial: (() -> Unit)? = null

    private val interstitialListener = object : com.adivery.sdk.AdiveryListener() {
        override fun onInterstitialAdLoaded(placementId: String) = Unit
        override fun onInterstitialAdShown(placementId: String) = Unit
        override fun onInterstitialAdClicked(placementId: String) = Unit
        override fun onInterstitialAdClosed(placementId: String) {
            val action = pendingAfterInterstitial
            pendingAfterInterstitial = null
            action?.invoke()
        }
        override fun log(placementId: String, message: String) = Unit
    }

    fun initialize(context: Context) {
        if (initialized) return
        val appContext = context.applicationContext
        adsEnabled = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getBoolean(KEY_ADS_ENABLED, true)
        Adivery.setLoggingEnabled(BuildConfig.DEBUG)
        val application = appContext as Application
        Adivery.configure(application, BuildConfig.ADIVERY_APP_ID)
        val placement = BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID
        if (placement.isNotBlank()) {
            Adivery.addPlacementListener(placement, interstitialListener)
            Adivery.prepareInterstitialAd(appContext, placement)
        }
        if (BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID.isNotBlank()) {
            application.registerActivityLifecycleCallbacks(AppOpenAdLifecycle())
        }
        initialized = true
    }

    fun isPremium(context: Context): Boolean = PremiumGate.isPremium(context)
    fun shouldShowAds(context: Context): Boolean = adsEnabled && !isPremium(context)

    fun setAdsEnabled(context: Context, enabled: Boolean) {
        adsEnabled = enabled
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_ADS_ENABLED, enabled).apply()
    }

    fun playAfterInterstitial(context: Context, afterAd: () -> Unit) {
        if (!shouldShowAds(context)) { afterAd(); return }
        val activity = context as? Activity
        val placement = BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID
        if (activity == null || placement.isBlank() || !Adivery.isLoaded(placement)) {
            afterAd()
            return
        }
        pendingAfterInterstitial = afterAd
        Adivery.showAd(placement)
    }

    fun showBanner() = Unit
    fun showNative() = Unit
    fun showRewarded(onReward: () -> Unit) = Unit
}

private class AppOpenAdLifecycle : Application.ActivityLifecycleCallbacks {
    private var startedActivities = 0
    private var backgroundedAt = 0L
    private var showing = false

    private val listener = object : com.adivery.sdk.AdiveryListener() {
        override fun onAppOpenAdShown(placementId: String) { showing = true }
        override fun onAppOpenAdClosed(placementId: String) { showing = false }
        override fun onAppOpenAdClicked(placementId: String) = Unit
        override fun onAppOpenAdLoaded(placementId: String) = Unit
        override fun log(placementId: String, message: String) = Unit
    }

    override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {
        val placement = BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID
        if (placement.isNotBlank()) {
            Adivery.addPlacementListener(placement, listener)
            Adivery.prepareAppOpenAd(activity, placement)
        }
    }
    override fun onActivityStarted(activity: Activity) {
        startedActivities++
        if (startedActivities == 1 && backgroundedAt > 0L) {
            val placement = BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID
            if (!showing && System.currentTimeMillis() - backgroundedAt >= 5_000L && placement.isNotBlank() && AdManager.shouldShowAds(activity) && Adivery.isLoaded(placement)) {
                Adivery.showAppOpenAd(activity, placement)
            }
        }
    }
    override fun onActivityStopped(activity: Activity) {
        startedActivities = (startedActivities - 1).coerceAtLeast(0)
        if (startedActivities == 0 && !showing) backgroundedAt = System.currentTimeMillis()
    }
    override fun onActivityResumed(activity: Activity) = Unit
    override fun onActivityPaused(activity: Activity) = Unit
    override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) = Unit
    override fun onActivityDestroyed(activity: Activity) = Unit
}

object PremiumGate {
    private const val PREFS = "beatnova_premium"
    private const val KEY_PREMIUM = "premium"
    fun isPremium(context: Context): Boolean = context.applicationContext
        .getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(KEY_PREMIUM, false)
    fun setPremium(context: Context, premium: Boolean) {
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_PREMIUM, premium).apply()
    }
}
