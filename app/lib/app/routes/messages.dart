import 'package:flutter/material.dart';
import 'package:kurl/app/layout.dart';
import 'package:kurl/app/routes/thread.dart';
import 'package:kurl/models/thread.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/services/social_service.dart';
import 'package:kurl/utils/date_format.dart';
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

  @override
  void initState() {
    super.initState();
    _load();
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
      final threads = await SocialService.threads();
      if (mounted) {
        setState(() {
          _loggedIn = true;
          _threads = threads;
          _loading = false;
        });
      }
      widget.onUnread?.call(threads.fold(0, (sum, t) => sum + t.unread));
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
                    : _ThreadList(threads: _threads, onOpen: _open),
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
  final ValueChanged<MessageThread> onOpen;

  const _ThreadList({required this.threads, required this.onOpen});

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
                const Text(
                  'messages',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFE5E5E5),
                    letterSpacing: -0.5,
                  ),
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
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                      constraints: const BoxConstraints(minWidth: 18),
                      decoration: BoxDecoration(
                        color: const Color(0xFFEF4444),
                        borderRadius: BorderRadius.circular(9),
                      ),
                      child: Text(
                        unread > 99 ? '99+' : '$unread',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
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
