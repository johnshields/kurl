// Cross-platform clipboard paste.
// Web impl uses navigator.clipboard.readText() because Flutter web's
// Clipboard.getData relies on document.execCommand('paste'), which iOS
// Safari blocks.
export 'clipboard_paste_io.dart'
    if (dart.library.js_interop) 'clipboard_paste_web.dart';
