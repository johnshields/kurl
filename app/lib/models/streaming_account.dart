class StreamingAccount {
  final bool connected;
  final String? userId;
  final String? displayName;

  const StreamingAccount({
    required this.connected,
    this.userId,
    this.displayName,
  });

  factory StreamingAccount.fromJson(Map<String, dynamic> json) {
    return StreamingAccount(
      connected: json['connected'] ?? false,
      userId: json['spotifyUserId'] ?? json['googleUserId'] ?? json['soundcloudUserId'],
      displayName: json['displayName'],
    );
  }

  static const disconnected = StreamingAccount(connected: false);
}
