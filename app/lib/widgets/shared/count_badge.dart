import 'package:flutter/material.dart';

class CountBadge extends StatelessWidget {
  final int count;
  final bool compact;

  const CountBadge({super.key, required this.count, this.compact = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: compact ? 4 : 6, vertical: 1),
      constraints: BoxConstraints(minWidth: compact ? 14 : 18),
      decoration: BoxDecoration(
        color: const Color(0xFFEF4444),
        borderRadius: BorderRadius.circular(compact ? 8 : 9),
      ),
      child: Text(
        count > 99 ? '99+' : '$count',
        textAlign: TextAlign.center,
        style: TextStyle(color: Colors.white, fontSize: compact ? 9 : 10, fontWeight: FontWeight.w700),
      ),
    );
  }
}
