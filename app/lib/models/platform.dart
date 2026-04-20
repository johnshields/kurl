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
  StreamingPlatform(
    id: 'deezer',
    name: 'Deezer',
    colour: Color(0xFFA238FF),
    icon: Icons.music_note,
  ),
  StreamingPlatform(
    id: 'tidal',
    name: 'Tidal',
    colour: Color(0xFFFFFFFF),
    icon: SimpleIcons.tidal,
  ),
  StreamingPlatform(
    id: 'soundcloud',
    name: 'SoundCloud',
    colour: Color(0xFFFF5500),
    icon: SimpleIcons.soundcloud,
  ),
  StreamingPlatform(
    id: 'amazonMusic',
    name: 'Amazon',
    colour: Color(0xFF25D1DA),
    icon: SimpleIcons.amazonmusic,
  ),
  StreamingPlatform(
    id: 'audiomack',
    name: 'Audiomack',
    colour: Color(0xFFFFA200),
    icon: SimpleIcons.audiomack,
  ),
  StreamingPlatform(
    id: 'pandora',
    name: 'Pandora',
    colour: Color(0xFF224099),
    icon: SimpleIcons.pandora,
  ),
];

StreamingPlatform? findPlatform(String id) {
  for (final p in platforms) {
    if (p.id == id) return p;
  }
  return null;
}
