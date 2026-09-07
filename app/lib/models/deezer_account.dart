class DeezerAccount {
  final bool connected;
  final String? deezerUserId;
  final String? displayName;

  const DeezerAccount({
    required this.connected,
    this.deezerUserId,
    this.displayName,
  });

  factory DeezerAccount.fromJson(Map<String, dynamic> json) {
    return DeezerAccount(
      connected: json['connected'] ?? false,
      deezerUserId: json['deezerUserId'],
      displayName: json['displayName'],
    );
  }

  static const disconnected = DeezerAccount(connected: false);
}
