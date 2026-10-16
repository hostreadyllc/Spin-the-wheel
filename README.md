# Spin the Wheel

A decision-maker wheel for Android. Package name: `com.ash.spinthewheel`.

## Features

- Wheel for 3 to 8 players; the player count can change at any time.
- Rename any slice with names, numbers, emoji or any symbol the keyboard supports. Names are saved on the phone.
- Optional **Eliminator mode**: knock out each pick until one person is left.
- 3 free themes (Candy Pop, Lagoon, Chalk) and 4 premium themes (Neon Arcade, Royal Gold, Desert Sunset, Galaxy).
- Tick sound on every slice, a win fanfare, and confetti.
- Vibration on each tick and on the win, through a native bridge.
- Shake the phone to spin, or press SPIN, or tap the wheel.
- The wheel scales to fill any screen, from small phones to tablets.
- **Works fully offline.** Fonts and all assets are bundled, and the app does not request internet permission.

## Project layout

| Path | What it is |
|---|---|
| `web/index.html` | The whole app: UI, wheel, themes, sounds, shake detection |
| `web/fonts/` | Bundled Baloo 2 and Nunito Sans fonts (SIL Open Font License) |
| `android/AndroidManifest.xml` | Manifest: VIBRATE permission only, portrait, min SDK 24, target SDK 36 |
| `android/res/` | App name, theme colours, launcher icons |
| `android/tools/build_dex.py` | Generates `classes.dex`: a full-screen WebView activity plus the vibration bridge (Java equivalent in the file header) |
| `android/tools/zipalign.py` | Aligns the APK before signing |
| `android/tools/Sign.java` | Signs the APK (v2 + v3) with apksig |
| `android/tools/make_icons.py` | Redraws the launcher icons and the 512px store icon |
| `android/store/` | Play Store listing icon |
| `android/build.sh` | One command that builds the signed APK and AAB into `dist/` |

## Building

Requirements: Java 17 or newer, Python 3, and three Android tools:

- `aapt2` (Android build-tools)
- `android.jar` for API 36
- `bundletool-all.jar`

```bash
export AAPT2=/path/to/aapt2
export ANDROID_JAR=/path/to/android-36.jar
export BUNDLETOOL=/path/to/bundletool-all.jar
export KEYSTORE=/path/to/spinthewheel-upload.jks
export STORE_PASS='your-keystore-password'
VERSION_CODE=2 VERSION_NAME=1.1 ./android/build.sh
```

Increase `VERSION_CODE` for every Play Store upload.

## How it works

The native layer is deliberately tiny. `MainActivity` opens a full-screen WebView that loads `file:///android_asset/index.html?app=1`. The page detects `app=1` and does three things: it calls the native vibrator through `prompt("vib", ms)`, which `Bridge.onJsPrompt` intercepts; it turns on shake detection automatically through `devicemotion`; and it hides the browser-only "Enable shake" button.

## Before publishing to Google Play

- **Premium is a demo unlock.** Real payments need Google Play Billing, which requires a Gradle-based build. The premium themes and the paywall UI are ready; only the purchase call is missing.
- **Signing key:** the upload keystore is not in this repository on purpose. Keep it and its password safe. Every future update must be signed with the same key.
- **Play Console:** opt in to Play App Signing, which is the default for new apps, and upload the `.aab`.
