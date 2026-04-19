# Share Extension Setup

`receive_sharing_intent` handles the Flutter side. Android is fully wired via `AndroidManifest.xml`. iOS needs a Share Extension target in Xcode — a one-time manual setup.

## Android (done)

Two `<intent-filter>` blocks inside `<activity>` in `app/android/app/src/main/AndroidManifest.xml`:

```xml
<intent-filter>
    <action android:name="android.intent.action.SEND"/>
    <category android:name="android.intent.category.DEFAULT"/>
    <data android:mimeType="text/plain"/>
</intent-filter>
<intent-filter>
    <action android:name="android.intent.action.SEND"/>
    <category android:name="android.intent.category.DEFAULT"/>
    <data android:mimeType="text/*"/>
</intent-filter>
```

kurl now appears in the Android share sheet for any text/URL payload.

## iOS (manual)

### 1. Add Share Extension target

Open `app/ios/Runner.xcworkspace` in Xcode, then:

- **File → New → Target → Share Extension**
- Product Name: `ShareExtension`
- Language: Swift
- Team: your Apple Developer team
- Bundle ID: `com.kurl.kurl.ShareExtension`
- Click **Finish**. When prompted to activate the scheme, say **Activate**.

### 2. Enable App Groups

Both the `Runner` target and the new `ShareExtension` target need the same App Group.

On each target: **Signing & Capabilities → + Capability → App Groups**. Add:

```
group.com.kurl.kurl.sharedData
```

### 3. Replace ShareViewController.swift

Xcode generated `ios/ShareExtension/ShareViewController.swift`. Replace its contents with:

```swift
import receive_sharing_intent

class ShareViewController: RSIShareViewController {
    override func shouldAutoRedirect() -> Bool {
        return true
    }
}
```

### 4. Update the extension's Info.plist

Open `ios/ShareExtension/Info.plist` and set `NSExtensionAttributes`:

```xml
<key>NSExtensionAttributes</key>
<dict>
    <key>NSExtensionActivationRule</key>
    <dict>
        <key>NSExtensionActivationSupportsText</key>
        <true/>
        <key>NSExtensionActivationSupportsWebURLWithMaxCount</key>
        <integer>1</integer>
    </dict>
</dict>
```

### 5. Update the Runner's Info.plist

Open `ios/Runner/Info.plist` and add near the bottom:

```xml
<key>NSPhotoLibraryUsageDescription</key>
<string>kurl needs access to the share sheet to receive links.</string>
```

### 6. Set the App Group in Swift code

In `ios/ShareExtension/ShareViewController.swift`, if you need custom handling later, access shared data via `UserDefaults(suiteName: "group.com.kurl.kurl.sharedData")`.

### 7. Rebuild

```bash
cd app
flutter clean
flutter pub get
flutter run -d <ios-device>
```

Now share a link from Safari, Spotify, etc. — kurl appears in the iOS share sheet.

## Testing

- **Android emulator:** open Spotify, Apple Music, or any browser, tap share on a track, pick kurl.
- **iOS simulator:** same flow. The simulator's share sheet is limited but works for text URLs.
- **Debug:** Flutter DevTools console will show `kurl.api` logs when the shared URL triggers the resolve call.
