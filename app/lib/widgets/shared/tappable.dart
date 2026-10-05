import 'package:flutter/material.dart';

class Tappable extends StatelessWidget {
  static const _radius = BorderRadius.all(Radius.circular(8));

  final Color color;
  final Color? borderColor;
  final EdgeInsets padding;
  final VoidCallback? onTap;
  final Widget child;

  const Tappable({
    super.key,
    this.color = Colors.transparent,
    this.borderColor,
    this.padding = EdgeInsets.zero,
    required this.onTap,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      shape: RoundedRectangleBorder(
        borderRadius: _radius,
        side: borderColor == null ? BorderSide.none : BorderSide(color: borderColor!),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: _radius,
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}
