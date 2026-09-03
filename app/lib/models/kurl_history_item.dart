class KurlHistoryItem {
  final String uid;
  final String sourceUrl;
  final String targetUrl;
  final String platform;
  final String via;
  final String? title;
  final String? artist;
  final String createdAt;

  const KurlHistoryItem({
    required this.uid,
    required this.sourceUrl,
    required this.targetUrl,
    required this.platform,
    required this.via,
    this.title,
    this.artist,
    required this.createdAt,
  });

  factory KurlHistoryItem.fromJson(Map<String, dynamic> json) {
    return KurlHistoryItem(
      uid: json['uid'],
      sourceUrl: json['sourceUrl'],
      targetUrl: json['targetUrl'],
      platform: json['platform'],
      via: json['via'],
      title: json['title'],
      artist: json['artist'],
      createdAt: json['createdAt'] ?? '',
    );
  }
}
