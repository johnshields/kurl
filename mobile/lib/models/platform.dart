import 'package:flutter/material.dart';

class StreamingPlatform {
  final String id;
  final String name;
  final Color colour;

  const StreamingPlatform({
    required this.id,
    required this.name,
    required this.colour,
  });
}

const platforms = [
  StreamingPlatform(id: 'spotify', name: 'Spotify', colour: Color(0xFF1DB954)),
  StreamingPlatform(id: 'appleMusic', name: 'Apple Music', colour: Color(0xFFFA2D48)),
  StreamingPlatform(id: 'youtubeMusic', name: 'YouTube Music', colour: Color(0xFFFF0000)),
  StreamingPlatform(id: 'deezer', name: 'Deezer', colour: Color(0xFFA238FF)),
  StreamingPlatform(id: 'tidal', name: 'Tidal', colour: Color(0xFF000000)),
  StreamingPlatform(id: 'amazonMusic', name: 'Amazon Music', colour: Color(0xFF25D1DA)),
  StreamingPlatform(id: 'pandora', name: 'Pandora', colour: Color(0xFF224099)),
];
