import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:kurl/models/google_account.dart';
import 'package:kurl/models/platform.dart';
import 'package:kurl/models/soundcloud_account.dart';
import 'package:kurl/models/spotify_account.dart';
import 'package:kurl/models/user.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/utils/auth_validator.dart';
import 'package:kurl/utils/friendly_error.dart';
import 'package:kurl/utils/url_state.dart';
import 'package:kurl/widgets/shared/platform_picker.dart';

const _errorRed = Color(0xFFEF4444);
const _borderIdle = Color(0xFF333333);
const _borderFocused = Color(0xFF555555);

/// Shared by both the sign-in screen and the profile view's Connect button --
/// starts the Spotify OAuth flow and navigates there. Returns the URL that
/// was opened, or null if Spotify sign-in isn't available right now.
Future<String?> _launchSpotifyAuth() async {
  final url = await AuthService.startSpotifyAuth();
  if (url != null) await launchUrl(Uri.parse(url), webOnlyWindowName: '_self');
  return url;
}

Future<String?> _launchSoundcloudAuth() async {
  final url = await AuthService.startSoundcloudAuth();
  if (url != null) await launchUrl(Uri.parse(url), webOnlyWindowName: '_self');
  return url;
}

Future<String?> _launchGoogleAuth() async {
  final url = await AuthService.startGoogleAuth();
  if (url != null) await launchUrl(Uri.parse(url), webOnlyWindowName: '_self');
  return url;
}

void _showToast(BuildContext context, String message) {
  final overlay = Overlay.of(context);
  late final OverlayEntry entry;
  entry = OverlayEntry(
    builder: (context) => Positioned(
      left: 24,
      right: 24,
      bottom: 96,
      child: Center(
        child: Material(
          color: const Color(0xFF222222),
          borderRadius: BorderRadius.circular(8),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              border: Border.all(color: _borderIdle),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(message, style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 13)),
          ),
        ),
      ),
    ),
  );
  overlay.insert(entry);
  Future.delayed(const Duration(seconds: 2), entry.remove);
}

class _ForgotPasswordDialog extends StatefulWidget {
  const _ForgotPasswordDialog();

  @override
  State<_ForgotPasswordDialog> createState() => _ForgotPasswordDialogState();
}

class _ForgotPasswordDialogState extends State<_ForgotPasswordDialog> {
  final _emailController = TextEditingController();
  bool _sending = false;
  bool _sent = false;
  String? _error;

  Future<void> _send() async {
    final error = validateEmail(_emailController.text);
    if (error != null) {
      setState(() => _error = error);
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      await AuthService.forgotPassword(_emailController.text.trim());
      if (mounted) setState(() => _sent = true);
    } catch (e) {
      if (mounted) setState(() => _error = e is ApiException ? e.message : friendlyError(e));
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: const Color(0xFF141414),
      title: const Text('Reset password', style: TextStyle(color: Color(0xFFE5E5E5))),
      content: _sent
          ? const Text(
              'If that email has an account, a reset link is on its way.',
              style: TextStyle(color: Color(0xFF888888)),
            )
          : Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: _emailController,
                  enabled: !_sending,
                  keyboardType: TextInputType.emailAddress,
                  style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                  decoration: InputDecoration(
                    hintText: 'Email',
                    hintStyle: const TextStyle(color: Color(0xFF555555), fontSize: 14),
                    filled: true,
                    fillColor: const Color(0xFF0A0A0A),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: _borderIdle),
                    ),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 8),
                  Text(_error!, style: const TextStyle(color: _errorRed, fontSize: 12)),
                ],
              ],
            ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text(_sent ? 'Close' : 'Cancel', style: const TextStyle(color: Color(0xFF888888))),
        ),
        if (!_sent)
          TextButton(
            onPressed: _sending ? null : _send,
            child: const Text('Send'),
          ),
      ],
    );
  }
}

class _ChangePasswordDialog extends StatefulWidget {
  final ValueChanged<KurlUser> onUpdated;

