class GoogleAccount {
  final bool connected;
  final String? googleUserId;
  final String? displayName;

  const GoogleAccount({
    required this.connected,
    this.googleUserId,
    this.displayName,
  });

  factory GoogleAccount.fromJson(Map<String, dynamic> json) {
    return GoogleAccount(
      connected: json['connected'] ?? false,
      googleUserId: json['googleUserId'],
      displayName: json['displayName'],
    );
  }

  static const disconnected = GoogleAccount(connected: false);
}
