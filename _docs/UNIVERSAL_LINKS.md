# Universal Links & App Links

Tap a `https://kurlshare.com/?u=<encoded-url>` link and kurl opens directly with the URL pre-filled — no share sheet needed.

## URL format

```
https://kurlshare.com/?u=<percent-encoded-music-url>
```

Example:
```
https://kurlshare.com/?u=https%3A%2F%2Fopen.spotify.com%2Ftrack%2F6QJVQSuMC77psM4vgPo31D
```

Any music URL can be wrapped this way for sharing. When tapped:
- **On a device with kurl installed** → opens the app, populates the input, ready to tap a platform
- **Without the app** → opens kurlshare.com in the browser (future: web version handles it)

## Backend — already served

- `GET /.well-known/apple-app-site-association` → [backend/public/.well-known/apple-app-site-association](../backend/public/.well-known/apple-app-site-association)
- `GET /.well-known/assetlinks.json` → [backend/public/.well-known/assetlinks.json](../backend/public/.well-known/assetlinks.json)

Both are served as `application/json` (Apple's file has no extension but must have the correct MIME type).

**Before going live at kurlshare.com, replace placeholders:**

- `apple-app-site-association` → `TEAMID` with your 10-char Apple Team ID (find it in Apple Developer → Membership)
- `assetlinks.json` → `REPLACE_WITH_SHA256_CERT_FINGERPRINT` with your Android app signing key's SHA-256 fingerprint. Get it with:

```bash
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
```

For production you'll want to use the release keystore, not the debug one.

## Android — already wired

Manifest intent filter in [app/android/app/src/main/AndroidManifest.xml](../app/android/app/src/main/AndroidManifest.xml):

```xml
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW"/>
    <category android:name="android.intent.category.DEFAULT"/>
    <category android:name="android.intent.category.BROWSABLE"/>
    <data android:scheme="https" android:host="kurlshare.com"/>
    <data android:scheme="https" android:host="www.kurlshare.com"/>
</intent-filter>
```

`autoVerify="true"` means Android will automatically hit `https://kurlshare.com/.well-known/assetlinks.json` on first install to verify the app owns the domain. Once verified, kurl becomes the default handler for those URLs.

## iOS — manual (but light)

Unlike the Share Extension, Universal Links only need a capability toggle on the existing Runner target. No new target.

### Steps

1. Open `app/ios/Runner.xcworkspace` in Xcode.
2. Select the **Runner** target.
3. **Signing & Capabilities → + Capability → Associated Domains**.
4. Add one entry:

```
applinks:kurlshare.com
```

5. Make sure the Runner target has a valid Team selected under Signing.
6. Rebuild:

```bash
cd app
flutter clean
flutter run -d <ios-device>
```

iOS will then fetch `https://kurlshare.com/.well-known/apple-app-site-association` on first launch and honour links to that domain.

### Troubleshooting

- If Universal Links don't work on iOS, check the AASA file is served correctly:
  ```bash
  curl -v https://kurlshare.com/.well-known/apple-app-site-association
  ```
  Must return `200 OK` with `Content-Type: application/json` and valid JSON.
- Apple caches AASA aggressively — delete the app and reinstall to re-verify.

## Flutter — handles all three platforms

[app/lib/app/routes/kurl.dart](../app/lib/app/routes/kurl.dart) pulls the URL from three sources:

- `_appLinks.getInitialLink()` — iOS/Android: app launched from a link
- `_appLinks.uriLinkStream` — iOS/Android: link tapped while app is in background
- `Uri.base` at init — web: the current browser URL (for Flutter web builds served at kurlshare.com)

All three paths extract `?u=<encoded-url>` and populate the input. If no `u` param is present, the URI is ignored.

## Flutter web hosting

Build the Flutter web app and deploy it to `kurlshare.com` so the browser fallback works:

```bash
cd app
flutter build web --release --base-href /
```

Serve the `build/web/` directory behind kurlshare.com. Tapping `https://kurlshare.com/?u=...` from a desktop browser then loads the web app, which immediately picks up `?u=` and pre-fills the input.

## Testing

Once deployed and verified:

```bash
# Android — adb
adb shell am start -a android.intent.action.VIEW \
  -d "https://kurlshare.com/?u=https%3A%2F%2Fopen.spotify.com%2Ftrack%2F6QJVQSuMC77psM4vgPo31D"

# iOS — xcrun
xcrun simctl openurl booted "https://kurlshare.com/?u=https%3A%2F%2Fopen.spotify.com%2Ftrack%2F6QJVQSuMC77psM4vgPo31D"
```

Tapping the link in Safari / Messages on a real device is the best real-world test.
