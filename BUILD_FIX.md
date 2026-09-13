# BeatNova APK build fix

`NavigationBarItem` was removed from the bottom navigation implementation and replaced with a self-contained Compose `RowScope` item to avoid the previous unresolved-reference compilation error.

Codemagic builds the release APK with Gradle 8.9 using `clean assembleRelease`.

GitHub Actions now explicitly signs the release APK, verifies it with `apksigner`, and publishes the installable APK as a build artifact and prerelease asset.
