import 'package:flutter/material.dart';
import 'package:kurl/app/routes/kurl.dart';
import 'package:kurl/app/routes/kurls.dart';
import 'package:kurl/app/routes/settings.dart';
import 'package:kurl/widgets/shared/floating_nav_bar.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

typedef _TabEntry = ({NavTab tab, Widget screen});

class _MainShellState extends State<MainShell> {
  int _selectedIndex = 0;

  static const _tabs = <_TabEntry>[
    (tab: NavTab(icon: Icons.home_rounded, label: 'Home'), screen: KurlScreen()),
    (tab: NavTab(icon: Icons.link_rounded, label: 'Kurls'), screen: KurlsScreen()),
    (tab: NavTab(icon: Icons.settings_rounded, label: 'Settings'), screen: SettingsScreen()),
  ];

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.paddingOf(context).bottom;

    return Scaffold(
      body: Stack(
        // expand: loose Stacks size to content, leaving the nav unclickable below it.
        fit: StackFit.expand,
        children: [
          IndexedStack(
            index: _selectedIndex,
            children: [for (final entry in _tabs) entry.screen],
          ),
          Positioned.fill(
            child: Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: EdgeInsets.only(bottom: bottomInset + 16),
                child: FloatingNavBar(
                  tabs: [for (final entry in _tabs) entry.tab],
                  selectedIndex: _selectedIndex,
                  onSelect: (i) => setState(() => _selectedIndex = i),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
