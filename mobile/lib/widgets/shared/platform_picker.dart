import 'package:flutter/material.dart';
import 'package:kurl/models/platform.dart';

class PlatformPicker extends StatelessWidget {
  final String? selected;
  final ValueChanged<String> onSelect;
  final bool disabled;

  const PlatformPicker({
    super.key,
    required this.selected,
    required this.onSelect,
    this.disabled = false,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: platforms.map((p) {
        final isSelected = selected == p.id;
        return GestureDetector(
          onTap: disabled ? null : () => onSelect(p.id),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: isSelected ? p.colour : const Color(0xFF141414),
              border: Border.all(
                color: isSelected ? p.colour : const Color(0xFF333333),
              ),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              p.name,
              style: TextStyle(
                fontSize: 13,
                color: isSelected ? Colors.white : const Color(0xFFE5E5E5),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
