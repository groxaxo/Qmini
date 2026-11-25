# Qmini J2 — experimental head adaptation

Based on Unitree Qmini, upstream commit f6f3fef. The fork retains the upstream CC BY-NC-SA 4.0 license. This is a personal/research prototype, not a certified robot or a complete replacement for the Qmini controller.

## Handset

Samsung Galaxy J2 SM-J200Y: nominal bare body 136.5 × 69 × 8.4 mm, 130 g, 4.7-inch 540 × 960 display, 1 GB RAM, Android 5.1 at launch. Source: [One NZ product datasheet](https://one.nz/MEDIA_ProductCatalog/m900057_Samsung_SM-J200Y_Product_Datasheet_1_14.pdf).

## Printable head carrier

- `cad/build.py`: parametric Blender 4.x source. Run `blender -b --python-exit-code 1 --python j2/cad/build.py` from repository root.
- `cad/generated/Qmini_J2_head.blend`: assembled carrier, four removable retainers, and nominal handset reference (do not print the reference).
- `cad/generated/*.stl`: five printable components in millimetres, laid flat at z=0.
- `cad/generated/validation.json`: measured bounding boxes, manifold/connected-component checks, and phone-envelope intersection checks.

Carrier is 160 × 72 × 3.2 mm; four corner retainers bolt through the outer rails. Allow nominal 0.65 mm clearance each side and over the phone face; add thin soft pads if necessary, without pressing screen, camera or buttons. Print one retainer first and check the phone with calipers. PETG recommended, 0.2 mm layers, at least four perimeters, 35–50% infill as initial prototype settings; inspect overhangs/supports in the slicer. Use M3 through bolts with washers and locking nuts; select lengths after measuring the printed stack. Do not overtighten. The four centre holes are on a 30 × 30 mm square, with phone-side shallow counterbores; verify heads are flush or recessed before inserting the phone. Bare handset only; cases or battery swelling invalidate the dimensions.

**Mechanical limitation:** the carrier-side pattern is intentionally an independent interface, not a claimed match for the M8010 output or Qmini neck. Verify motor-side mounting geometry, approved fastener holes and engagement against the actual robot and official V2 STEP assembly. The upstream URDF has no explicit neck/head link. Do not substitute assembly fasteners or operate with an unsecured phone. Check static strength, dynamic load, range of motion, balance, cable strain relief and clearance before powered tests. Upstream policy and inertial parameters have not been updated.

## Android head

`dist/qmini-j2-dev.apk` is a locally signed development build, min SDK 22 (Android 5.1), target SDK 28, no native ABI dependency. Features: landscape animated eyes, local Android TTS greeting (engine/voice required), manually activated front-camera preview (permission required), and explicit read-only simulation gateway check. Camera frames remain local. The microphone and remote perception pipeline are not implemented.

Build: `j2/android/build.sh`. Requires Android SDK platform jar, build tools with d8/aapt/apksigner/zipalign, and JDK. Override ANDROID_SDK_ROOT, ANDROID_BUILD_TOOLS, ANDROID_PLATFORM_JAR if necessary. The private development key stays on the build machine. Do not distribute it. Install on an authorized, connected handset:

```sh
adb install -r j2/dist/qmini-j2-dev.apk
adb shell am start -n com.qmini.j2/.MainActivity
```

The APK compiled and passed signature verification. No live J2 was available for installation or runtime camera, TTS, network, or UI tests.

## Host gateway (simulation only)

```sh
export QMINI_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python3 j2/gateway/server.py
```

The default bind is loopback. To test the handset on an isolated trusted LAN, deliberately bind to the host's LAN address with `--host ADDRESS`; prefer an authenticated HTTPS reverse proxy when available. Plain HTTP does not encrypt the token. Enter the base URL and token in the Android Connect dialog; it performs one authenticated status check. No motor commands are accepted. Tests: `python3 -m unittest discover -s j2/tests -v`.

## Planned integration

J2 is the user-facing head, not the safety-critical gait controller. Retain the Linux controller and body IMU, and the upstream [RoboTamerSdk4Qmini](https://github.com/vsislab/RoboTamerSdk4Qmini) deployment stack for locomotion. Connect only after a separate motor-control safety review, hardware emergency stop and validated watchdog/fail-safe behavior. Heavy vision, speech recognition and language-model inference can run on a separate host, but are not wired into this version. Any new mass distribution requires updated simulation parameters and retraining or revalidation before walking. Test without motor power first.

All upstream files except the added README link are untouched.
