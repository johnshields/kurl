import 'dart:convert';
import 'dart:developer' as developer;
import 'package:http/http.dart' as http;
import 'package:kurl/app/config.dart';

// Fire-and-forget analytics events to the first-party backend.
class Analytics {
  static Future<void> _send(String type, Map<String, dynamic> payload) async {
    try {
      await http.post(
        Uri.parse('$apiBaseUrl/api/events'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'type': type, ...payload}),
      );
    } catch (e) {
      developer.log('Analytics error: $e', name: 'kurl.analytics');
    }
  }

  static void trackPageView() {
    _send('page_view', {});
  }

  static void trackKurl(String sourceUrl, String platform) {
    _send('kurl', {'sourceUrl': sourceUrl, 'platform': platform});
  }

  static void trackKurlSuccess(String sourceUrl, String platform, String via) {
    _send('kurl_success', {'sourceUrl': sourceUrl, 'platform': platform});
  }

  static void trackPlatformSelect(String platform) {
    _send('platform_select', {'platform': platform});
  }

  static void trackOpenResult(String platform) {
    _send('open_result', {'platform': platform});
  }
}
