from pathlib import Path

root = Path(__file__).resolve().parents[1]

gradle = root / "app/build.gradle.kts"
s = gradle.read_text()
if "ADIVERY_INTERSTITIAL_PLACEMENT_ID" not in s:
    old = '        val adiveryBannerPlacementId = System.getenv("ADIVERY_BANNER_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: "129de33c-9f73-45f8-a411-b0262faff3f9"\n'
    new = old + '        val adiveryInterstitialPlacementId = System.getenv("ADIVERY_INTERSTITIAL_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: ""\n        val adiveryAppOpenPlacementId = System.getenv("ADIVERY_APP_OPEN_PLACEMENT_ID")?.takeIf { it.isNotBlank() } ?: ""\n'
    s = s.replace(old, new)
    old2 = '        buildConfigField("String", "ADIVERY_BANNER_PLACEMENT_ID", "\\"$adiveryBannerPlacementId\\"")\n'
    new2 = old2 + '        buildConfigField("String", "ADIVERY_INTERSTITIAL_PLACEMENT_ID", "\\"$adiveryInterstitialPlacementId\\"")\n        buildConfigField("String", "ADIVERY_APP_OPEN_PLACEMENT_ID", "\\"$adiveryAppOpenPlacementId\\"")\n'
    s = s.replace(old2, new2)
    gradle.write_text(s)

ad = root / "app/src/main/java/com/beatnova/app/AdManager.kt"
s = ad.read_text()
if "AppOpenAdLifecycle" not in s:
    start = s.index("object AdManager {")
    end = s.index("\nobject PremiumGate", start)
    replacement = '''object AdManager {
    private const val PREFS = "beatnova_monetization"
    private const val KEY_ADS_ENABLED = "ads_enabled"
    private const val KEY_INTERSTITIAL_COUNT = "interstitial_count"
    private const val KEY_LAST_INTERSTITIAL = "last_interstitial"

    private var initialized = false
    private var adsEnabled = true

    fun initialize(context: Context) {
        if (initialized) return
        val appContext = context.applicationContext
        val prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        adsEnabled = prefs.getBoolean(KEY_ADS_ENABLED, true)
        Adivery.setLoggingEnabled(BuildConfig.DEBUG)
        val application = appContext as Application
        Adivery.configure(application, BuildConfig.ADIVERY_APP_ID)
        if (BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID.isNotBlank()) {
            Adivery.prepareInterstitialAd(appContext, BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID)
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

    fun maybeShowInterstitial(context: Context) {
        if (!shouldShowAds(context)) return
        val placement = BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID
        if (placement.isBlank() || context !is android.app.Activity) return
        val prefs = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val count = prefs.getInt(KEY_INTERSTITIAL_COUNT, 0) + 1
        val last = prefs.getLong(KEY_LAST_INTERSTITIAL, 0L)
        val now = System.currentTimeMillis()
        if (count < 4 || now - last < 120_000L) {
            prefs.edit().putInt(KEY_INTERSTITIAL_COUNT, count).apply()
            return
        }
        if (Adivery.isLoaded(placement)) {
            prefs.edit().putInt(KEY_INTERSTITIAL_COUNT, 0).putLong(KEY_LAST_INTERSTITIAL, now).apply()
            Adivery.showAd(placement)
        }
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
    override fun onActivityDestroyed(activity: android.app.Activity) {
        val placement = BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID
        if (placement.isNotBlank()) Adivery.removePlacementListener(placement)
    }
}
'''
    s = s[:start] + replacement + s[end:]
    if 'import android.os.Bundle' not in s:
        s = s.replace('import android.content.Context\n', 'import android.content.Context\nimport android.os.Bundle\n')
    ad.write_text(s)

main = root / "app/src/main/java/com/beatnova/app/MainActivity.kt"
s = main.read_text()
needle = '    fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showFullPlayer = true; showPlaybackNotification(context, song, true) }'
replacement = '    fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showFullPlayer = true; showPlaybackNotification(context, song, true); AdManager.maybeShowInterstitial(context) }'
if needle in s and 'AdManager.maybeShowInterstitial(context)' not in s:
    s = s.replace(needle, replacement)
main.write_text(s)

print("Fullscreen Adivery ads patch applied safely.")
