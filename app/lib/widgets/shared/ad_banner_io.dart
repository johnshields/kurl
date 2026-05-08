import 'package:flutter/widgets.dart';

// Native stub -- AdSense is web only. Mobile uses google_mobile_ads (TODO).
class AdBanner extends StatelessWidget {
  final String slot;
  final double height;

  const AdBanner({super.key, required this.slot, this.height = 90});

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
