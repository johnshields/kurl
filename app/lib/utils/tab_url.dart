// Sync the selected tab with the address bar path so refresh + share work.
// Web pushes via history.pushState; native is a no-op.
export 'tab_url_io.dart' if (dart.library.js_interop) 'tab_url_web.dart';
