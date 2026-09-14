import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:kurl/services/api_exception.dart';

void throwIfError(Map<String, dynamic> json, int statusCode) {
  if (json['status'] != 'error') return;
  throw ApiException(
    code: json['code'] as String? ?? 'INTERNAL_ERROR',
    message: json['message'] as String? ?? 'Request failed',
    status: statusCode,
  );
}

/// Sends a Bearer-authenticated request and returns the decoded JSON body.
/// Throws ApiException on an error response.
Future<Map<String, dynamic>> authedSend(
  String method,
  Uri uri,
  String token, {
  Map<String, dynamic>? body,
}) async {
  final headers = {
    'Authorization': 'Bearer $token',
    if (body != null) 'Content-Type': 'application/json',
  };
  final encoded = body == null ? null : jsonEncode(body);
  final response = switch (method) {
    'GET' => await http.get(uri, headers: headers),
    'POST' => await http.post(uri, headers: headers, body: encoded),
    'DELETE' => await http.delete(uri, headers: headers, body: encoded),
    _ => throw ArgumentError('unsupported method: $method'),
  };
  final json = jsonDecode(response.body) as Map<String, dynamic>;
  throwIfError(json, response.statusCode);
  return json;
}
