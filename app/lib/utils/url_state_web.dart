import 'package:web/web.dart' as web;

import 'package:kurl/utils/url_short.dart';

// Replace current entry so back button isn't polluted with state-only updates.
void updateUrlState({String? url, String? target}) {
  final params = <String, String>{};
  if (url != null && url.isNotEmpty) params['url'] = compactEncode(url);
  if (target != null && target.isNotEmpty) params['target'] = target;

  final query = params.isEmpty
      ? ''
      : '?${params.entries.map((e) => '${e.key}=${e.value}').join('&')}';

  final loc = web.window.location;
  final next = '${loc.pathname}$query';
  web.window.history.replaceState(null, '', next);
}

String buildShareUrl({required String url, required String target}) {
  return 'https://kurl.online/?url=${compactEncode(url)}&target=$target';
}
