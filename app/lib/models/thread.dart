import 'package:kurl/models/kurl_result.dart';
import 'package:kurl/models/message.dart';
import 'package:kurl/models/user_ref.dart';

class MessagePreview {
  final String? body;
  final KurlResult? kurl;
  final String senderUid;
  final String createdAt;

  const MessagePreview({
    this.body,
    this.kurl,
    required this.senderUid,
    required this.createdAt,
  });

  factory MessagePreview.fromJson(Map<String, dynamic> json) {
    return MessagePreview(
      body: json['body'],
      kurl: json['kurl'] == null ? null : KurlResult.fromJson(json['kurl']),
      senderUid: json['senderUid'] ?? '',
      createdAt: json['createdAt'] ?? '',
    );
  }
}

class MessageThread {
  final String uid;
  final UserRef user; // the other participant
  final String lastMessageAt;
  final int unread;
  final MessagePreview? lastMessage; // thread-list rows only
  final String? lastReadAt; // thread-detail header only

  const MessageThread({
    required this.uid,
    required this.user,
    required this.lastMessageAt,
    this.unread = 0,
    this.lastMessage,
    this.lastReadAt,
  });

  factory MessageThread.fromJson(Map<String, dynamic> json) {
    return MessageThread(
      uid: json['uid'],
      user: UserRef.fromJson(json['user']),
      lastMessageAt: json['lastMessageAt'] ?? '',
      unread: json['unread'] ?? 0,
      lastMessage: json['lastMessage'] == null
          ? null
          : MessagePreview.fromJson(json['lastMessage']),
      lastReadAt: json['lastReadAt'],
    );
  }
}

class ThreadDetail {
  final MessageThread thread;
  final List<Message> messages;

  const ThreadDetail({required this.thread, required this.messages});

  factory ThreadDetail.fromJson(Map<String, dynamic> json) {
    return ThreadDetail(
      thread: MessageThread.fromJson(json['thread']),
      messages: (json['messages'] as List? ?? const [])
          .map((e) => Message.fromJson(e))
          .toList(),
    );
  }
}
