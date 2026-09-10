import 'package:flutter/material.dart';
import 'package:kurl/app/routes/settings/settings_style.dart';
import 'package:kurl/models/user.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/utils/auth_validator.dart';
import 'package:kurl/utils/friendly_error.dart';

class ForgotPasswordDialog extends StatefulWidget {
  const ForgotPasswordDialog({super.key});

  @override
  State<ForgotPasswordDialog> createState() => _ForgotPasswordDialogState();
}

class _ForgotPasswordDialogState extends State<ForgotPasswordDialog> {
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
                  decoration: darkInputDecoration('Email', dialog: true),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 8),
                  Text(_error!, style: const TextStyle(color: errorRed, fontSize: 12)),
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

class ChangePasswordDialog extends StatefulWidget {
  final ValueChanged<KurlUser> onUpdated;

  const ChangePasswordDialog({super.key, required this.onUpdated});

  @override
  State<ChangePasswordDialog> createState() => _ChangePasswordDialogState();
}

class _ChangePasswordDialogState extends State<ChangePasswordDialog> {
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
        showToast(context, 'Password updated');
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
            decoration: darkInputDecoration(
              'New password',
              dialog: true,
              suffixIcon: visibilityToggle(
                _obscurePassword,
                () => setState(() => _obscurePassword = !_obscurePassword),
                enabled: !_saving,
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _confirmPasswordController,
            enabled: !_saving,
            obscureText: _obscureConfirmPassword,
            onSubmitted: (_) => _save(),
            style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
            decoration: darkInputDecoration(
              'Confirm new password',
              dialog: true,
              suffixIcon: visibilityToggle(
                _obscureConfirmPassword,
                () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                enabled: !_saving,
              ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: errorRed, fontSize: 12)),
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

class AddEmailDialog extends StatefulWidget {
  final ValueChanged<KurlUser> onUpdated;

  const AddEmailDialog({super.key, required this.onUpdated});

  @override
  State<AddEmailDialog> createState() => _AddEmailDialogState();
}

class _AddEmailDialogState extends State<AddEmailDialog> {
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
        showToast(context, 'Email added');
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
            decoration: darkInputDecoration('Email', dialog: true),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: errorRed, fontSize: 12)),
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

class EditUsernameDialog extends StatefulWidget {
  final String currentUsername;
  final ValueChanged<KurlUser> onUpdated;

  const EditUsernameDialog({super.key, required this.currentUsername, required this.onUpdated});

  @override
  State<EditUsernameDialog> createState() => _EditUsernameDialogState();
}

class _EditUsernameDialogState extends State<EditUsernameDialog> {
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
        showToast(context, 'Username updated');
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
            decoration: darkInputDecoration('Username', dialog: true),
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: errorRed, fontSize: 12)),
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
