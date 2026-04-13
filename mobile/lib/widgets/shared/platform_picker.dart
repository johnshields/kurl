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
    return GridView.count(
      crossAxisCount: 3,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      childAspectRatio: 3.2,
      children: platforms.map((p) {
        final isSelected = selected == p.id;
        const onColour = Colors.black;
        return Opacity(
          opacity: disabled ? 0.5 : 1,
          child: Material(
            color: isSelected ? p.colour : const Color(0xFF141414),
            borderRadius: BorderRadius.circular(8),
            child: InkWell(
              onTap: disabled ? null : () => onSelect(p.id),
              borderRadius: BorderRadius.circular(8),
              child: Container(
                decoration: BoxDecoration(
                  border: Border.all(
                    color: isSelected ? p.colour : const Color(0xFF333333),
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      p.icon,
                      size: 16,
                      color: isSelected ? onColour : p.colour,
                    ),
                    const SizedBox(width: 6),
                    Flexible(
                      child: Text(
                        p.name,
                        overflow: TextOverflow.ellipsis,
                        softWrap: false,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: isSelected ? onColour : const Color(0xFFE5E5E5),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
