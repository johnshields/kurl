/// Whitelist of hosts kurl can resolve. Matches the backend's url_parser.
final _musicHostPattern = RegExp(
  r'^(open\.spotify\.com'
  r'|spotify\.link'
  r'|music\.apple\.com'
  r'|(music\.|www\.|m\.)?youtube\.com'
  r'|youtu\.be'
  r'|(www\.)?deezer\.com'
  r'|dzr\.page\.link'
  r'|(www\.|listen\.)?tidal\.com'
  r'|(www\.)?soundcloud\.com'
  r'|on\.soundcloud\.com'
  r'|music\.amazon\.(com|co\.uk)'
  r'|(www\.)?audiomack\.com'
  r'|(www\.)?pandora\.com)$',
  caseSensitive: false,
);

/// Returns an error message if [input] is not a recognisable music link,
/// or null if it's either empty or valid.
String? validateMusicUrl(String? input) {
  if (input == null) return null;
  final trimmed = input.trim();
  if (trimmed.isEmpty) return null;

  final uri = Uri.tryParse(trimmed);
  if (uri == null || !uri.hasScheme) {
    return 'Not a valid URL';
  }
  if (uri.scheme != 'https' && uri.scheme != 'http') {
    return 'URL must start with http or https';
  }
  if (uri.host.isEmpty) {
    return 'Not a valid URL';
  }
  if (!_musicHostPattern.hasMatch(uri.host)) {
    return "Doesn't look like a music link";
  }
  return null;
}

/// Detects which platform a URL belongs to. Returns the platform ID matching
/// the backend's keys (spotify, appleMusic, youtubeMusic, deezer, tidal, soundcloud),
/// or null if the URL isn't recognised.
String? detectPlatform(String? input) {
  if (input == null) return null;
  final uri = Uri.tryParse(input.trim());
  if (uri == null) return null;
  final host = uri.host.toLowerCase();
  if (host.isEmpty) return null;

  if (host.contains('spotify.com') || host == 'spotify.link') return 'spotify';
  if (host.contains('music.apple.com')) return 'appleMusic';
  if (host.contains('youtube.com') || host == 'youtu.be') return 'youtubeMusic';
  if (host.contains('deezer.com') || host == 'dzr.page.link') return 'deezer';
  if (host.contains('tidal.com')) return 'tidal';
  if (host.contains('soundcloud.com')) return 'soundcloud';
  if (host.contains('music.amazon.')) return 'amazonMusic';
  if (host.contains('audiomack.com')) return 'audiomack';
  if (host.contains('pandora.com')) return 'pandora';
  return null;
}
