class SoundcloudAccount {
  final bool connected;
  final String? soundcloudUserId;
  final String? displayName;

  const SoundcloudAccount({
    required this.connected,
    this.soundcloudUserId,
    this.displayName,
  });

  factory SoundcloudAccount.fromJson(Map<String, dynamic> json) {
    return SoundcloudAccount(
      connected: json['connected'] ?? false,
      soundcloudUserId: json['soundcloudUserId'],
      displayName: json['displayName'],
    );
  }

  static const disconnected = SoundcloudAccount(connected: false);
}
