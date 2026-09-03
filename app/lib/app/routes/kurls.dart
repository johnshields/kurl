import 'package:flutter/material.dart';
import 'package:kurl/widgets/shared/placeholder_screen.dart';

class KurlsScreen extends StatelessWidget {
  const KurlsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const PlaceholderScreen(
      icon: Icons.link_rounded,
      title: 'Kurls',
      subtitle: 'Your kurl history will show up here',
    );
  }
}
