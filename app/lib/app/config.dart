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

// Default debug API = pywrangler dev (port 8787).
const _apiUrlOverride = String.fromEnvironment('KURL_API_URL');
const _localPort = 8787;

String _localUrl() {
  if (kIsWeb) return 'http://localhost:$_localPort';
  if (defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:$_localPort';
  }
  return 'http://localhost:$_localPort';
}

// Candidate base URLs in priority order. Release builds use prod only.
// Debug builds try local first, fall back to prod when worker is offline,
// so the app keeps working without `pywrangler dev` running. A web build
// served from kurl.online (or any non-local host) is treated as live
// regardless of build mode -- never probes localhost.
List<String> _candidates() {
  if (_apiUrlOverride.isNotEmpty) return [_apiUrlOverride];
  if (kReleaseMode || _isLiveWebHost()) return [_prodUrl];
  return [_localUrl(), _prodUrl];
}

bool _isLiveWebHost() {
  if (!kIsWeb) return false;
  final host = Uri.base.host.toLowerCase();
  return host.isNotEmpty && host != 'localhost' && host != '127.0.0.1';
}

final List<String> apiCandidateUrls = _candidates();
