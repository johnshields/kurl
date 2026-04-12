class ResolveResult {
  final String? title;
  final String? artist;
  final String resolvedUrl;
  final String platform;
  final bool cached;

  const ResolveResult({
    this.title,
    this.artist,
    required this.resolvedUrl,
    required this.platform,
    required this.cached,
  });

  factory ResolveResult.fromJson(Map<String, dynamic> json) {
    return ResolveResult(
      title: json['title'],
      artist: json['artist'],
      resolvedUrl: json['resolved_url'],
      platform: json['platform'],
      cached: json['cached'] ?? false,
    );
  }
}
