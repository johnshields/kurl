import 'package:flutter/material.dart';
import 'package:kurl/app/routes/kurl.dart';
import 'package:kurl/app/routes/kurls.dart';
import 'package:kurl/app/routes/messages.dart';
import 'package:kurl/app/routes/settings.dart';
import 'package:kurl/utils/tab_url.dart';
import 'package:kurl/widgets/shared/floating_nav_bar.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

typedef _TabEntry = ({IconData icon, String label, Widget screen, String path});

class _MainShellState extends State<MainShell> {
  final _kurlsKey = GlobalKey<KurlsScreenState>();
  final _messagesKey = GlobalKey<MessagesScreenState>();
  int _messagesUnread = 0;

  late int _selectedIndex = _tabs.indexWhere((t) => t.path == currentTabPath()).clamp(0, _tabs.length - 1);

  late final _tabs = <_TabEntry>[
    (icon: Icons.home_rounded, label: 'home', screen: const KurlScreen(), path: '/'),
    (icon: Icons.link_rounded, label: 'kurls', screen: KurlsScreen(key: _kurlsKey), path: '/kurls'),
    (
      icon: Icons.forum_rounded,
      label: 'messages',
      screen: MessagesScreen(
        key: _messagesKey,
        onUnread: (n) => setState(() => _messagesUnread = n),
      ),
      path: '/messages',
    ),
    (icon: Icons.settings_rounded, label: 'settings', screen: const SettingsScreen(), path: '/settings'),
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
                  tabs: [
                    for (final entry in _tabs)
                      NavTab(
                        icon: entry.icon,
                        label: entry.label,
                        badgeCount: entry.path == '/messages' ? _messagesUnread : 0,
                      ),
                  ],
                  selectedIndex: _selectedIndex,
                  onSelect: (i) => setState(() {
                    _selectedIndex = i;
                    updateTabPath(_tabs[i].path);
                    if (_tabs[i].path == '/kurls') _kurlsKey.currentState?.refresh();
                    if (_tabs[i].path == '/messages') _messagesKey.currentState?.refresh();
                  }),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
