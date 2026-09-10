/// A "sign in with" streaming service.
/// key: OAuth URL segment; platformId: findPlatform() lookup for icon and colour.
enum StreamingProvider {
  spotify('spotify', 'Spotify', 'spotify'),
  soundcloud('soundcloud', 'SoundCloud', 'soundcloud'),
  google('google', 'YouTube', 'youtubeMusic');

  const StreamingProvider(this.key, this.label, this.platformId);

  final String key;
  final String label;
  final String platformId;
}
