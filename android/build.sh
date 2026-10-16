#!/usr/bin/env bash
# Builds a signed APK and a signed AAB for com.ash.spinthewheel
# without Android Studio or Gradle.
#
# Needs: Java 17+, Python 3, and these tools (set the paths below or as env vars):
#   AAPT2       aapt2 binary (Android build-tools)
#   ANDROID_JAR platform android.jar (API 36)
#   BUNDLETOOL  bundletool-all-*.jar (also provides the apksig signer)
# Signing:
#   KEYSTORE, KEY_ALIAS, STORE_PASS   (the upload key; never commit it)
#
# Usage: VERSION_CODE=1 VERSION_NAME=1.0 ./android/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
: "${AAPT2:?set AAPT2}" "${ANDROID_JAR:?set ANDROID_JAR}" "${BUNDLETOOL:?set BUNDLETOOL}"
: "${KEYSTORE:?set KEYSTORE}" "${KEY_ALIAS:=upload}" "${STORE_PASS:?set STORE_PASS}"
VERSION_CODE="${VERSION_CODE:-1}"
VERSION_NAME="${VERSION_NAME:-1.0}"
MIN_SDK=24
TARGET_SDK=36
OUT=dist
B=build
rm -rf "$B" && mkdir -p "$B" "$OUT"

echo "1/6 native code -> classes.dex"
python3 android/tools/build_dex.py "$B/classes.dex"

echo "2/6 compile resources"
"$AAPT2" compile --dir android/res -o "$B/res.zip"

LINK=(link -I "$ANDROID_JAR" --manifest android/AndroidManifest.xml -A web
      --min-sdk-version $MIN_SDK --target-sdk-version $TARGET_SDK
      --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" --auto-add-overlay)

echo "3/6 link APK"
"$AAPT2" "${LINK[@]}" -o "$B/unsigned.apk" "$B/res.zip"
(cd "$B" && zip -q -X unsigned.apk classes.dex)
python3 android/tools/zipalign.py "$B/unsigned.apk" "$B/aligned.apk"

echo "4/6 align + sign APK"
javac -nowarn -cp "$BUNDLETOOL" -d "$B" android/tools/Sign.java
java -cp "$BUNDLETOOL:$B" Sign "$KEYSTORE" "$KEY_ALIAS" "$STORE_PASS" "$B/aligned.apk" "$OUT/SpinTheWheel-$VERSION_NAME.apk"

echo "5/6 link AAB module"
"$AAPT2" "${LINK[@]}" --proto-format -o "$B/proto.apk" "$B/res.zip"
mkdir -p "$B/base/manifest" "$B/base/dex"
(cd "$B/base" && unzip -q ../proto.apk)
mv "$B/base/AndroidManifest.xml" "$B/base/manifest/AndroidManifest.xml"
cp "$B/classes.dex" "$B/base/dex/classes.dex"
(cd "$B/base" && zip -q -r -X ../base.zip manifest dex res assets resources.pb)
java -jar "$BUNDLETOOL" build-bundle --modules="$B/base.zip" --output="$B/unsigned.aab" --overwrite

echo "6/6 sign AAB"
cp "$B/unsigned.aab" "$OUT/SpinTheWheel-$VERSION_NAME.aab"
jarsigner -keystore "$KEYSTORE" -storepass "$STORE_PASS" -sigalg SHA256withRSA -digestalg SHA-256 \
  "$OUT/SpinTheWheel-$VERSION_NAME.aab" "$KEY_ALIAS" >/dev/null

echo "done:"
ls -la "$OUT"
