import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:kurl/models/kurl_history_item.dart';
import 'package:kurl/models/user.dart';
import 'package:kurl/services/api_base.dart';
import 'package:kurl/services/api_exception.dart';

const _tokenKey = 'kurl_session_token';

class AuthService {
  static String? _cachedToken;

  static Future<String?> getToken() async {
    if (_cachedToken != null) return _cachedToken;
    final prefs = await SharedPreferences.getInstance();
    _cachedToken = prefs.getString(_tokenKey);
    return _cachedToken;
  }

  static Future<bool> isLoggedIn() async => (await getToken()) != null;

  static Future<void> logout() async {
    _cachedToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }

  static Future<KurlUser> signup(String email, String password) async {
    final data = await _post('/api/auth/signup', {'email': email, 'password': password});
    await _saveToken(data['token']);
    return KurlUser.fromJson(data['user']);
  }

  static Future<KurlUser> login(String email, String password) async {
    final data = await _post('/api/auth/login', {'email': email, 'password': password});
    await _saveToken(data['token']);
    return KurlUser.fromJson(data['user']);
  }

  /// Null when logged out, or when the stored token is no longer valid --
  /// callers should treat both the same way (show the login form).
  static Future<KurlUser?> getProfile() async {
    final data = await _authedGet('/api/auth/profile');
    return data == null ? null : KurlUser.fromJson(data);
  }

  static Future<KurlUser> updateProfile({String? username, String? preferredPlatform}) async {
    final token = await getToken();
    if (token == null) {
      throw ApiException(code: 'AUTH_REQUIRED', message: 'Login required.', status: 401);
    }
    final base = await resolveApiBase();
    final response = await http.patch(
      Uri.parse('$base/api/auth/profile'),
      headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
      body: jsonEncode({
        'username': ?username,
        'preferredPlatform': ?preferredPlatform,
      }),
    );
    final json = jsonDecode(response.body);
    if (json['status'] == 'error') {
      throw ApiException(
        code: json['code'] as String? ?? 'INTERNAL_ERROR',
        message: json['message'] as String? ?? 'Request failed',
        status: response.statusCode,
      );
    }
    return KurlUser.fromJson(json['data']);
  }

  static Future<List<KurlHistoryItem>> getKurls() async {
    final data = await _authedGet('/api/kurls');
    if (data == null) return [];
    return (data as List).map((e) => KurlHistoryItem.fromJson(e)).toList();
  }

  static Future<void> deleteKurl(String uid) async {
    final token = await getToken();
    if (token == null) {
      throw ApiException(code: 'AUTH_REQUIRED', message: 'Login required.', status: 401);
    }
    final base = await resolveApiBase();
    final response = await http.delete(
      Uri.parse('$base/api/kurls/$uid'),
      headers: {'Authorization': 'Bearer $token'},
    );
    final json = jsonDecode(response.body);
    if (json['status'] == 'error') {
      throw ApiException(
        code: json['code'] as String? ?? 'INTERNAL_ERROR',
        message: json['message'] as String? ?? 'Request failed',
        status: response.statusCode,
      );
    }
  }

  static Future<void> _saveToken(String token) async {
    _cachedToken = token;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  static Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final base = await resolveApiBase();
    final response = await http.post(
      Uri.parse('$base$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    final json = jsonDecode(response.body);
    if (json['status'] == 'error') {
      throw ApiException(
        code: json['code'] as String? ?? 'INTERNAL_ERROR',
        message: json['message'] as String? ?? 'Request failed',
        status: response.statusCode,
      );
    }
    return json['data'];
  }

  /// Null on logged-out, no session, or an invalid/expired token -- clears
  /// a dead token so the next call doesn't keep retrying it.
  static Future<dynamic> _authedGet(String path) async {
    final token = await getToken();
    if (token == null) return null;

    final base = await resolveApiBase();
    final response = await http.get(
      Uri.parse('$base$path'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 401) {
      await logout();
      return null;
    }

    final json = jsonDecode(response.body);
    if (json['status'] == 'error') return null;
    return json['data'];
  }
}
