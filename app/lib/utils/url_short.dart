// Compact share-URL encoding. Trades robustness for brevity:
// - Strips https:// scheme; readers add it back
// - Escapes only chars that break query parsing (& = ? # + space)

const _escapes = {
  '&': '%26',
  '=': '%3D',
  '?': '%3F',
  '#': '%23',
  '+': '%2B',
  ' ': '%20',
  '%': '%25',
};

String compactEncode(String url) {
  var stripped = url.replaceFirst(RegExp(r'^https?://'), '');
  final buf = StringBuffer();
  for (final ch in stripped.split('')) {
    buf.write(_escapes[ch] ?? ch);
  }
  return buf.toString();
}

String compactDecode(String value) {
  // Uri.decodeComponent handles all %xx -- safe for the small set we emit.
  final decoded = Uri.decodeComponent(value);
  if (decoded.startsWith('http://') || decoded.startsWith('https://')) {
    return decoded;
  }
  return 'https://$decoded';
}

