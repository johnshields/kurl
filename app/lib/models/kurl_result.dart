class KurlResult {
  final String? title;
  final String? artist;
  final String resolvedUrl;
  final String platform;
  final bool cached;
  final String via;
  final String? artworkUrl;

  const KurlResult({
    this.title,
    this.artist,
    required this.resolvedUrl,
    required this.platform,
    required this.cached,
    required this.via,
    this.artworkUrl,
  });

  bool get isSearch => via == 'search';

  factory KurlResult.fromJson(Map<String, dynamic> json) {
    return KurlResult(
      title: json['title'],
      artist: json['artist'],
      resolvedUrl: json['resolved_url'],
      platform: json['platform'],
      cached: json['cached'] ?? false,
      via: json['via'] ?? 'direct',
      artworkUrl: json['artwork_url'],
    );
  }
}
