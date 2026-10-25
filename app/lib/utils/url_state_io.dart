import 'package:kurl/utils/url_short.dart';

// Native: no address bar to sync; no-op.
void updateUrlState({String? url, String? target}) {}

String buildShareUrl({required String url, required String target}) {
  return 'https://kurl.fromlost.com/?url=${compactEncode(url)}&target=$target';
}
