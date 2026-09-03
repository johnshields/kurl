import 'package:web/web.dart' as web;

String currentTabPath() => web.window.location.pathname;

// Pushed (not replaced) so the browser back button steps between tabs.
void updateTabPath(String path) {
  final loc = web.window.location;
  if (loc.pathname == path) return;
  web.window.history.pushState(null, '', path);
}
