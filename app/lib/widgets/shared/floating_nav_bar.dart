import 'package:flutter/material.dart';

class NavTab {
  final IconData icon;
  final String label;

  const NavTab({required this.icon, required this.label});
}

class FloatingNavBar extends StatelessWidget {
  final List<NavTab> tabs;
  final int selectedIndex;
  final ValueChanged<int> onSelect;

  const FloatingNavBar({
    super.key,
    required this.tabs,
    required this.selectedIndex,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFF141414),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFF333333)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.4),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(tabs.length, (i) {
          final tab = tabs[i];
          final isSelected = i == selectedIndex;
          final colour = isSelected ? const Color(0xFFE5E5E5) : const Color(0xFF888888);
          return Material(
            color: isSelected ? const Color(0xFF1F1F1F) : Colors.transparent,
            borderRadius: BorderRadius.circular(18),
            child: InkWell(
              onTap: () => onSelect(i),
              borderRadius: BorderRadius.circular(18),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(tab.icon, size: 22, color: colour),
                    const SizedBox(height: 3),
                    Text(
                      tab.label,
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                        color: colour,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}
