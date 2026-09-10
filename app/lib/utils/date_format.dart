const _months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

String? shortDate(String? iso) {
  if (iso == null || iso.isEmpty) return null;
  final date = DateTime.tryParse(iso);
  if (date == null) return null;
  return '${date.day} ${_months[date.month - 1]}';
}

// Compact age of a timestamp: "now", "5m", "3h", "2d", then the short date.
String relativeTime(String? iso) {
  if (iso == null || iso.isEmpty) return '';
  final t = DateTime.tryParse(iso);
  if (t == null) return '';
  final diff = DateTime.now().difference(t);
  if (diff.isNegative || diff.inSeconds < 60) return 'now';
  if (diff.inMinutes < 60) return '${diff.inMinutes}m';
  if (diff.inHours < 24) return '${diff.inHours}h';
  if (diff.inDays < 7) return '${diff.inDays}d';
  return shortDate(iso) ?? '';
}
