// Cross-platform AdSense banner.
// Web variant injects an <ins class="adsbygoogle"> element via HtmlElementView.
// Native variant renders nothing -- AdSense is web-only; mobile would use
// the google_mobile_ads plugin instead.
export 'ad_banner_io.dart' if (dart.library.js_interop) 'ad_banner_web.dart';
