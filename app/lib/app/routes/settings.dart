import 'package:flutter/material.dart';
import 'package:kurl/app/routes/settings/auth_form.dart';
import 'package:kurl/app/routes/settings/profile_view.dart';
import 'package:kurl/app/routes/settings/reset_password_form.dart';
import 'package:kurl/models/user.dart';
import 'package:kurl/services/auth_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  KurlUser? _user;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    // Sign in with Spotify hands back the token via the redirect URL, not storage.
    final redirectToken = Uri.base.queryParameters['token'];
    if (redirectToken != null) await AuthService.adoptSessionToken(redirectToken);

    final verifyToken = Uri.base.queryParameters['verify'];
    if (verifyToken != null) {
      try {
        await AuthService.verifyEmail(verifyToken);
      } catch (_) {
      }
    }

    final user = await AuthService.getProfile();
    if (mounted) {
      setState(() {
        _user = user;
        _loading = false;
      });
    }
  }

  Future<void> _logout() async {
    await AuthService.logout();
    if (mounted) setState(() => _user = null);
  }

  @override
  Widget build(BuildContext context) {
    final resetToken = Uri.base.queryParameters['reset'];

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: _loading
            ? const Center(
                child: CircularProgressIndicator(color: Color(0xFF555555), strokeWidth: 2),
              )
            : resetToken != null
                ? ResetPasswordForm(
                    token: resetToken,
                    onDone: (user) => setState(() => _user = user),
                  )
                : _user == null
                    ? AuthForm(onAuthenticated: (user) => setState(() => _user = user))
                    : ProfileView(
                        user: _user!,
                        onUpdated: (user) => setState(() => _user = user),
                        onLogout: _logout,
                      ),
      ),
    );
  }
}
