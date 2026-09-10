import 'package:flutter_test/flutter_test.dart';
import 'package:kurl/models/friend.dart';
import 'package:kurl/models/message.dart';
import 'package:kurl/models/thread.dart';

void main() {
  group('Friend.fromJson', () {
    test('maps the friendship uid and the other party', () {
      final f = Friend.fromJson({
        'uid': 'FRN_1',
        'user': {'uid': 'USR_Y', 'username': 'cool-cat'},
        'status': 'accepted',
        'createdAt': '2026-09-01T00:00:00.000Z',
        'respondedAt': '2026-09-02T00:00:00.000Z',
      });

      expect(f.uid, 'FRN_1');
      expect(f.user.uid, 'USR_Y');
      expect(f.user.username, 'cool-cat');
      expect(f.status, 'accepted');
      expect(f.respondedAt, '2026-09-02T00:00:00.000Z');
    });
  });

  group('FriendsOverview.fromJson', () {
    test('splits the three buckets', () {
      final o = FriendsOverview.fromJson({
        'friends': [
          {
            'uid': 'FRN_1',
            'user': {'uid': 'USR_Y', 'username': 'a'},
            'status': 'accepted',
            'createdAt': '',
          },
        ],
        'incoming': [
          {
            'uid': 'FRN_2',
            'user': {'uid': 'USR_Z', 'username': 'b'},
            'status': 'pending',
            'createdAt': '',
          },
        ],
        'outgoing': [],
      });

      expect(o.friends.single.uid, 'FRN_1');
      expect(o.incoming.single.uid, 'FRN_2');
      expect(o.outgoing, isEmpty);
    });

    test('missing keys become empty lists', () {
      final o = FriendsOverview.fromJson({});
      expect(o.friends, isEmpty);
      expect(o.incoming, isEmpty);
      expect(o.outgoing, isEmpty);
    });
  });

  group('Message.fromJson', () {
    test('a text-only message', () {
      final m = Message.fromJson({
        'uid': 'MSG_1',
        'threadUid': 'THR_1',
        'senderUid': 'USR_X',
        'body': 'hey',
        'kurl': null,
        'kurlRecipient': null,
        'createdAt': '2026-09-01T00:00:00.000Z',
      });

      expect(m.body, 'hey');
      expect(m.kurl, isNull);
      expect(m.displayKurl, isNull);
    });

    test('an attached kurl parses as a KurlResult', () {
      final m = Message.fromJson({
        'uid': 'MSG_2',
        'threadUid': 'THR_1',
        'senderUid': 'USR_X',
        'body': null,
        'kurl': {
          'resolved_url': 'https://open.spotify.com/track/1',
          'platform': 'spotify',
          'via': 'isrc',
          'title': 'Delilah',
          'artist': 'Fred again..',
        },
        'kurlRecipient': null,
        'createdAt': '',
      });

      expect(m.kurl!.resolvedUrl, 'https://open.spotify.com/track/1');
      expect(m.displayKurl!.platform, 'spotify');
    });
  });

  group('Message.displayKurl', () {
    test('overlays the recipient re-resolve, keeping title and artist', () {
      final m = Message.fromJson({
        'uid': 'MSG_3',
        'threadUid': 'THR_1',
        'senderUid': 'USR_X',
        'body': null,
        'kurl': {
          'resolved_url': 'https://open.spotify.com/track/1',
          'platform': 'spotify',
          'via': 'isrc',
          'title': 'Delilah',
          'artist': 'Fred again..',
        },
        'kurlRecipient': {
          'target_url': 'https://tidal.com/track/9',
          'platform': 'tidal',
          'via': 'isrc',
        },
        'createdAt': '',
      });

      final shown = m.displayKurl!;
      expect(shown.resolvedUrl, 'https://tidal.com/track/9');
      expect(shown.platform, 'tidal');
      expect(shown.title, 'Delilah');
      expect(shown.artist, 'Fred again..');
    });
  });

  group('MessageThread / ThreadDetail', () {
    test('thread-list row: unread count and last-message preview', () {
      final t = MessageThread.fromJson({
        'uid': 'THR_1',
        'user': {'uid': 'USR_Y', 'username': 'cool-cat'},
        'lastMessageAt': '2026-09-01T00:00:00.000Z',
        'unread': 3,
        'lastMessage': {
          'body': 'yo',
          'kurl': null,
          'senderUid': 'USR_Y',
          'createdAt': '2026-09-01T00:00:00.000Z',
        },
      });

      expect(t.unread, 3);
      expect(t.user.username, 'cool-cat');
      expect(t.lastMessage!.body, 'yo');
    });

    test('unread defaults to zero and lastMessage may be absent', () {
      final t = MessageThread.fromJson({
        'uid': 'THR_2',
        'user': {'uid': 'USR_Y', 'username': 'x'},
        'lastMessageAt': '',
      });
      expect(t.unread, 0);
      expect(t.lastMessage, isNull);
    });

    test('ThreadDetail carries the header and the messages', () {
      final d = ThreadDetail.fromJson({
        'thread': {
          'uid': 'THR_1',
          'user': {'uid': 'USR_Y', 'username': 'cool-cat'},
          'lastMessageAt': '',
          'lastReadAt': '2026-09-01T00:00:00.000Z',
        },
        'messages': [
          {
            'uid': 'MSG_1',
            'threadUid': 'THR_1',
            'senderUid': 'USR_X',
            'body': 'hi',
            'createdAt': '',
          },
        ],
      });

      expect(d.thread.lastReadAt, '2026-09-01T00:00:00.000Z');
      expect(d.messages.single.uid, 'MSG_1');
    });
  });
}
