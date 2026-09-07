class SpotifyAccount {
  final bool connected;
  final String? spotifyUserId;
  final String? displayName;

  const SpotifyAccount({
    required this.connected,
    this.spotifyUserId,
    this.displayName,
  });

  factory SpotifyAccount.fromJson(Map<String, dynamic> json) {
    return SpotifyAccount(
      connected: json['connected'] ?? false,
      spotifyUserId: json['spotifyUserId'],
      displayName: json['displayName'],
    );
  }

  static const disconnected = SpotifyAccount(connected: false);
}
