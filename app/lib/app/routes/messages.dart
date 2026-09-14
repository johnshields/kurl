import 'dart:async';

import 'package:flutter/material.dart';
import 'package:kurl/app/layout.dart';
import 'package:kurl/app/routes/settings/friends_view.dart';
import 'package:kurl/app/routes/thread.dart';
import 'package:kurl/models/thread.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/services/social_service.dart';
import 'package:kurl/utils/date_format.dart';
import 'package:kurl/widgets/shared/count_badge.dart';
import 'package:kurl/widgets/shared/empty_state.dart';

/// One-line preview for a thread row: the last message's text, or a note that
/// it carried a kurl, or a placeholder for an empty thread.
String threadPreview(MessageThread thread) {
  final last = thread.lastMessage;
  if (last == null) return 'No messages yet';
  final body = last.body;
  if (body != null && body.isNotEmpty) return body;
  final kurl = last.kurl;
  if (kurl != null) {
    final artist = kurl.artist;
    final title = kurl.title;
    if (artist != null && title != null) return '$artist - $title';
    return 'Sent a kurl';
  }
  return 'No messages yet';
}

class MessagesScreen extends StatefulWidget {
  final ValueChanged<int>? onUnread;

  const MessagesScreen({super.key, this.onUnread});

  @override
  State<MessagesScreen> createState() => MessagesScreenState();
}

class MessagesScreenState extends State<MessagesScreen> {
  bool _loading = true;
  bool _loggedIn = false;
  List<MessageThread> _threads = [];
  int _incomingRequests = 0;
  Timer? _poll;

  @override
  void initState() {
    super.initState();
    _load();
    _poll = Timer.periodic(const Duration(seconds: 5), (_) => _load());
  }

  @override
  void dispose() {
    _poll?.cancel();
    super.dispose();
  }

  // Called by MainShell when this tab becomes active -- IndexedStack keeps
  // the screen mounted, so initState alone would only ever load it once.
  Future<void> refresh() => _load();

  Future<void> _load() async {
    final loggedIn = await AuthService.isLoggedIn();
    if (!loggedIn) {
      widget.onUnread?.call(0);
      if (mounted) {
        setState(() {
          _loggedIn = false;
          _loading = false;
        });
      }
      return;
    }

    try {
      final (threads, friends) = await (SocialService.threads(), SocialService.friends()).wait;
      final incomingRequests = friends.incoming.length;
      if (mounted) {
        setState(() {
          _loggedIn = true;
          _threads = threads;
          _incomingRequests = incomingRequests;
          _loading = false;
        });
      }
      final unread = threads.fold(0, (sum, t) => sum + t.unread);
      widget.onUnread?.call(unread + incomingRequests);
    } catch (_) {
      if (mounted) {
        setState(() {
          _loggedIn = true;
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: _loading
            ? const Center(
                child: CircularProgressIndicator(color: Color(0xFF555555), strokeWidth: 2),
              )
            : !_loggedIn
                ? const EmptyState(
                    icon: Icons.lock_outline_rounded,
                    title: 'Sign in to see your messages',
                    subtitle: 'Head to Settings to create an account.',
                  )
                : _threads.isEmpty
                    ? const EmptyState(
                        icon: Icons.forum_outlined,
                        title: 'No messages yet',
                        subtitle: 'Send a kurl to a friend to start a thread.',
                      )
                    : _ThreadList(
                        threads: _threads,
                        incomingRequests: _incomingRequests,
                        onOpen: _open,
                      ),
      ),
    );
  }

  Future<void> _open(MessageThread thread) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ThreadScreen(threadUid: thread.uid, otherUsername: thread.user.username),
      ),
    );
    _load(); // unread count may have changed while the thread was open
  }
}

class _ThreadList extends StatelessWidget {
  final List<MessageThread> threads;
  final int incomingRequests;
  final ValueChanged<MessageThread> onOpen;

  const _ThreadList({required this.threads, required this.incomingRequests, required this.onOpen});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: kContentMaxWidth),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 48, 24, 100),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'messages',
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFE5E5E5),
                        letterSpacing: -0.5,
                      ),
                    ),
                    _FriendsButton(badgeCount: incomingRequests),
                  ],
                ),
                const SizedBox(height: 20),
                for (final thread in threads) ...[
                  _ThreadTile(thread: thread, onTap: () => onOpen(thread)),
                  const SizedBox(height: 8),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _FriendsButton extends StatelessWidget {
  final int badgeCount;

  const _FriendsButton({required this.badgeCount});

  @override
  Widget build(BuildContext context) {
    return TextButton.icon(
      onPressed: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => const FriendsScreen()),
      ),
      style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 0)),
      icon: Stack(
        clipBehavior: Clip.none,
        children: [
          const Icon(Icons.people_outline, size: 18, color: Color(0xFFE5E5E5)),
          if (badgeCount > 0)
            Positioned(
              right: -6,
              top: -4,
              child: CountBadge(count: badgeCount, compact: true),
            ),
        ],
      ),
      label: const Text('Friends', style: TextStyle(fontSize: 14, color: Color(0xFFE5E5E5))),
    );
  }
}

class _ThreadTile extends StatelessWidget {
  final MessageThread thread;
  final VoidCallback onTap;

  const _ThreadTile({required this.thread, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final unread = thread.unread;
    final date = shortDate(thread.lastMessageAt);

    return Material(
      color: const Color(0xFF141414),
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            border: Border.all(color: const Color(0xFF333333)),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      thread.user.username,
                      style: TextStyle(
                        color: const Color(0xFFE5E5E5),
                        fontSize: 14,
                        fontWeight: unread > 0 ? FontWeight.w700 : FontWeight.w600,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      threadPreview(thread),
                      style: const TextStyle(color: Color(0xFF888888), fontSize: 13),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (date != null)
                    Text(date, style: const TextStyle(color: Color(0xFF888888), fontSize: 12)),
                  if (unread > 0) ...[
                    const SizedBox(height: 6),
                    CountBadge(count: unread),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
