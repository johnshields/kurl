import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:kurl/models/deezer_account.dart';
import 'package:kurl/models/kurl_history_item.dart';
import 'package:kurl/models/soundcloud_account.dart';
import 'package:kurl/models/spotify_account.dart';
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

  static Future<KurlUser> updateProfile({
    String? email,
    String? username,
    String? preferredPlatform,
    bool clearPreferredPlatform = false,
    String? password,
  }) async {
    final token = await getToken();
    if (token == null) {
      throw ApiException(code: 'AUTH_REQUIRED', message: 'Login required.', status: 401);
    }
    final base = await resolveApiBase();
    final response = await http.patch(
      Uri.parse('$base/api/auth/profile'),
      headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
      body: jsonEncode({
        'email': ?email,
        'username': ?username,
        'password': ?password,
        if (clearPreferredPlatform) 'preferredPlatform': null else 'preferredPlatform': ?preferredPlatform,
      }),
    );
    final json = jsonDecode(response.body);
    _throwIfError(json, response.statusCode);
    return KurlUser.fromJson(json['data']);
  }

  static Future<void> forgotPassword(String email) async {
    await _post('/api/auth/forgot-password', {'email': email});
  }

  static Future<KurlUser> resetPassword(String token, String password) async {
    final data = await _post('/api/auth/reset-password', {'token': token, 'password': password});
    await _saveToken(data['token']);
    return KurlUser.fromJson(data['user']);
  }

  static Future<void> verifyEmail(String token) async {
    await _post('/api/auth/verify-email', {'token': token});
  }

  static Future<void> resendVerification() async {
    final token = await getToken();
    if (token == null) {
      throw ApiException(code: 'AUTH_REQUIRED', message: 'Login required.', status: 401);
    }
    final base = await resolveApiBase();
    final response = await http.post(
      Uri.parse('$base/api/auth/resend-verification'),
      headers: {'Authorization': 'Bearer $token'},
    );
    _throwIfError(jsonDecode(response.body), response.statusCode);
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
    _throwIfError(jsonDecode(response.body), response.statusCode);
  }

  static Future<SpotifyAccount> getSpotifyStatus() async {
    final data = await _authedGet('/api/auth/spotify');
    return data == null ? SpotifyAccount.disconnected : SpotifyAccount.fromJson(data);
  }

  /// Authorize URL to open, or null if unconfigured/failed. Works signed-in
  /// (link mode) or signed-out (full sign-in).
  static Future<String?> startSpotifyAuth() async {
    final results = await Future.wait([getToken(), resolveApiBase()]);
    final token = results[0];
    final base = results[1]!;
    final response = await http.get(
      Uri.parse('$base/api/auth/spotify/start'),
      headers: {if (token != null) 'Authorization': 'Bearer $token'},
    );
    final json = jsonDecode(response.body);
    if (json['status'] == 'error') return null;
    return json['data']?['url'];
  }

  /// Adopts a session token handed back on the Spotify sign-in redirect
  /// (?token=...) -- same storage path as signup/login.
  static Future<void> adoptSessionToken(String token) => _saveToken(token);

  static Future<void> disconnectSpotify() async {
    final token = await getToken();
    if (token == null) {
      throw ApiException(code: 'AUTH_REQUIRED', message: 'Login required.', status: 401);
    }
    final base = await resolveApiBase();
    final response = await http.delete(
      Uri.parse('$base/api/auth/spotify'),
      headers: {'Authorization': 'Bearer $token'},
    );
    _throwIfError(jsonDecode(response.body), response.statusCode);
  }

  static Future<DeezerAccount> getDeezerStatus() async {
    final data = await _authedGet('/api/auth/deezer');
    return data == null ? DeezerAccount.disconnected : DeezerAccount.fromJson(data);
  }

  /// Authorize URL to open, or null if unconfigured/failed. Works signed-in
  /// (link mode) or signed-out (full sign-in).
  static Future<String?> startDeezerAuth() async {
    final results = await Future.wait([getToken(), resolveApiBase()]);
    final token = results[0];
    final base = results[1]!;
    final response = await http.get(
      Uri.parse('$base/api/auth/deezer/start'),
      headers: {if (token != null) 'Authorization': 'Bearer $token'},
    );
    final json = jsonDecode(response.body);
    if (json['status'] == 'error') return null;
    return json['data']?['url'];
  }

  static Future<void> disconnectDeezer() async {
    final token = await getToken();
    if (token == null) {
      throw ApiException(code: 'AUTH_REQUIRED', message: 'Login required.', status: 401);
    }
    final base = await resolveApiBase();
    final response = await http.delete(
      Uri.parse('$base/api/auth/deezer'),
      headers: {'Authorization': 'Bearer $token'},
    );
    _throwIfError(jsonDecode(response.body), response.statusCode);
  }

  static Future<SoundcloudAccount> getSoundcloudStatus() async {
    final data = await _authedGet('/api/auth/soundcloud');
    return data == null ? SoundcloudAccount.disconnected : SoundcloudAccount.fromJson(data);
  }

  /// Authorize URL to open, or null if unconfigured/failed. Works signed-in
  /// (link mode) or signed-out (full sign-in).
  static Future<String?> startSoundcloudAuth() async {
    final results = await Future.wait([getToken(), resolveApiBase()]);
    final token = results[0];
    final base = results[1]!;
    final response = await http.get(
      Uri.parse('$base/api/auth/soundcloud/start'),
      headers: {if (token != null) 'Authorization': 'Bearer $token'},
    );
    final json = jsonDecode(response.body);
    if (json['status'] == 'error') return null;
    return json['data']?['url'];
  }

  static Future<void> disconnectSoundcloud() async {
    final token = await getToken();
    if (token == null) {
      throw ApiException(code: 'AUTH_REQUIRED', message: 'Login required.', status: 401);
    }
    final base = await resolveApiBase();
    final response = await http.delete(
      Uri.parse('$base/api/auth/soundcloud'),
      headers: {'Authorization': 'Bearer $token'},
    );
    _throwIfError(jsonDecode(response.body), response.statusCode);
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
    _throwIfError(json, response.statusCode);
    return json['data'] ?? {};
  }

  static void _throwIfError(Map<String, dynamic> json, int statusCode) {
    if (json['status'] != 'error') return;
    throw ApiException(
      code: json['code'] as String? ?? 'INTERNAL_ERROR',
      message: json['message'] as String? ?? 'Request failed',
      status: statusCode,
    );
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
