import 'package:flutter/services.dart';

// Native paste -- Flutter Clipboard works on iOS/Android/desktop.
Future<String?> readClipboardText() async {
  final data = await Clipboard.getData(Clipboard.kTextPlain);
  return data?.text;
}
