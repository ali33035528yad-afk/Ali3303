from pathlib import Path

root = Path(__file__).resolve().parents[1]

gradle = root / "app/build.gradle.kts"
s = gradle.read_text()
if "ADIVERY_INTERSTITIAL_PLACEMENT_ID" not in s:
    old = '        val adiveryBannerPlacementId = System.getenv("ADIVERY_BANNER_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: "129de33c-9f73-45f8-a411-b0262faff3f9"\n'
    new = old + '        val adiveryInterstitialPlacementId = System.getenv("ADIVERY_INTERSTITIAL_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: "fe68f200-abe4-4773-9ed2-a48e59883a76"\n        val adiveryAppOpenPlacementId = System.getenv("ADIVERY_APP_OPEN_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: "3fb1f6a3-6aab-404b-9813-01a2c94682bc"\n'
    s = s.replace(old, new)
    old2 = '        buildConfigField("String", "ADIVERY_BANNER_PLACEMENT_ID", "\\"$adiveryBannerPlacementId\\"")\n'
    new2 = old2 + '        buildConfigField("String", "ADIVERY_INTERSTITIAL_PLACEMENT_ID", "\\"$adiveryInterstitialPlacementId\\"")\n        buildConfigField("String", "ADIVERY_APP_OPEN_PLACEMENT_ID", "\\"$adiveryAppOpenPlacementId\\"")\n'
    s = s.replace(old2, new2)
    gradle.write_text(s)

ad = root / "app/src/main/java/com/beatnova/app/AdManager.kt"
s = ad.read_text()
if "playAfterInterstitial" not in s:
    start = s.index("object AdManager {")
    end = s.index("\nobject PremiumGate", start)
    replacement = '''object AdManager {
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
        val prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        adsEnabled = prefs.getBoolean(KEY_ADS_ENABLED, true)
        Adivery.setLoggingEnabled(BuildConfig.DEBUG)
        val application = appContext as Application
        Adivery.configure(application, BuildConfig.ADIVERY_APP_ID)

        val interstitial = BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID
        if (interstitial.isNotBlank()) {
            Adivery.addPlacementListener(interstitial, interstitialListener)
            Adivery.prepareInterstitialAd(appContext, interstitial)
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

    /** Runs [afterAd] only after the interstitial closes. If no ad is ready, playback starts normally. */
    fun playAfterInterstitial(context: Context, afterAd: () -> Unit) {
        if (!shouldShowAds(context)) {
            afterAd()
            return
        }
        val activity = context as? android.app.Activity
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
    fun showRewarded(onReward: () -> Unit) { }
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

    override fun onActivityCreated(activity: android.app.Activity, savedInstanceState: Bundle?) {
        val placement = BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID
        if (placement.isNotBlank()) {
            Adivery.addPlacementListener(placement, listener)
            Adivery.prepareAppOpenAd(activity, placement)
        }
    }

    override fun onActivityStarted(activity: android.app.Activity) {
        startedActivities++
        if (startedActivities == 1 && backgroundedAt > 0L) {
            val placement = BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID
            if (!showing && System.currentTimeMillis() - backgroundedAt >= 5_000L && placement.isNotBlank() && AdManager.shouldShowAds(activity) && Adivery.isLoaded(placement)) {
                showing = true
                Adivery.showAppOpenAd(activity, placement)
            }
        }
    }

    override fun onActivityStopped(activity: android.app.Activity) {
        startedActivities = (startedActivities - 1).coerceAtLeast(0)
        if (startedActivities == 0 && !showing) backgroundedAt = System.currentTimeMillis()
    }
    override fun onActivityResumed(activity: android.app.Activity) = Unit
    override fun onActivityPaused(activity: android.app.Activity) = Unit
    override fun onActivitySaveInstanceState(activity: android.app.Activity, outState: Bundle) = Unit
    override fun onActivityDestroyed(activity: android.app.Activity) = Unit
}
'''
    s = s[:start] + replacement + s[end:]
    if 'import android.os.Bundle' not in s:
        s = s.replace('import android.content.Context\n', 'import android.content.Context\nimport android.os.Bundle\n')
    ad.write_text(s)

main = root / "app/src/main/java/com/beatnova/app/MainActivity.kt"
s = main.read_text()
old = '    fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showFullPlayer = true; showPlaybackNotification(context, song, true); AdManager.maybeShowInterstitial(context) }'
new = '    fun play(song: Song) { AdManager.playAfterInterstitial(context) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showFullPlayer = true; showPlaybackNotification(context, song, true) } }'
if old in s:
    s = s.replace(old, new)
else:
    old2 = '    fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showFullPlayer = true; showPlaybackNotification(context, song, true) }'
    if old2 in s:
        s = s.replace(old2, new)
main.write_text(s)

print("Interstitial now blocks playback until the ad closes; playback remains immediate when no ad is ready.")
