import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:kurl/models/deezer_account.dart';
import 'package:kurl/models/platform.dart';
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

/// Same as [_launchSpotifyAuth], for Deezer.
Future<String?> _launchDeezerAuth() async {
  final url = await AuthService.startDeezerAuth();
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
        // Best-effort -- a stale/invalid link just falls through to the profile as-is.
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
  bool _deezerLoading = false;
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

  Future<void> _signInWithDeezer() async {
    setState(() {
      _deezerLoading = true;
      _error = null;
    });
    try {
      final url = await _launchDeezerAuth();
      if (url == null && mounted) {
        setState(() => _error = 'Deezer sign-in is not available right now.');
      }
    } finally {
      if (mounted) setState(() => _deezerLoading = false);
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
    final deezer = findPlatform('deezer');

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
                  'Save your kurls and set a preferred platform.',
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
                    onPressed: (_loading || _deezerLoading) ? null : _signInWithDeezer,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFE5E5E5),
                      side: BorderSide(color: deezer?.colour ?? _borderIdle),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(deezer?.icon, size: 18, color: deezer?.colour),
                        const SizedBox(width: 8),
                        Text(_deezerLoading ? 'Connecting...' : 'Continue with Deezer'),
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
  late final TextEditingController _usernameController;
  bool _savingUsername = false;
  bool _savingPlatform = false;
  String? _usernameError;
  SpotifyAccount _spotify = SpotifyAccount.disconnected;
  bool _loadingSpotify = true;
  bool _connectingSpotify = false;
  DeezerAccount _deezer = DeezerAccount.disconnected;
  bool _loadingDeezer = true;
  bool _connectingDeezer = false;
  bool _resendingVerification = false;

  @override
  void initState() {
    super.initState();
    _usernameController = TextEditingController(text: widget.user.username);
    _loadSpotifyStatus();
    _loadDeezerStatus();
    WidgetsBinding.instance.addPostFrameCallback((_) => _showSpotifyReturnMessage());
    WidgetsBinding.instance.addPostFrameCallback((_) => _showDeezerReturnMessage());
    WidgetsBinding.instance.addPostFrameCallback((_) => _showVerifyEmailMessage());
  }

  void _showSpotifyReturnMessage() {
    final spotifyParam = Uri.base.queryParameters['spotify'];
    if (spotifyParam == null || !mounted) return;
    _showToast(context, spotifyParam == 'connected' ? 'Spotify connected' : 'Spotify connection failed');
  }

  void _showDeezerReturnMessage() {
    final deezerParam = Uri.base.queryParameters['deezer'];
    if (deezerParam == null || !mounted) return;
    _showToast(context, deezerParam == 'connected' ? 'Deezer connected' : 'Deezer connection failed');
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

  Future<void> _loadDeezerStatus() async {
    final status = await AuthService.getDeezerStatus();
    if (mounted) {
      setState(() {
        _deezer = status;
        _loadingDeezer = false;
      });
    }
  }

  Future<void> _connectDeezer() async {
    setState(() => _connectingDeezer = true);
    try {
      await _launchDeezerAuth();
    } finally {
      if (mounted) setState(() => _connectingDeezer = false);
    }
  }

  Future<void> _resendVerification() async {
    setState(() => _resendingVerification = true);
    try {
      await AuthService.resendVerification();
      if (mounted) _showToast(context, 'Verification email sent');
    } catch (_) {
      // Best-effort -- no feedback needed beyond the button re-enabling.
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
      // Best-effort -- the card simply won't reflect the change on failure.
    } finally {
      if (mounted) setState(() => _connectingSpotify = false);
    }
  }

  Future<void> _disconnectDeezer() async {
    setState(() => _connectingDeezer = true);
    try {
      await AuthService.disconnectDeezer();
      if (mounted) setState(() => _deezer = DeezerAccount.disconnected);
    } catch (_) {
      // Best-effort -- the card simply won't reflect the change on failure.
    } finally {
      if (mounted) setState(() => _connectingDeezer = false);
    }
  }

  @override
  void didUpdateWidget(covariant _ProfileView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.user.username != widget.user.username) {
      _usernameController.text = widget.user.username;
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    super.dispose();
  }

  Future<void> _saveUsername() async {
    final username = _usernameController.text.trim();
    if (username.isEmpty || username == widget.user.username) return;

    setState(() {
      _savingUsername = true;
      _usernameError = null;
    });
    try {
      final updated = await AuthService.updateProfile(username: username);
      if (mounted) widget.onUpdated(updated);
    } catch (e) {
      if (mounted) setState(() => _usernameError = e is ApiException ? e.message : friendlyError(e));
    } finally {
      if (mounted) setState(() => _savingUsername = false);
    }
  }

  Future<void> _selectPlatform(String id) async {
    setState(() => _savingPlatform = true);
    try {
      final updated = await AuthService.updateProfile(preferredPlatform: id);
      if (mounted) widget.onUpdated(updated);
    } catch (_) {
      // Best-effort -- the picker simply won't reflect the change on failure.
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
      // Best-effort -- the picker simply won't reflect the change on failure.
    } finally {
      if (mounted) setState(() => _savingPlatform = false);
    }
  }

  Widget _card({required List<Widget> children}) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: children);
  }

  @override
  Widget build(BuildContext context) {
    final initial = widget.user.email.isNotEmpty ? widget.user.email[0].toUpperCase() : '?';

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
                      child: Text(
                        widget.user.email,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 14, color: Color(0xFF888888)),
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
                      'Username',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _usernameController,
                            enabled: !_savingUsername,
                            onSubmitted: (_) => _saveUsername(),
                            style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                            decoration: InputDecoration(
                              filled: true,
                              fillColor: const Color(0xFF141414),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(8),
                                borderSide: const BorderSide(color: _borderIdle),
                              ),
                              enabledBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(8),
                                borderSide: const BorderSide(color: _borderIdle),
                              ),
                              focusedBorder: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(8),
                                borderSide: const BorderSide(color: _borderFocused),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        ValueListenableBuilder<TextEditingValue>(
                          valueListenable: _usernameController,
                          builder: (context, value, _) {
                            final unchanged = value.text.trim() == widget.user.username;
                            return Opacity(
                              opacity: unchanged ? 0.3 : 1,
                              child: IconButton(
                                onPressed: (_savingUsername || unchanged) ? null : _saveUsername,
                                icon: const Icon(Icons.check),
                                color: const Color(0xFF888888),
                                tooltip: 'Save username',
                              ),
                            );
                          },
                        ),
                      ],
                    ),
                    if (_usernameError != null) ...[
                      const SizedBox(height: 6),
                      Text(_usernameError!, style: const TextStyle(color: _errorRed, fontSize: 12)),
                    ],
                  ],
                ),
                const SizedBox(height: 24),
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
                      'Spotify',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    if (_loadingSpotify)
                      const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(color: Color(0xFF555555), strokeWidth: 2),
                      )
                    else if (_spotify.connected)
                      Row(
                        children: [
                          const Icon(Icons.check_circle, size: 16, color: Color(0xFF1DB954)),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Connected as ${_spotify.displayName ?? _spotify.spotifyUserId}',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                            ),
                          ),
                          TextButton(
                            onPressed: _connectingSpotify ? null : _disconnectSpotify,
                            child: const Text('Disconnect', style: TextStyle(color: _errorRed, fontSize: 13)),
                          ),
                        ],
                      )
                    else
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton(
                          onPressed: _connectingSpotify ? null : _connectSpotify,
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFFE5E5E5),
                            side: const BorderSide(color: _borderIdle),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                          ),
                          child: Text(_connectingSpotify ? 'Connecting...' : 'Connect Spotify'),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 24),
                _card(
                  children: [
                    const Text(
                      'Deezer',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    if (_loadingDeezer)
                      const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(color: Color(0xFF555555), strokeWidth: 2),
                      )
                    else if (_deezer.connected)
                      Row(
                        children: [
                          Icon(Icons.check_circle, size: 16, color: findPlatform('deezer')?.colour),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Connected as ${_deezer.displayName ?? _deezer.deezerUserId}',
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                            ),
                          ),
                          TextButton(
                            onPressed: _connectingDeezer ? null : _disconnectDeezer,
                            child: const Text('Disconnect', style: TextStyle(color: _errorRed, fontSize: 13)),
                          ),
                        ],
                      )
                    else
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton(
                          onPressed: _connectingDeezer ? null : _connectDeezer,
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFFE5E5E5),
                            side: const BorderSide(color: _borderIdle),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                          ),
                          child: Text(_connectingDeezer ? 'Connecting...' : 'Connect Deezer'),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 24),
                _card(
                  children: [
                    const Text(
                      'Preferred platform',
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
