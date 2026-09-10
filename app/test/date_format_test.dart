import 'package:flutter_test/flutter_test.dart';
import 'package:kurl/utils/date_format.dart';

String _ago(Duration d) => DateTime.now().toUtc().subtract(d).toIso8601String();

void main() {
  group('relativeTime', () {
    test('empty or unparseable input', () {
      expect(relativeTime(null), '');
      expect(relativeTime(''), '');
      expect(relativeTime('not-a-date'), '');
    });

    test('recent timestamps collapse to "now"', () {
      expect(relativeTime(_ago(const Duration(seconds: 20))), 'now');
    });

    test('minutes, hours and days', () {
      expect(relativeTime(_ago(const Duration(minutes: 5))), '5m');
      expect(relativeTime(_ago(const Duration(hours: 3))), '3h');
      expect(relativeTime(_ago(const Duration(days: 2))), '2d');
    });

    test('older than a week falls back to the short date', () {
      final old = DateTime.utc(2026, 1, 15).toIso8601String();
      expect(relativeTime(old), '15 Jan');
    });
  });
}
