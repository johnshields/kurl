import 'dart:developer' as developer;

import 'package:http/http.dart' as http;
import 'package:kurl/app/config.dart';

// First reachable candidate, cached for the session.
String? _activeBase;

Future<String> resolveApiBase() async {
  if (_activeBase != null) return _activeBase!;
  if (apiCandidateUrls.length == 1) {
    _activeBase = apiCandidateUrls.first;
    return _activeBase!;
  }

  for (final base in apiCandidateUrls) {
    try {
      final resp = await http
          .get(Uri.parse('$base/api/healthz'))
          .timeout(const Duration(milliseconds: 600));
      if (resp.statusCode == 200) {
        _activeBase = base;
        developer.log('Using API base: $base', name: 'kurl.api');
        return base;
      }
    } catch (_) {
      // Try next candidate.
    }
  }

  // Nothing reachable -- fall back to last candidate so real errors surface.
  _activeBase = apiCandidateUrls.last;
  return _activeBase!;
}
