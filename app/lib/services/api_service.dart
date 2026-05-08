import 'dart:convert';
import 'dart:developer' as developer;
import 'package:http/http.dart' as http;
import 'package:kurl/app/config.dart';
import 'package:kurl/models/kurl_result.dart';

class ApiService {
  static Future<KurlResult> kurl(String url, String targetPlatform) async {
    final endpoint = '$apiBaseUrl/api/kurl';
    developer.log('POST $endpoint [$targetPlatform] $url', name: 'kurl.api');

    final response = await http.post(
      Uri.parse(endpoint),
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey,
      },
      body: jsonEncode({
        'url': url,
        'target_platform': targetPlatform,
      }),
    );

    developer.log(
      '<- ${response.statusCode} ${response.body}',
      name: 'kurl.api',
    );

    final json = jsonDecode(response.body);

    if (response.statusCode != 200 || json['status'] == 'error') {
      throw ApiException(
        code: json['code'] as String? ?? 'INTERNAL_ERROR',
        message: json['message'] as String? ?? json['detail'] as String? ?? 'Request failed',
        status: response.statusCode,
      );
    }

    final data = json['data'] as Map<String, dynamic>?;
    if (data == null) {
      throw ApiException(
        code: 'INVALID_RESPONSE',
        message: 'Invalid response from server',
        status: response.statusCode,
      );
    }

    return KurlResult.fromJson(data);
  }
}

class ApiException implements Exception {
  final String code;
  final String message;
  final int status;

  ApiException({
    required this.code,
    required this.message,
    required this.status,
  });

  @override
  String toString() => message;
}
