import 'package:flutter/foundation.dart';

const _prodUrl = 'https://api.kurl.online';
const apiKey = String.fromEnvironment('KURL_API_KEY');

// AdSense slot IDs are public (visible in rendered HTML), so safe to
// commit. Override via --dart-define for staging / different sites.
const adsenseClient = String.fromEnvironment(
  'ADSENSE_CLIENT',
  defaultValue: 'ca-pub-3145356206216831',
);
const adsenseSlotInline = String.fromEnvironment(
  'ADSENSE_SLOT_INLINE',
  defaultValue: '9162167583',
);
const adsenseSlotFooter = String.fromEnvironment(
  'ADSENSE_SLOT_FOOTER',
  defaultValue: '2004136400',
);

String _resolveBaseUrl() {
  if (kReleaseMode) return _prodUrl;
  if (kIsWeb) return 'http://localhost:8000';
  if (defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
}

final apiBaseUrl = _resolveBaseUrl();
