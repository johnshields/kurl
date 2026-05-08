import 'dart:js_interop';

import 'package:web/web.dart' as web;

// Web paste -- navigator.clipboard.readText() works on iOS Safari 13.4+
// when called from a user gesture (button click). Returns null on
// permission denial or unsupported browsers.
Future<String?> readClipboardText() async {
  try {
    final clipboard = web.window.navigator.clipboard;
    final result = await clipboard.readText().toDart;
    return result.toDart;
  } catch (_) {
    return null;
  }
}
