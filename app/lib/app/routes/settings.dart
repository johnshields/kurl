import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:kurl/models/platform.dart';
import 'package:kurl/models/spotify_account.dart';
import 'package:kurl/models/user.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/utils/auth_validator.dart';
import 'package:kurl/utils/friendly_error.dart';
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
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: _loading
            ? const Center(
                child: CircularProgressIndicator(color: Color(0xFF555555), strokeWidth: 2),
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

  @override
  void initState() {
    super.initState();
    _usernameController = TextEditingController(text: widget.user.username);
    _loadSpotifyStatus();
    WidgetsBinding.instance.addPostFrameCallback((_) => _showSpotifyReturnMessage());
  }

  void _showSpotifyReturnMessage() {
    final spotifyParam = Uri.base.queryParameters['spotify'];
    if (spotifyParam == null || !mounted) return;
    final message = spotifyParam == 'connected' ? 'Spotify connected' : 'Spotify connection failed';
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
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
                  'Settings',
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
                    Text(widget.user.email, style: const TextStyle(fontSize: 14, color: Color(0xFF888888))),
                  ],
                ),
                const SizedBox(height: 24),
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
                const SizedBox(height: 16),
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
                const SizedBox(height: 16),
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
                const SizedBox(height: 32),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: widget.onLogout,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _errorRed,
                      foregroundColor: const Color(0xFF0A0A0A),
                      padding: const EdgeInsets.symmetric(vertical: 18),
                      elevation: 0,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.logout_rounded, size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Log out',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: -0.2),
                        ),
                      ],
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