  const _ChangePasswordDialog({required this.onUpdated});

  @override
  State<_ChangePasswordDialog> createState() => _ChangePasswordDialogState();
}

class _ChangePasswordDialogState extends State<_ChangePasswordDialog> {
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _saving = false;
  String? _error;

  Future<void> _save() async {
    final password = _passwordController.text;
    final validationError =
        validatePassword(password) ?? validateConfirmPassword(password, _confirmPasswordController.text);
    if (validationError != null) {
      setState(() => _error = validationError);
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final updated = await AuthService.updateProfile(password: password);
      if (mounted) {
        widget.onUpdated(updated);
        Navigator.of(context).pop();
        _showToast(context, 'Password updated');
      }
    } catch (e) {
      if (mounted) setState(() => _error = e is ApiException ? e.message : friendlyError(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Widget _visibilityToggle(bool obscured, VoidCallback onPressed) {
    return IconButton(
      icon: Icon(obscured ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: const Color(0xFF888888), size: 18),
      onPressed: _saving ? null : onPressed,
    );
  }

  InputDecoration _decoration(String hint, {required Widget suffixIcon}) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: Color(0xFF555555), fontSize: 14),
      filled: true,
      fillColor: const Color(0xFF0A0A0A),
      suffixIcon: suffixIcon,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: _borderIdle)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: const Color(0xFF141414),
      title: const Text('Change password', style: TextStyle(color: Color(0xFFE5E5E5))),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _passwordController,
            enabled: !_saving,
            obscureText: _obscurePassword,
            style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
            decoration: _decoration(
              'New password',
              suffixIcon: _visibilityToggle(_obscurePassword, () => setState(() => _obscurePassword = !_obscurePassword)),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _confirmPasswordController,
            enabled: !_saving,
            obscureText: _obscureConfirmPassword,
            onSubmitted: (_) => _save(),
            style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
            decoration: _decoration(
              'Confirm new password',
              suffixIcon: _visibilityToggle(
                _obscureConfirmPassword,
                () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
              ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: _errorRed, fontSize: 12)),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
        ),
        TextButton(
          onPressed: _saving ? null : _save,
          child: Text(_saving ? 'Saving...' : 'Save'),
        ),
      ],
    );
  }
}

class _AddEmailDialog extends StatefulWidget {
  final ValueChanged<KurlUser> onUpdated;

  const _AddEmailDialog({required this.onUpdated});

  @override
  State<_AddEmailDialog> createState() => _AddEmailDialogState();
}

class _AddEmailDialogState extends State<_AddEmailDialog> {
  final _emailController = TextEditingController();
  bool _saving = false;
  String? _error;

  Future<void> _save() async {
    final email = _emailController.text.trim();
    final validationError = validateEmail(email);
    if (validationError != null) {
      setState(() => _error = validationError);
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final updated = await AuthService.updateProfile(email: email);
      if (mounted) {
        widget.onUpdated(updated);
        Navigator.of(context).pop();
        _showToast(context, 'Email added');
      }
    } catch (e) {
      if (mounted) setState(() => _error = e is ApiException ? e.message : friendlyError(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: const Color(0xFF141414),
      title: const Text('Add email', style: TextStyle(color: Color(0xFFE5E5E5))),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _emailController,
            enabled: !_saving,
            keyboardType: TextInputType.emailAddress,
            onSubmitted: (_) => _save(),
            style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
            decoration: InputDecoration(
              hintText: 'Email',
              hintStyle: const TextStyle(color: Color(0xFF555555), fontSize: 14),
              filled: true,
              fillColor: const Color(0xFF0A0A0A),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: _borderIdle)),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: _errorRed, fontSize: 12)),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
        ),
        TextButton(
          onPressed: _saving ? null : _save,
          child: Text(_saving ? 'Saving...' : 'Save'),
        ),
      ],
    );
  }
}

class _EditUsernameDialog extends StatefulWidget {
  final String currentUsername;
  final ValueChanged<KurlUser> onUpdated;

