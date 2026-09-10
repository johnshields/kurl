import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:kurl/models/friend.dart';
import 'package:kurl/models/message.dart';
import 'package:kurl/models/thread.dart';
import 'package:kurl/services/api_base.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/auth_service.dart';

/// Friends graph and direct messages. Session-gated -- every call needs a
/// stored token, otherwise it throws AUTH_REQUIRED.
class SocialService {
  static Future<FriendsOverview> friends() async {
    final data = await _get('/api/friends');
    return data == null ? FriendsOverview.empty : FriendsOverview.fromJson(data);
  }

  static Future<void> sendFriendRequest(String username) =>
      _send('POST', '/api/friends', body: {'username': username});

  static Future<void> acceptFriendRequest(String friendUid) =>
      _send('POST', '/api/friends/$friendUid/accept');

  static Future<void> removeFriend(String friendUid) =>
      _send('DELETE', '/api/friends/$friendUid');

  static Future<List<MessageThread>> threads() async {
    final data = await _get('/api/messages');
    if (data == null) return [];
    return (data as List).map((e) => MessageThread.fromJson(e)).toList();
  }

  static Future<ThreadDetail> thread(String threadUid) async {
    final data = await _get('/api/messages/$threadUid');
    return ThreadDetail.fromJson(data as Map<String, dynamic>);
  }

  static Future<Message> sendMessage({
    String? toUsername,
    String? toUid,
    String? threadUid,
    String? body,
    Map<String, dynamic>? kurl,
  }) async {
    final json = await _send('POST', '/api/messages', body: {
      'toUsername': ?toUsername,
      'toUid': ?toUid,
      'threadUid': ?threadUid,
      'body': ?body,
      'kurl': ?kurl,
    });
    return Message.fromJson(json!['data']);
  }

  static Future<void> markThreadRead(String threadUid) =>
      _send('POST', '/api/messages/$threadUid/read');

  static Future<void> deleteMessage(String messageUid) =>
      _send('DELETE', '/api/messages/$messageUid');

  static Future<String> _token() async {
    final token = await AuthService.getToken();
    if (token == null) {
      throw ApiException(code: 'AUTH_REQUIRED', message: 'Login required.', status: 401);
    }
    return token;
  }

  static Future<dynamic> _get(String path) async {
    final token = await _token();
    final base = await resolveApiBase();
    final response = await http.get(
      Uri.parse('$base$path'),
      headers: {'Authorization': 'Bearer $token'},
    );
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    _throwIfError(json, response.statusCode);
    return json['data'];
  }

  static Future<Map<String, dynamic>?> _send(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final token = await _token();
    final base = await resolveApiBase();
    final uri = Uri.parse('$base$path');
    final headers = {
      'Authorization': 'Bearer $token',
      if (body != null) 'Content-Type': 'application/json',
    };
    final encoded = body == null ? null : jsonEncode(body);
    final response = switch (method) {
      'POST' => await http.post(uri, headers: headers, body: encoded),
      'DELETE' => await http.delete(uri, headers: headers, body: encoded),
      _ => throw ArgumentError('unsupported method: $method'),
    };
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    _throwIfError(json, response.statusCode);
    return json;
  }

  static void _throwIfError(Map<String, dynamic> json, int statusCode) {
    if (json['status'] != 'error') return;
    throw ApiException(
      code: json['code'] as String? ?? 'INTERNAL_ERROR',
      message: json['message'] as String? ?? 'Request failed',
      status: statusCode,
    );
  }
}
