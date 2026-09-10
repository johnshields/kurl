import 'package:flutter/material.dart';
import 'package:kurl/app/routes/settings/settings_style.dart';
import 'package:kurl/models/friend.dart';
import 'package:kurl/models/kurl_result.dart';
import 'package:kurl/models/message.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/social_service.dart';
import 'package:kurl/utils/friendly_error.dart';

/// Pick a friend, add an optional note, and send [kurl] to them as a message.
/// Pops with the created [Message] on success, null on cancel.
class SendKurlSheet extends StatefulWidget {
  final KurlResult kurl;
  final String sourceUrl;

  const SendKurlSheet({super.key, required this.kurl, required this.sourceUrl});

  @override
  State<SendKurlSheet> createState() => _SendKurlSheetState();
}

class _SendKurlSheetState extends State<SendKurlSheet> {
  final _noteController = TextEditingController();
  bool _loading = true;
  bool _sending = false;
  List<Friend> _friends = const [];
  Friend? _selected;
  String? _error;

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
    return AlertDialog(
      backgroundColor: const Color(0xFF141414),
      title: const Text('Send to a friend', style: TextStyle(color: Color(0xFFE5E5E5))),
      content: _loading
          ? const SizedBox(
              height: 48,
              child: Center(
                child: CircularProgressIndicator(color: Color(0xFF555555), strokeWidth: 2),
              ),
            )
          : _friends.isEmpty
              ? const Text(
                  'Add a friend first, then you can send them kurls.',
                  style: TextStyle(color: Color(0xFF888888), fontSize: 13),
                )
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    ConstrainedBox(
                      constraints: const BoxConstraints(maxHeight: 180),
                      child: SingleChildScrollView(
                        child: Column(
                          children: [
                            for (final friend in _friends)
                              _FriendOption(
                                username: friend.user.username,
                                selected: friend.uid == _selected?.uid,
                                onTap: _sending ? null : () => setState(() => _selected = friend),
                              ),
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
      actions: [
        TextButton(
          onPressed: _sending ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
        ),
        if (_friends.isNotEmpty)
          TextButton(
            onPressed: (_sending || _selected == null) ? null : _send,
            child: Text(_sending ? 'Sending...' : 'Send'),
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
    return Material(
      color: selected ? const Color(0xFF1F1F1F) : Colors.transparent,
      borderRadius: BorderRadius.circular(8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            children: [
              Icon(
                selected ? Icons.check_circle : Icons.circle_outlined,
                size: 16,
                color: selected ? const Color(0xFFE5E5E5) : const Color(0xFF555555),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  username,
                  style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 14),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