  const _EditUsernameDialog({required this.currentUsername, required this.onUpdated});

  @override
  State<_EditUsernameDialog> createState() => _EditUsernameDialogState();
}

class _EditUsernameDialogState extends State<_EditUsernameDialog> {
  late final _usernameController = TextEditingController(text: widget.currentUsername);
  bool _saving = false;
  String? _error;

  Future<void> _save() async {
    final username = _usernameController.text.trim();
    if (username.isEmpty || username == widget.currentUsername) {
      Navigator.of(context).pop();
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final updated = await AuthService.updateProfile(username: username);
      if (mounted) {
        widget.onUpdated(updated);
        Navigator.of(context).pop();
        _showToast(context, 'Username updated');
      }
    } catch (e) {
      if (mounted) setState(() => _error = e is ApiException ? e.message : friendlyError(e));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: const Color(0xFF141414),
      title: const Text('Edit username', style: TextStyle(color: Color(0xFFE5E5E5))),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _usernameController,
            enabled: !_saving,
            onSubmitted: (_) => _save(),
            style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
            decoration: InputDecoration(
              hintText: 'Username',
              hintStyle: const TextStyle(color: Color(0xFF555555), fontSize: 14),
              filled: true,
              fillColor: const Color(0xFF0A0A0A),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: _borderIdle)),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: _errorRed, fontSize: 12)),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
        ),
        TextButton(
          onPressed: _saving ? null : _save,
          child: Text(_saving ? 'Saving...' : 'Save'),
        ),
      ],
    );
  }
}

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
                ? _ResetPasswordForm(
                    token: resetToken,
                    onDone: (user) => setState(() => _user = user),
                  )
                : _user == null
                    ? _AuthForm(onAuthenticated: (user) => setState(() => _user = user))
                    : _ProfileView(
                        user: _user!,
                        onUpdated: (user) => setState(() => _user = user),
                        onLogout: _logout,
                      ),
      ),
    );
  }
}

class _ResetPasswordForm extends StatefulWidget {
  final String token;
  final ValueChanged<KurlUser> onDone;

  const _ResetPasswordForm({required this.token, required this.onDone});

  @override
  State<_ResetPasswordForm> createState() => _ResetPasswordFormState();
}

class _ResetPasswordFormState extends State<_ResetPasswordForm> {
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _loading = false;
  String? _error;

  Future<void> _submit() async {
    final password = _passwordController.text;
    final validationError =
        validatePassword(password) ?? validateConfirmPassword(password, _confirmPasswordController.text);
    if (validationError != null) {
      setState(() => _error = validationError);
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final user = await AuthService.resetPassword(widget.token, password);
      if (mounted) {
        updateUrlState(); // clear ?reset=... so a refresh lands back on the profile
        widget.onDone(user);
      }
    } catch (e) {
      if (mounted) setState(() => _error = e is ApiException ? e.message : friendlyError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  InputDecoration _decoration(String hint, {required Widget suffixIcon}) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: Color(0xFF555555), fontSize: 14),
      filled: true,
      fillColor: const Color(0xFF141414),
      suffixIcon: suffixIcon,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: _borderIdle)),
      enabledBorder:
          OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: _borderIdle)),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: _borderFocused),
      ),
    );
  }

  Widget _visibilityToggle(bool obscured, VoidCallback onPressed) {
    return IconButton(
      icon: Icon(obscured ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: const Color(0xFF888888), size: 18),
      onPressed: _loading ? null : onPressed,
    );
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Set a new password',
                  style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Color(0xFFE5E5E5), letterSpacing: -0.5),
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _passwordController,
                  enabled: !_loading,
                  obscureText: _obscurePassword,
                  style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                  decoration: _decoration(
                    'New password',
                    suffixIcon: _visibilityToggle(
                      _obscurePassword,
                      () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _confirmPasswordController,
                  enabled: !_loading,
                  obscureText: _obscureConfirmPassword,
                  onSubmitted: (_) => _submit(),
                  style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                  decoration: _decoration(
                    'Confirm new password',
                    suffixIcon: _visibilityToggle(
                      _obscureConfirmPassword,
                      () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                    ),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: _errorRed, fontSize: 13)),
                ],
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _loading ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFE5E5E5),
                      foregroundColor: const Color(0xFF0A0A0A),
                      padding: const EdgeInsets.symmetric(vertical: 18),
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: Text(
                      _loading ? '...' : 'Update password',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: -0.2),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AuthForm extends StatefulWidget {
  final ValueChanged<KurlUser> onAuthenticated;

  const _AuthForm({required this.onAuthenticated});

  @override
  State<_AuthForm> createState() => _AuthFormState();
}

