import 'package:flutter/material.dart';
import 'package:kurl/app/routes/settings/settings_dialogs.dart';
import 'package:kurl/app/routes/settings/settings_style.dart';
import 'package:kurl/models/platform.dart';
import 'package:kurl/models/streaming_provider.dart';
import 'package:kurl/models/user.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/utils/auth_validator.dart';
import 'package:kurl/utils/friendly_error.dart';

class AuthForm extends StatefulWidget {
  final ValueChanged<KurlUser> onAuthenticated;

  const AuthForm({super.key, required this.onAuthenticated});

  @override
  State<AuthForm> createState() => _AuthFormState();
}

class _AuthFormState extends State<AuthForm> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _isSignup = false;
  bool _loading = false;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  final Set<StreamingProvider> _connecting = {};
  String? _error;

  Future<void> _signInWith(StreamingProvider provider) async {
    setState(() {
      _connecting.add(provider);
      _error = null;
    });
    try {
      final url = await launchStreamingAuth(provider.key);
      if (url == null && mounted) {
        setState(() => _error = '${provider.label} sign-in is not available right now.');
      }
    } finally {
      if (mounted) setState(() => _connecting.remove(provider));
    }
  }

  Widget _providerButton(StreamingProvider provider) {
    final platform = findPlatform(provider.platformId);
    final connecting = _connecting.contains(provider);
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton(
        onPressed: (_loading || connecting) ? null : () => _signInWith(provider),
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFFE5E5E5),
          side: BorderSide(color: platform?.colour ?? borderIdle),
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(platform?.icon, size: 18, color: platform?.colour),
            const SizedBox(width: 8),
            Text(connecting ? 'Connecting...' : 'Continue with ${provider.label}'),
          ],
        ),
      ),
    );
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
                for (var i = 0; i < StreamingProvider.values.length; i++) ...[
                  if (i > 0) const SizedBox(height: 8),
                  _providerButton(StreamingProvider.values[i]),
                ],
                const SizedBox(height: 20),
                Row(
                  children: [
                    const Expanded(child: Divider(color: borderIdle)),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: const Text('or', style: TextStyle(color: Color(0xFF555555), fontSize: 12)),
                    ),
                    const Expanded(child: Divider(color: borderIdle)),
                  ],
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _emailController,
                  enabled: !_loading,
                  keyboardType: TextInputType.emailAddress,
                  style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                  decoration: darkInputDecoration('Email'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _passwordController,
                  enabled: !_loading,
                  obscureText: _obscurePassword,
                  onSubmitted: _isSignup ? null : (_) => _submit(),
                  style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                  decoration: darkInputDecoration(
                    'Password',
                    suffixIcon: visibilityToggle(
                      _obscurePassword,
                      () => setState(() => _obscurePassword = !_obscurePassword),
                      enabled: !_loading,
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
                          : () => showDialog(context: context, builder: (_) => const ForgotPasswordDialog()),
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
                    decoration: darkInputDecoration(
                      'Confirm password',
                      suffixIcon: visibilityToggle(
                        _obscureConfirmPassword,
                        () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                        enabled: !_loading,
                      ),
                    ),
                  ),
                ],
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: errorRed, fontSize: 13)),
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
