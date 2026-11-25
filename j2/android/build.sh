#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
SDK="${ANDROID_SDK_ROOT:-$HOME/.local/share/mcz-android-sdk}"
if [ ! -d "$SDK/platforms" ]; then SDK=/usr/lib/android-sdk; fi
BT="${ANDROID_BUILD_TOOLS:-$(find "$SDK/build-tools" -mindepth 1 -maxdepth 1 -type d -name '[0-9]*' | sort -V | tail -1)}"
JAR="${ANDROID_PLATFORM_JAR:-$(find "$SDK/platforms" -mindepth 2 -maxdepth 2 -name android.jar | sort -V | tail -1)}"
test -f "$JAR"
OUT="$PWD/build"; mkdir -p "$OUT/classes" "$OUT/dex" ../dist
javac -source 8 -target 8 -encoding UTF-8 -classpath "$JAR" -d "$OUT/classes" MainActivity.java
"$BT/d8" --min-api 22 --lib "$JAR" --output "$OUT/dex" $(find "$OUT/classes" -name '*.class')
"$BT/aapt" package -f -M AndroidManifest.xml -I "$JAR" -F "$OUT/unsigned.apk"
(cd "$OUT/dex"; "$BT/aapt" add "$OUT/unsigned.apk" classes.dex)
"$BT/zipalign" -f 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
# Local Android development signing only. The generated key is not tracked.
KEY="${QMINI_DEV_KEY:-$HOME/.local/share/qmini-j2/dev.keystore}"
mkdir -p "$(dirname "$KEY")"; umask 077
if [ ! -e "$KEY" ]; then
    keytool -genkeypair -keystore "$KEY" -storepass android -keypass android -alias qmini-dev -keyalg RSA -keysize 2048 -validity 10000 -dname 'CN=Qmini J2 development'
fi
"$BT/apksigner" sign --ks "$KEY" --ks-key-alias qmini-dev --ks-pass pass:android --key-pass pass:android --out ../dist/qmini-j2-dev.apk "$OUT/aligned.apk"
"$BT/apksigner" verify --verbose ../dist/qmini-j2-dev.apk
"$BT/aapt" dump badging ../dist/qmini-j2-dev.apk | sed -n '1,12p'
