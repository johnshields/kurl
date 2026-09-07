import 'package:flutter_test/flutter_test.dart';
import 'package:kurl/models/user.dart';

void main() {
  group('KurlUser.fromJson', () {
    test('handles a null email (SoundCloud accounts have none)', () {
      final user = KurlUser.fromJson({
        'uid': 'USR_X',
        'email': null,
        'username': 'brave-otter',
        'preferredPlatform': null,
        'emailVerified': false,
        'createdAt': '2026-09-07T00:00:00.000Z',
      });

      expect(user.email, '');
    });

    test('keeps a real email', () {
      final user = KurlUser.fromJson({
        'uid': 'USR_X',
        'email': 'jane@example.com',
        'username': 'brave-otter',
        'preferredPlatform': null,
        'emailVerified': true,
        'createdAt': '2026-09-07T00:00:00.000Z',
      });

      expect(user.email, 'jane@example.com');
    });
  });
}
