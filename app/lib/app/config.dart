import 'package:flutter/foundation.dart';

const _prodUrl = 'https://api.kurl.online';

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

// Base URLs in priority order. Release builds and live web hosts use prod
// only; debug builds try local first, then fall back to prod.
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
