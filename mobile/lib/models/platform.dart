import 'package:flutter/material.dart';
import 'package:simple_icons/simple_icons.dart';

class StreamingPlatform {
  final String id;
  final String name;
  final Color colour;
  final IconData icon;

  const StreamingPlatform({
    required this.id,
    required this.name,
    required this.colour,
    required this.icon,
  });
}

const platforms = [
  StreamingPlatform(
    id: 'spotify',
    name: 'Spotify',
    colour: Color(0xFF1DB954),
    icon: SimpleIcons.spotify,
  ),
  StreamingPlatform(
    id: 'appleMusic',
    name: 'Apple',
    colour: Color(0xFFFA2D48),
    icon: SimpleIcons.applemusic,
  ),
  StreamingPlatform(
    id: 'youtubeMusic',
    name: 'YouTube',
    colour: Color(0xFFFF0000),
    icon: SimpleIcons.youtubemusic,
  ),
];

StreamingPlatform? findPlatform(String id) {
  for (final p in platforms) {
    if (p.id == id) return p;
  }
  return null;
}
