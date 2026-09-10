import 'package:flutter_test/flutter_test.dart';
import 'package:kurl/models/kurl_result.dart';

void main() {
  group('KurlResult.toJson', () {
    test('emits snake_case keys and drops null optionals', () {
      final json = const KurlResult(
        resolvedUrl: 'https://open.spotify.com/track/1',
        platform: 'spotify',
        via: 'isrc',
        title: 'Delilah',
        artist: 'Fred again..',
      ).toJson();

      expect(json, {
        'title': 'Delilah',
        'artist': 'Fred again..',
        'resolved_url': 'https://open.spotify.com/track/1',
        'platform': 'spotify',
        'via': 'isrc',
      });
      expect(json.containsKey('artwork_url'), isFalse);
    });

    test('round-trips through fromJson', () {
      const original = KurlResult(
        resolvedUrl: 'https://tidal.com/track/9',
        platform: 'tidal',
        via: 'upc',
        artworkUrl: 'https://img/art.jpg',
      );

      final back = KurlResult.fromJson(original.toJson());
      expect(back.resolvedUrl, original.resolvedUrl);
      expect(back.platform, 'tidal');
      expect(back.via, 'upc');
      expect(back.artworkUrl, 'https://img/art.jpg');
    });
  });
}
