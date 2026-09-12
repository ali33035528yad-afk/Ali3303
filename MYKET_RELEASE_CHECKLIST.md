# BeatNova — Myket Release Checklist

## Current app build
- Application ID: `com.beatnova.app`
- Version: `1.6.0` (`versionCode 10`)
- Target SDK: 35
- Release outputs: APK + AAB
- Ads: Adivery banner, interstitial and app-open placements are configured.

## Required before submitting to Myket
1. **Production release signing**
   - Configure a real release keystore in CI using `CM_KEYSTORE_PATH`, `CM_KEYSTORE_PASSWORD`, `CM_KEY_ALIAS`, and `CM_KEY_PASSWORD`.
   - Do not publish an APK signed with the temporary/debug fallback.
2. **Privacy policy**
   - Publish a public privacy-policy URL describing account/authentication, Supabase data processing, Adivery advertising, identifiers/analytics if applicable, and user rights.
   - Put the same URL in the Myket listing.
3. **Music/content rights**
   - Confirm that every distributed track, cover, image, and other copyrighted asset is licensed for distribution.
4. **Store listing**
   - App name: BeatNova
   - Category: Music/Audio (choose the closest available Myket category)
   - Add icon, screenshots, description, support contact, privacy-policy URL, and release notes.
5. **Final QA**
   - Test login/register/recovery, playback, downloads, notifications, ads, premium behavior, and deep-link recovery on Android 8–15+ devices.

## CI note
The GitHub Actions workflow builds on every push to `main` and also supports manual dispatch. The workflow consumes optional production secrets for Supabase and Adivery. Release signing remains dependent on the real keystore secrets being configured.
