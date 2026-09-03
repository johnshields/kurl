import 'package:flutter/material.dart';
import 'package:kurl/widgets/shared/placeholder_screen.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const PlaceholderScreen(
      icon: Icons.settings_rounded,
      title: 'Settings',
      subtitle: 'Coming soon',
    );
  }
}
