import 'package:flutter/foundation.dart';

const _prodUrl = 'https://api.kurl.online';
const apiKey = String.fromEnvironment('KURL_API_KEY');

// AdSense -- pass via --dart-define on build.
// Empty string disables ads (dev / non-prod).
const adsenseClient = String.fromEnvironment('ADSENSE_CLIENT');
const adsenseSlotInline = String.fromEnvironment('ADSENSE_SLOT_INLINE');
const adsenseSlotFooter = String.fromEnvironment('ADSENSE_SLOT_FOOTER');

String _resolveBaseUrl() {
  if (kReleaseMode) return _prodUrl;
  if (kIsWeb) return 'http://localhost:8000';
  if (defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
}

final apiBaseUrl = _resolveBaseUrl();
