import 'package:flutter/material.dart';
import 'package:kurl/app/routes/settings/settings_style.dart';
import 'package:kurl/models/user.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/utils/auth_validator.dart';
import 'package:kurl/utils/friendly_error.dart';
import 'package:kurl/utils/url_state.dart';

class ResetPasswordForm extends StatefulWidget {
  final String token;
  final ValueChanged<KurlUser> onDone;

  const ResetPasswordForm({super.key, required this.token, required this.onDone});

  @override
  State<ResetPasswordForm> createState() => _ResetPasswordFormState();
}

class _ResetPasswordFormState extends State<ResetPasswordForm> {
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
                  decoration: darkInputDecoration(
                    'New password',
                    suffixIcon: visibilityToggle(
                      _obscurePassword,
                      () => setState(() => _obscurePassword = !_obscurePassword),
                      enabled: !_loading,
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
                  decoration: darkInputDecoration(
                    'Confirm new password',
                    suffixIcon: visibilityToggle(
                      _obscureConfirmPassword,
                      () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                      enabled: !_loading,
                    ),
                  ),
                ),
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
