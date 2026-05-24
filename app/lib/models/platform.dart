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
  // Row 1: mainstream
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
  // Row 2: indie / UGC / DJ
  StreamingPlatform(
    id: 'soundcloud',
    name: 'SoundCloud',
    colour: Color(0xFFFF5500),
    icon: SimpleIcons.soundcloud,
  ),
  StreamingPlatform(
    id: 'beatport',
    name: 'Beatport',
    colour: Color(0xFF01FF95),
    icon: SimpleIcons.beatport,
  ),
  StreamingPlatform(
    id: 'bandcamp',
    name: 'Bandcamp',
    colour: Color(0xFF629AA9),
    icon: SimpleIcons.bandcamp,
  ),
  // Row 3: long tail
  StreamingPlatform(
    id: 'amazonMusic',
    name: 'Amazon',
    colour: Color(0xFF25D1DA),
    icon: SimpleIcons.amazonmusic,
  ),
  StreamingPlatform(
    id: 'tidal',
    name: 'Tidal',
    colour: Color(0xFFFFFFFF),
    icon: SimpleIcons.tidal,
  ),
  StreamingPlatform(
    id: 'deezer',
    name: 'Deezer',
    colour: Color(0xFFA238FF),
    icon: Icons.music_note,
  ),
];

StreamingPlatform? findPlatform(String id) {
  for (final p in platforms) {
    if (p.id == id) return p;
  }
  return null;
}
