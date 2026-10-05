import 'package:flutter/material.dart';
import 'package:kurl/app/layout.dart';
import 'package:kurl/app/routes/settings/settings_style.dart';
import 'package:kurl/app/routes/thread.dart';
import 'package:kurl/models/friend.dart';
import 'package:kurl/models/kurl_result.dart';
import 'package:kurl/models/message.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/social_service.dart';
import 'package:kurl/utils/friendly_error.dart';
import 'package:kurl/utils/initial.dart';
import 'package:kurl/widgets/shared/tappable.dart';

/// Opens the send dialog, then the new thread once the kurl is sent.
Future<void> kurlToFriend(BuildContext context, KurlResult kurl, String sourceUrl) async {
  final sent = await showDialog<Message>(
    context: context,
    builder: (_) => _SendKurlSheet(kurl: kurl, sourceUrl: sourceUrl),
  );
  if (sent != null && context.mounted) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ThreadScreen(threadUid: sent.threadUid)),
    );
  }
}

/// Pick a friend, add an optional note, and send [kurl] to them as a message.
/// Pops with the created [Message] on success, null on cancel.
class _SendKurlSheet extends StatefulWidget {
  final KurlResult kurl;
  final String sourceUrl;

  const _SendKurlSheet({required this.kurl, required this.sourceUrl});

  @override
  State<_SendKurlSheet> createState() => _SendKurlSheetState();
}

class _SendKurlSheetState extends State<_SendKurlSheet> {
  final _noteController = TextEditingController();
  bool _loading = true;
  bool _sending = false;
  List<Friend> _friends = const [];
  Friend? _selected;
  String? _error;

  String? get _kurlLabel {
    final parts = [widget.kurl.artist, widget.kurl.title].whereType<String>();
    return parts.isEmpty ? null : parts.join(' - ');
  }

  @override
  void initState() {
    super.initState();
    _loadFriends();
  }

  Future<void> _loadFriends() async {
    try {
      final overview = await SocialService.friends();
      if (mounted) setState(() => _friends = overview.friends);
    } catch (e) {
      if (mounted) setState(() => _error = friendlyError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _send() async {
    final selected = _selected;
    if (selected == null) return;

    setState(() {
      _sending = true;
      _error = null;
    });
    final note = _noteController.text.trim();
    try {
      final message = await SocialService.sendMessage(
        toUid: selected.user.uid,
        body: note.isEmpty ? null : note,
        kurl: {'source_url': widget.sourceUrl, ...widget.kurl.toJson()},
      );
      if (mounted) Navigator.of(context).pop(message);
    } catch (e) {
      if (mounted) {
        setState(() => _error = e is ApiException ? e.message : friendlyError(e));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final label = _kurlLabel;
    return AlertDialog(
      backgroundColor: const Color(0xFF141414),
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Kurl to a friend', style: TextStyle(color: Color(0xFFE5E5E5))),
          if (label != null) ...[
            const SizedBox(height: 4),
            Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Color(0xFF888888), fontSize: 12, fontWeight: FontWeight.normal),
            ),
          ],
        ],
      ),
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      constraints: const BoxConstraints(maxWidth: kContentMaxWidth - 48),
      content: SizedBox(
        width: double.maxFinite,
        child: _loading
          ? const SizedBox(
              height: 48,
              child: Center(
                child: CircularProgressIndicator(color: Color(0xFF555555), strokeWidth: 2),
              ),
            )
          : _friends.isEmpty
              ? const Text(
                  'Add a friend first (Messages > Friends), then you can send them kurls.',
                  style: TextStyle(color: Color(0xFF888888), fontSize: 13),
                )
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    ConstrainedBox(
                      constraints: const BoxConstraints(maxHeight: 240),
                      child: SingleChildScrollView(
                        child: Column(
                          children: [
                            for (final friend in _friends) ...[
                              _FriendOption(
                                username: friend.user.username,
                                selected: friend.uid == _selected?.uid,
                                onTap: _sending ? null : () => setState(() => _selected = friend),
                              ),
                              const SizedBox(height: 6),
                            ],
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _noteController,
                      enabled: !_sending,
                      maxLength: 280,
                      style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                      decoration: darkInputDecoration('Add a note (optional)', dialog: true),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 8),
                      Text(_error!, style: const TextStyle(color: errorRed, fontSize: 12)),
                    ],
                  ],
                ),
      ),
      actions: [
        TextButton(
          onPressed: _sending ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
        ),
        if (_friends.isNotEmpty)
          FilledButton.icon(
            onPressed: (_sending || _selected == null) ? null : _send,
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFFE5E5E5),
              foregroundColor: Colors.black,
              disabledBackgroundColor: const Color(0xFF222222),
              disabledForegroundColor: const Color(0xFF555555),
            ),
            icon: const Icon(Icons.send_rounded, size: 16),
            label: Text(_sending ? 'Sending...' : 'Send'),
          ),
      ],
    );
  }
}

class _FriendOption extends StatelessWidget {
  final String username;
  final bool selected;
  final VoidCallback? onTap;

  const _FriendOption({required this.username, required this.selected, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Tappable(
      color: selected ? const Color(0xFF1F1F1F) : Colors.transparent,
      borderColor: selected ? const Color(0xFF888888) : const Color(0xFF2A2A2A),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      onTap: onTap,
      child: Row(
        children: [
          CircleAvatar(
            radius: 14,
            backgroundColor: const Color(0xFF222222),
            child: Text(
              initialOf(username),
              style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              username,
              style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 14),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (selected) const Icon(Icons.check_circle, size: 18, color: Color(0xFFE5E5E5)),
        ],
      ),
    );
  }
}
