/// Matches the backend's own checks (auth_controller.py) so form errors
/// surface before hitting the API, not just after.
final _emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

String? validateEmail(String? input) {
  final trimmed = (input ?? '').trim();
  if (trimmed.isEmpty) return 'Email is required';
  if (!_emailPattern.hasMatch(trimmed)) return 'Not a valid email address';
  return null;
}

String? validatePassword(String? input) {
  final value = input ?? '';
  if (value.isEmpty) return 'Password is required';
  if (value.length < 8) return 'Password must be at least 8 characters';
  return null;
}

String? validateConfirmPassword(String? password, String? confirm) {
  if ((confirm ?? '').isEmpty) return 'Confirm your password';
  if (password != confirm) return "Passwords don't match";
  return null;
}
