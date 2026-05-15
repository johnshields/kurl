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

// Default debug API = pywrangler dev (port 8787)
const _apiUrlOverride = String.fromEnvironment('KURL_API_URL');
const _localPort = 8787;

String _resolveBaseUrl() {
  if (_apiUrlOverride.isNotEmpty) return _apiUrlOverride;
  if (kReleaseMode) return _prodUrl;
  if (kIsWeb) return 'http://localhost:$_localPort';
  if (defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:$_localPort';
  }
  return 'http://localhost:$_localPort';
}

final apiBaseUrl = _resolveBaseUrl();
