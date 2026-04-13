import 'package:flutter/foundation.dart';

String _resolveBaseUrl() {
  if (kIsWeb) return 'http://localhost:8000';
  if (defaultTargetPlatform == TargetPlatform.android) {
    return 'http://10.0.2.2:8000';
  }
  return 'http://localhost:8000';
}

final apiBaseUrl = _resolveBaseUrl();
