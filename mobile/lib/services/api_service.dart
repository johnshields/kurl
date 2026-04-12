import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:kurl/app/config.dart';
import 'package:kurl/models/resolve_result.dart';

class ApiService {
  static Future<ResolveResult> resolve(String url, String targetPlatform) async {
    final response = await http.post(
      Uri.parse('$apiBaseUrl/api/resolve'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'url': url,
        'target_platform': targetPlatform,
      }),
    );

    final json = jsonDecode(response.body);

    if (response.statusCode != 200 || json['status'] == 'error') {
      throw Exception(json['message'] ?? json['detail'] ?? 'Request failed');
    }

    return ResolveResult.fromJson(json['data']);
  }
}
