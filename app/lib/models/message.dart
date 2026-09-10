import 'package:kurl/models/kurl_result.dart';

/// The recipient-preferred re-resolve stored alongside an attached kurl:
/// only the fields that differ from the sender's snapshot.
class KurlRecipient {
  final String targetUrl;
  final String platform;
  final String via;

  const KurlRecipient({
    required this.targetUrl,
    required this.platform,
    required this.via,
  });

  factory KurlRecipient.fromJson(Map<String, dynamic> json) {
    return KurlRecipient(
      targetUrl: json['target_url'],
      platform: json['platform'],
      via: json['via'],
    );
  }
}

class Message {
  final String uid;
  final String threadUid;
  final String senderUid;
  final String? body;
  final KurlResult? kurl; // sender's resolved snapshot
  final KurlRecipient? kurlRecipient; // re-resolve for this recipient, if any
  final String createdAt;

  const Message({
    required this.uid,
    required this.threadUid,
    required this.senderUid,
    this.body,
    this.kurl,
    this.kurlRecipient,
    required this.createdAt,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      uid: json['uid'],
      threadUid: json['threadUid'],
      senderUid: json['senderUid'],
      body: json['body'],
      kurl: json['kurl'] == null ? null : KurlResult.fromJson(json['kurl']),
      kurlRecipient: json['kurlRecipient'] == null
          ? null
          : KurlRecipient.fromJson(json['kurlRecipient']),
      createdAt: json['createdAt'] ?? '',
    );
  }

  /// The kurl to show this recipient -- the preferred-platform re-resolve
  /// when present, otherwise the sender's original.
  KurlResult? get displayKurl {
    final k = kurl;
    if (k == null) return null;
    final r = kurlRecipient;
    if (r == null) return k;
    return KurlResult(
      title: k.title,
      artist: k.artist,
      resolvedUrl: r.targetUrl,
      platform: r.platform,
      via: r.via,
      artworkUrl: k.artworkUrl,
      createdAt: k.createdAt,
    );
  }
}
