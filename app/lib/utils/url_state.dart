// Push current url + target into the address bar so refresh + share work.
// Web pushes via history.replaceState; native is a no-op.
export 'url_state_io.dart' if (dart.library.js_interop) 'url_state_web.dart';
