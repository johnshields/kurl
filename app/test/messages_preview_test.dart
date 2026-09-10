import 'package:flutter_test/flutter_test.dart';
import 'package:kurl/app/routes/messages.dart';
import 'package:kurl/models/thread.dart';

MessageThread _thread(Map<String, dynamic>? lastMessage) {
  return MessageThread.fromJson({
    'uid': 'THR_1',
    'user': {'uid': 'USR_Y', 'username': 'cool-cat'},
    'lastMessageAt': '2026-09-01T00:00:00.000Z',
    'unread': 0,
    'lastMessage': lastMessage,
  });
}

void main() {
  group('threadPreview', () {
    test('shows the last message body', () {
      final t = _thread({'body': 'yo', 'senderUid': 'USR_Y', 'createdAt': ''});
      expect(threadPreview(t), 'yo');
    });

    test('shows artist and title for a kurl-only message', () {
      final t = _thread({
        'body': null,
        'kurl': {
          'resolved_url': 'https://x',
          'platform': 'spotify',
          'via': 'isrc',
          'artist': 'Fred again..',
          'title': 'Delilah',
        },
        'senderUid': 'USR_Y',
        'createdAt': '',
      });
      expect(threadPreview(t), 'Fred again.. - Delilah');
    });

    test('falls back to "Sent a kurl" without metadata', () {
      final t = _thread({
        'body': null,
        'kurl': {'resolved_url': 'https://x', 'platform': 'spotify', 'via': 'isrc'},
        'senderUid': 'USR_Y',
        'createdAt': '',
      });
      expect(threadPreview(t), 'Sent a kurl');
    });

    test('placeholder for an empty thread', () {
      expect(threadPreview(_thread(null)), 'No messages yet');
    });
  });
}
