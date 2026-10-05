import 'package:flutter/material.dart';

class Tappable extends StatelessWidget {
  final Color color;
  final EdgeInsets padding;
  final VoidCallback? onTap;
  final Widget child;

  const Tappable({super.key, required this.color, required this.padding, required this.onTap, required this.child});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}
