from pathlib import Path

root = Path(__file__).resolve().parents[1]

# --- build.gradle.kts: add configurable placement IDs ---
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

# --- AdManager.kt: replace with safe fullscreen controller ---
ad = root / "app/src/main/java/com/beatnova/app/AdManager.kt"
s = ad.read_text()
if "FullscreenAdController" not in s:
    start = s.index("object AdManager {")
    end = s.index("\nobject PremiumGate", start)
    replacement = '''object AdManager {\n    private const val PREFS = "beatnova_monetization"\n    private const val KEY_ADS_ENABLED = "ads_enabled"\n    private const val KEY_INTERSTITIAL_COUNT = "interstitial_count"\n    private const val KEY_LAST_INTERSTITIAL = "last_interstitial"\n\n    private var initialized = false\n    private var adsEnabled = true\n\n    fun initialize(context: Context) {\n        if (initialized) return\n        val appContext = context.applicationContext\n        val prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)\n        adsEnabled = prefs.getBoolean(KEY_ADS_ENABLED, true)\n\n        Adivery.setLoggingEnabled(BuildConfig.DEBUG)\n        Adivery.configure(appContext as Application, BuildConfig.ADIVERY_APP_ID)\n\n        if (BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID.isNotBlank()) {\n            Adivery.prepareInterstitialAd(appContext, BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID)\n        }\n        if (BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID.isNotBlank()) {\n            Adivery.prepareAppOpenAd(appContext, BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID)\n            appContext.registerActivityLifecycleCallbacks(AppOpenAdLifecycle(appContext))\n        }\n        initialized = true\n    }\n\n    fun isPremium(context: Context): Boolean = PremiumGate.isPremium(context)\n\n    fun shouldShowAds(context: Context): Boolean = adsEnabled && !isPremium(context)\n\n    fun setAdsEnabled(context: Context, enabled: Boolean) {\n        adsEnabled = enabled\n        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)\n            .edit().putBoolean(KEY_ADS_ENABLED, enabled).apply()\n    }\n\n    /** Shows an interstitial only after several meaningful song starts, with a cooldown. */\n    fun maybeShowInterstitial(context: Context) {\n        if (!shouldShowAds(context)) return\n        val placement = BuildConfig.ADIVERY_INTERSTITIAL_PLACEMENT_ID\n        if (placement.isBlank()) return\n        val activity = context as? android.app.Activity ?: return\n        val prefs = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)\n        val count = prefs.getInt(KEY_INTERSTITIAL_COUNT, 0) + 1\n        val last = prefs.getLong(KEY_LAST_INTERSTITIAL, 0L)\n        val now = System.currentTimeMillis()\n        val eligible = count >= 4 && now - last >= 120_000L\n        if (!eligible) {\n            prefs.edit().putInt(KEY_INTERSTITIAL_COUNT, count).apply()\n            return\n        }\n        if (Adivery.isLoaded(placement)) {\n            prefs.edit().putInt(KEY_INTERSTITIAL_COUNT, 0).putLong(KEY_LAST_INTERSTITIAL, now).apply()\n            Adivery.showAd(placement)\n        }\n    }\n\n    fun showBanner() = Unit\n    fun showNative() = Unit\n    fun showRewarded(onReward: () -> Unit) { }\n}\n\nprivate class AppOpenAdLifecycle(private val appContext: Context) : Application.ActivityLifecycleCallbacks {\n    private var lastPausedAt = 0L\n\n    override fun onActivityResumed(activity: android.app.Activity) {\n        if (lastPausedAt == 0L) return\n        if (!AdManager.shouldShowAds(activity)) return\n        val placement = BuildConfig.ADIVERY_APP_OPEN_PLACEMENT_ID\n        if (placement.isBlank()) return\n        if (System.currentTimeMillis() - lastPausedAt >= 5_000L && Adivery.isLoaded(placement)) {\n            Adivery.showAppOpenAd(activity, placement)\n        }\n    }\n\n    override fun onActivityPaused(activity: android.app.Activity) { lastPausedAt = System.currentTimeMillis() }\n    override fun onActivityCreated(activity: android.app.Activity, savedInstanceState: Bundle?) = Unit\n    override fun onActivityStarted(activity: android.app.Activity) = Unit\n    override fun onActivityStopped(activity: android.app.Activity) = Unit\n    override fun onActivitySaveInstanceState(activity: android.app.Activity, outState: Bundle) = Unit\n    override fun onActivityDestroyed(activity: android.app.Activity) = Unit\n}\n'''
    s = s[:start] + replacement + s[end:]
    s = s.replace('import android.content.Context\n', 'import android.content.Context\nimport android.os.Bundle\n')
    ad.write_text(s)

# --- MainActivity.kt: trigger interstitial on meaningful song starts ---
main = root / "app/src/main/java/com/beatnova/app/MainActivity.kt"
s = main.read_text()
needle = '    fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showFullPlayer = true; showPlaybackNotification(context, song, true) }'
replacement = '    fun play(song: Song) { current = song; player.setMediaItem(MediaItem.fromUri(song.audioUrl)); player.prepare(); player.play(); showFullPlayer = true; showPlaybackNotification(context, song, true); AdManager.maybeShowInterstitial(context) }'
if needle in s and 'AdManager.maybeShowInterstitial(context)' not in s:
    s = s.replace(needle, replacement)
main.write_text(s)

print("Fullscreen Adivery ads patch applied.")