class _AuthFormState extends State<_AuthForm> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _isSignup = false;
  bool _loading = false;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _spotifyLoading = false;
  bool _soundcloudLoading = false;
  bool _googleLoading = false;
  String? _error;

  Future<void> _signInWithSpotify() async {
    setState(() {
      _spotifyLoading = true;
      _error = null;
    });
    try {
      final url = await _launchSpotifyAuth();
      if (url == null && mounted) {
        setState(() => _error = 'Spotify sign-in is not available right now.');
      }
    } finally {
      if (mounted) setState(() => _spotifyLoading = false);
    }
  }

  Future<void> _signInWithSoundcloud() async {
    setState(() {
      _soundcloudLoading = true;
      _error = null;
    });
    try {
      final url = await _launchSoundcloudAuth();
      if (url == null && mounted) {
        setState(() => _error = 'SoundCloud sign-in is not available right now.');
      }
    } finally {
      if (mounted) setState(() => _soundcloudLoading = false);
    }
  }

  Future<void> _signInWithGoogle() async {
    setState(() {
      _googleLoading = true;
      _error = null;
    });
    try {
      final url = await _launchGoogleAuth();
      if (url == null && mounted) {
        setState(() => _error = 'YouTube sign-in is not available right now.');
      }
    } finally {
      if (mounted) setState(() => _googleLoading = false);
    }
  }

  Future<void> _submit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    final validationError = validateEmail(email) ??
        validatePassword(password) ??
        (_isSignup ? validateConfirmPassword(password, _confirmPasswordController.text) : null);
    if (validationError != null) {
      setState(() => _error = validationError);
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final user = _isSignup ? await AuthService.signup(email, password) : await AuthService.login(email, password);
      if (mounted) widget.onAuthenticated(user);
    } catch (e) {
      if (mounted) setState(() => _error = e is ApiException ? e.message : friendlyError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  InputDecoration _decoration(String hint, {Widget? suffixIcon}) {
    return InputDecoration(
      hintText: hint,
      hintStyle: const TextStyle(color: Color(0xFF555555), fontSize: 14),
      filled: true,
      fillColor: const Color(0xFF141414),
      suffixIcon: suffixIcon,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: _borderIdle)),
      enabledBorder:
          OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: _borderIdle)),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: _borderFocused),
      ),
    );
  }

  Widget _visibilityToggle(bool obscured, VoidCallback onPressed) {
    return IconButton(
      icon: Icon(obscured ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: const Color(0xFF888888), size: 18),
      onPressed: _loading ? null : onPressed,
    );
  }

  @override
  Widget build(BuildContext context) {
    final spotify = findPlatform('spotify');
    final soundcloud = findPlatform('soundcloud');
    final google = findPlatform('youtubeMusic');

    return SingleChildScrollView(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _isSignup ? 'Create account' : 'Sign in',
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFE5E5E5),
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Save your kurls and set a preferred service.',
                  style: TextStyle(fontSize: 14, color: Color(0xFF888888)),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: (_loading || _spotifyLoading) ? null : _signInWithSpotify,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFE5E5E5),
                      side: BorderSide(color: spotify?.colour ?? _borderIdle),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(spotify?.icon, size: 18, color: spotify?.colour),
                        const SizedBox(width: 8),
                        Text(_spotifyLoading ? 'Connecting...' : 'Continue with Spotify'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: (_loading || _soundcloudLoading) ? null : _signInWithSoundcloud,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFE5E5E5),
                      side: BorderSide(color: soundcloud?.colour ?? _borderIdle),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(soundcloud?.icon, size: 18, color: soundcloud?.colour),
                        const SizedBox(width: 8),
                        Text(_soundcloudLoading ? 'Connecting...' : 'Continue with SoundCloud'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: (_loading || _googleLoading) ? null : _signInWithGoogle,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFE5E5E5),
                      side: BorderSide(color: google?.colour ?? _borderIdle),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(google?.icon, size: 18, color: google?.colour),
                        const SizedBox(width: 8),
                        Text(_googleLoading ? 'Connecting...' : 'Continue with YouTube'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    const Expanded(child: Divider(color: _borderIdle)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: const Text('or', style: TextStyle(color: Color(0xFF555555), fontSize: 12)),
                    ),
                    const Expanded(child: Divider(color: _borderIdle)),
                  ],
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _emailController,
                  enabled: !_loading,
                  keyboardType: TextInputType.emailAddress,
                  style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                  decoration: _decoration('Email'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _passwordController,
                  enabled: !_loading,
                  obscureText: _obscurePassword,
                  onSubmitted: _isSignup ? null : (_) => _submit(),
                  style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                  decoration: _decoration(
                    'Password',
                    suffixIcon: _visibilityToggle(
                      _obscurePassword,
                      () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ),
                ),
                if (!_isSignup) ...[
                  const SizedBox(height: 6),
                  Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: _loading
                          ? null
                          : () => showDialog(context: context, builder: (_) => const _ForgotPasswordDialog()),
                      style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 0)),
                      child: const Text('Forgot password?', style: TextStyle(color: Color(0xFF888888), fontSize: 12)),
                    ),
                  ),
                ],
                if (_isSignup) ...[
                  const SizedBox(height: 12),
                  TextField(
                    controller: _confirmPasswordController,
                    enabled: !_loading,
                    obscureText: _obscureConfirmPassword,
                    onSubmitted: (_) => _submit(),
                    style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                    decoration: _decoration(
                      'Confirm password',
                      suffixIcon: _visibilityToggle(
                        _obscureConfirmPassword,
                        () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                      ),
                    ),
                  ),
                ],
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: _errorRed, fontSize: 13)),
                ],
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _loading ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFE5E5E5),
                      foregroundColor: const Color(0xFF0A0A0A),
                      padding: const EdgeInsets.symmetric(vertical: 18),
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: Text(
                      _loading ? '...' : (_isSignup ? 'Create account' : 'Sign in'),
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: -0.2),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Center(
                  child: TextButton(
                    onPressed: _loading
                        ? null
                        : () => setState(() {
                              _isSignup = !_isSignup;
                              _error = null;
                              _confirmPasswordController.clear();
                            }),
                    child: Text(
                      _isSignup ? 'Already have an account? Sign in' : "No account? Create one",
                      style: const TextStyle(color: Color(0xFF888888), fontSize: 13),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ProfileView extends StatefulWidget {
  final KurlUser user;
  final ValueChanged<KurlUser> onUpdated;
  final VoidCallback onLogout;

  const _ProfileView({required this.user, required this.onUpdated, required this.onLogout});

  @override
  State<_ProfileView> createState() => _ProfileViewState();
}

class _ProfileViewState extends State<_ProfileView> {
  bool _savingPlatform = false;
  SpotifyAccount _spotify = SpotifyAccount.disconnected;
  bool _loadingSpotify = true;
  bool _connectingSpotify = false;
  SoundcloudAccount _soundcloud = SoundcloudAccount.disconnected;
  bool _loadingSoundcloud = true;
  bool _connectingSoundcloud = false;
  GoogleAccount _google = GoogleAccount.disconnected;
  bool _loadingGoogle = true;
  bool _connectingGoogle = false;
  bool _resendingVerification = false;

  @override
  void initState() {
    super.initState();
    _loadSpotifyStatus();
    _loadSoundcloudStatus();
    _loadGoogleStatus();
    WidgetsBinding.instance.addPostFrameCallback((_) => _showSpotifyReturnMessage());
    WidgetsBinding.instance.addPostFrameCallback((_) => _showSoundcloudReturnMessage());
    WidgetsBinding.instance.addPostFrameCallback((_) => _showGoogleReturnMessage());
    WidgetsBinding.instance.addPostFrameCallback((_) => _showVerifyEmailMessage());
  }

  void _showSpotifyReturnMessage() {
    final spotifyParam = Uri.base.queryParameters['spotify'];
    if (spotifyParam == null || !mounted) return;
    _showToast(context, spotifyParam == 'connected' ? 'Spotify connected' : 'Spotify connection failed');
  }

  void _showSoundcloudReturnMessage() {
    final soundcloudParam = Uri.base.queryParameters['soundcloud'];
    if (soundcloudParam == null || !mounted) return;
    _showToast(context, soundcloudParam == 'connected' ? 'SoundCloud connected' : 'SoundCloud connection failed');
  }

  void _showGoogleReturnMessage() {
    final googleParam = Uri.base.queryParameters['google'];
    if (googleParam == null || !mounted) return;
    _showToast(context, googleParam == 'connected' ? 'YouTube connected' : 'YouTube connection failed');
  }

  void _showVerifyEmailMessage() {
    if (Uri.base.queryParameters['verify'] == null || !mounted) return;
    updateUrlState();
    _showToast(context, widget.user.emailVerified ? 'Email verified' : 'Verification link invalid or expired');
  }

  Future<void> _loadSpotifyStatus() async {
    final status = await AuthService.getSpotifyStatus();
    if (mounted) {
      setState(() {
        _spotify = status;
        _loadingSpotify = false;
      });
    }
  }

  Future<void> _connectSpotify() async {
    setState(() => _connectingSpotify = true);
    try {
      await _launchSpotifyAuth();
    } finally {
      if (mounted) setState(() => _connectingSpotify = false);
    }
  }


  Future<void> _loadSoundcloudStatus() async {
    final status = await AuthService.getSoundcloudStatus();
    if (mounted) {
      setState(() {
        _soundcloud = status;
        _loadingSoundcloud = false;
      });
    }
  }

  Future<void> _connectSoundcloud() async {
    setState(() => _connectingSoundcloud = true);
    try {
      await _launchSoundcloudAuth();
    } finally {
      if (mounted) setState(() => _connectingSoundcloud = false);
    }
  }

  Future<void> _loadGoogleStatus() async {
    final status = await AuthService.getGoogleStatus();
    if (mounted) {
      setState(() {
        _google = status;
        _loadingGoogle = false;
      });
    }
  }

  Future<void> _connectGoogle() async {
    setState(() => _connectingGoogle = true);
    try {
      await _launchGoogleAuth();
    } finally {
      if (mounted) setState(() => _connectingGoogle = false);
    }
  }

  Future<void> _resendVerification() async {
    setState(() => _resendingVerification = true);
    try {
      await AuthService.resendVerification();
      if (mounted) _showToast(context, 'Verification email sent');
    } catch (_) {
    } finally {
      if (mounted) setState(() => _resendingVerification = false);
    }
  }

  Future<void> _disconnectSpotify() async {
    setState(() => _connectingSpotify = true);
    try {
      await AuthService.disconnectSpotify();
      if (mounted) setState(() => _spotify = SpotifyAccount.disconnected);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _connectingSpotify = false);
    }
  }

  Future<void> _disconnectSoundcloud() async {
    setState(() => _connectingSoundcloud = true);
    try {
      await AuthService.disconnectSoundcloud();
      if (mounted) setState(() => _soundcloud = SoundcloudAccount.disconnected);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _connectingSoundcloud = false);
    }
  }

  Future<void> _disconnectGoogle() async {
    setState(() => _connectingGoogle = true);
    try {
      await AuthService.disconnectGoogle();
      if (mounted) setState(() => _google = GoogleAccount.disconnected);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _connectingGoogle = false);
    }
  }

  Future<void> _selectPlatform(String id) async {
    setState(() => _savingPlatform = true);
    try {
      final updated = await AuthService.updateProfile(preferredPlatform: id);
      if (mounted) widget.onUpdated(updated);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _savingPlatform = false);
    }
  }

  Future<void> _deselectPlatform() async {
    setState(() => _savingPlatform = true);
    try {
      final updated = await AuthService.updateProfile(clearPreferredPlatform: true);
      if (mounted) widget.onUpdated(updated);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _savingPlatform = false);
    }
  }

  Widget _card({required List<Widget> children}) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: children);
  }

  Widget _serviceChip({
    required BuildContext context,
    required String name,
    required IconData? icon,
    required Color? colour,
    required bool loading,
    required bool connected,
    required bool busy,
    required VoidCallback? onTap,
  }) {
    const onColour = Colors.black;
    final fontSize = MediaQuery.of(context).size.width < 420 ? 11.0 : 13.0;
    return Opacity(
      opacity: busy ? 0.5 : 1,
      child: Material(
        color: connected ? colour : const Color(0xFF141414),
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: (loading || busy) ? null : onTap,
          borderRadius: BorderRadius.circular(8),
          child: Container(
            clipBehavior: Clip.hardEdge,
            decoration: BoxDecoration(
              border: Border.all(color: connected ? colour! : const Color(0xFF333333)),
              borderRadius: BorderRadius.circular(8),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (loading)
                  const SizedBox(
                    height: 14,
                    width: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF555555)),
                  )
                else
                  Icon(icon, size: 16, color: connected ? onColour : colour),
                const SizedBox(width: 4),
                Flexible(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      name,
                      maxLines: 1,
                      softWrap: false,
                      style: TextStyle(
                        fontSize: fontSize,
                        fontWeight: FontWeight.w500,
                        color: connected ? onColour : const Color(0xFFE5E5E5),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _confirmDisconnect(String name, Future<void> Function() onDisconnect) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF141414),
        title: Text('Disconnect $name?', style: const TextStyle(color: Color(0xFFE5E5E5))),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Disconnect', style: TextStyle(color: _errorRed)),
          ),
        ],
      ),
    );
    if (confirmed == true) await onDisconnect();
  }

  @override
  Widget build(BuildContext context) {
    final initial = widget.user.email.isNotEmpty
        ? widget.user.email[0].toUpperCase()
        : widget.user.username.isNotEmpty
            ? widget.user.username[0].toUpperCase()
            : '?';

    return SingleChildScrollView(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 48, 24, 140),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'settings',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFE5E5E5),
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF141414),
                        border: Border.all(color: _borderIdle),
                      ),
                      child: Text(
                        initial,
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Color(0xFFE5E5E5)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          widget.user.email.isNotEmpty
                              ? Text(
                                  widget.user.email,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 14, color: Color(0xFF888888)),
                                )
                              : TextButton(
                                  onPressed: () => showDialog(
                                    context: context,
                                    builder: (_) => _AddEmailDialog(onUpdated: widget.onUpdated),
                                  ),
                                  style: TextButton.styleFrom(
                                    padding: EdgeInsets.zero,
                                    alignment: Alignment.centerLeft,
                                    minimumSize: const Size(0, 0),
                                  ),
                                  child: const Text('Add email', style: TextStyle(fontSize: 14, color: Color(0xFF888888))),
                                ),
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  widget.user.username,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                    color: Color(0xFFE5E5E5),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 4),
                              IconButton(
                                onPressed: () => showDialog(
                                  context: context,
                                  builder: (_) => _EditUsernameDialog(
                                    currentUsername: widget.user.username,
                                    onUpdated: widget.onUpdated,
                                  ),
                                ),
                                icon: const Icon(Icons.edit_outlined, size: 14),
                                color: const Color(0xFF888888),
                                padding: EdgeInsets.zero,
                                constraints: const BoxConstraints(),
                                visualDensity: VisualDensity.compact,
                                tooltip: 'Edit username',
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: widget.onLogout,
                      icon: const Icon(Icons.logout_rounded, size: 20, color: _errorRed),
                      tooltip: 'Log out',
                    ),
                  ],
                ),
                if (widget.user.email.isNotEmpty && !widget.user.emailVerified) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.error_outline, size: 14, color: Color(0xFF888888)),
                      const SizedBox(width: 6),
                      const Text(
                        'Email not verified',
                        style: TextStyle(fontSize: 12, color: Color(0xFF888888)),
                      ),
                      const SizedBox(width: 8),
                      TextButton(
                        onPressed: _resendingVerification ? null : _resendVerification,
                        style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 0)),
                        child: Text(
                          _resendingVerification ? 'Sending...' : 'Resend',
                          style: const TextStyle(fontSize: 12, color: Color(0xFFE5E5E5)),
                        ),
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 28),
                _card(
                  children: [
                    const Text(
                      'Password',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                            decoration: BoxDecoration(
                              color: const Color(0xFF141414),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: _borderIdle),
                            ),
                            child: const Text(
                              '••••••••',
                              style: TextStyle(fontSize: 14, color: Color(0xFFE5E5E5), letterSpacing: 2),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton(
                          onPressed: () => showDialog(
                            context: context,
                            builder: (_) => _ChangePasswordDialog(onUpdated: widget.onUpdated),
                          ),
                          icon: const Icon(Icons.edit_outlined),
                          color: const Color(0xFF888888),
                          tooltip: 'Change password',
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                _card(
                  children: [
                    const Text(
                      'Connected services',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    GridView(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 3,
                        mainAxisSpacing: 8,
                        crossAxisSpacing: 8,
                        mainAxisExtent: 48,
                      ),
                      children: [
                        _serviceChip(
                          context: context,
                          name: 'Spotify',
                          icon: findPlatform('spotify')?.icon,
                          colour: findPlatform('spotify')?.colour,
                          loading: _loadingSpotify,
                          connected: _spotify.connected,
                          busy: _connectingSpotify,
                          onTap: _spotify.connected
                              ? () => _confirmDisconnect('Spotify', _disconnectSpotify)
                              : _connectSpotify,
                        ),
                        _serviceChip(
                          context: context,
                          name: 'YouTube',
                          icon: findPlatform('youtubeMusic')?.icon,
                          colour: findPlatform('youtubeMusic')?.colour,
                          loading: _loadingGoogle,
                          connected: _google.connected,
                          busy: _connectingGoogle,
                          onTap: _google.connected
                              ? () => _confirmDisconnect('YouTube', _disconnectGoogle)
                              : _connectGoogle,
                        ),
                        _serviceChip(
                          context: context,
                          name: 'SoundCloud',
                          icon: findPlatform('soundcloud')?.icon,
                          colour: findPlatform('soundcloud')?.colour,
                          loading: _loadingSoundcloud,
                          connected: _soundcloud.connected,
                          busy: _connectingSoundcloud,
                          onTap: _soundcloud.connected
                              ? () => _confirmDisconnect('SoundCloud', _disconnectSoundcloud)
                              : _connectSoundcloud,
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                _card(
                  children: [
                    const Text(
                      'Preferred service',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    Opacity(
                      opacity: _savingPlatform ? 0.5 : 1,
                      child: PlatformPicker(
                        selected: widget.user.preferredPlatform,
                        onSelect: _selectPlatform,
                        onDeselect: _deselectPlatform,
                        disabled: _savingPlatform,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
