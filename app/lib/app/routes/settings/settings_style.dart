import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:kurl/services/auth_service.dart';

const errorRed = Color(0xFFEF4444);
const borderIdle = Color(0xFF333333);
const borderFocused = Color(0xFF555555);

/// Starts the OAuth flow and navigates there. Returns the opened URL, or
/// null if that sign-in is unavailable.
Future<String?> launchStreamingAuth(String provider) async {
  final url = await AuthService.startStreamingAuth(provider);
  if (url != null) await launchUrl(Uri.parse(url), webOnlyWindowName: '_self');
  return url;
}

void showToast(BuildContext context, String message) {
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
              border: Border.all(color: borderIdle),
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

/// Dark-theme text field decoration. [dialog] uses the darker dialog fill and
/// drops the enabled/focused border states the full-screen forms carry.
InputDecoration darkInputDecoration(String hint, {Widget? suffixIcon, bool dialog = false}) {
  final border = OutlineInputBorder(
    borderRadius: BorderRadius.circular(8),
    borderSide: const BorderSide(color: borderIdle),
  );
  return InputDecoration(
    hintText: hint,
    hintStyle: const TextStyle(color: Color(0xFF555555), fontSize: 14),
    filled: true,
    fillColor: dialog ? const Color(0xFF0A0A0A) : const Color(0xFF141414),
    suffixIcon: suffixIcon,
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    border: border,
    enabledBorder: dialog ? null : border,
    focusedBorder: dialog
        ? null
        : OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: borderFocused),
          ),
  );
}

Widget visibilityToggle(bool obscured, VoidCallback onPressed, {bool enabled = true}) {
  return IconButton(
    icon: Icon(
      obscured ? Icons.visibility_off_outlined : Icons.visibility_outlined,
      color: const Color(0xFF888888),
      size: 18,
    ),
    onPressed: enabled ? onPressed : null,
  );
}
