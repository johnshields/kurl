import 'package:flutter/material.dart';
import 'package:kurl/app/routes/settings/settings_style.dart';
import 'package:kurl/models/friend.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/social_service.dart';
import 'package:kurl/utils/friendly_error.dart';

class FriendsScreen extends StatefulWidget {
  const FriendsScreen({super.key});

  @override
  State<FriendsScreen> createState() => _FriendsScreenState();
}

class _FriendsScreenState extends State<FriendsScreen> {
  final _usernameController = TextEditingController();
  bool _loading = true;
  bool _adding = false;
  String? _addError;
  FriendsOverview _overview = FriendsOverview.empty;
  final Set<String> _busy = {}; // friendship uids with an accept/remove in flight

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _usernameController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final overview = await SocialService.friends();
      if (mounted) setState(() => _overview = overview);
    } catch (_) {
      // Leave the last-known overview in place; the add form still works.
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _add() async {
    final username = _usernameController.text.trim();
    if (username.isEmpty || _adding) return;

    setState(() {
      _adding = true;
      _addError = null;
    });
    try {
      await SocialService.sendFriendRequest(username);
      _usernameController.clear();
      await _load();
      if (mounted) showToast(context, 'Friend request sent');
    } catch (e) {
      if (mounted) {
        setState(() => _addError = e is ApiException ? e.message : friendlyError(e));
      }
    } finally {
      if (mounted) setState(() => _adding = false);
    }
  }

  Future<void> _run(String friendUid, Future<void> Function() action) async {
    setState(() => _busy.add(friendUid));
    try {
      await action();
      await _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e is ApiException ? e.message : friendlyError(e)),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _busy.remove(friendUid));
    }
  }

  Future<void> _confirmUnfriend(Friend friend) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF141414),
        title: Text(
          'Remove ${friend.user.username}?',
          style: const TextStyle(color: Color(0xFFE5E5E5)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Remove', style: TextStyle(color: errorRed)),
          ),
        ],
      ),
    );
    if (confirmed == true) {
      await _run(friend.uid, () => SocialService.removeFriend(friend.uid));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0A),
        title: const Text('friends', style: TextStyle(color: Color(0xFFE5E5E5), fontSize: 16)),
        iconTheme: const IconThemeData(color: Color(0xFFE5E5E5)),
        elevation: 0,
      ),
      body: SafeArea(
        child: _loading
            ? const Center(
                child: CircularProgressIndicator(color: Color(0xFF555555), strokeWidth: 2),
              )
            : SingleChildScrollView(
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(24, 24, 24, 100),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _addForm(),
                          if (_overview.incoming.isNotEmpty) ...[
                            const SizedBox(height: 28),
                            _section('Requests', _overview.incoming, _incomingRow),
                          ],
                          if (_overview.outgoing.isNotEmpty) ...[
                            const SizedBox(height: 28),
                            _section('Pending', _overview.outgoing, _outgoingRow),
                          ],
                          const SizedBox(height: 28),
                          _overview.friends.isEmpty
                              ? const Text(
                                  'No friends yet. Add someone by their username above.',
                                  style: TextStyle(color: Color(0xFF888888), fontSize: 13),
                                )
                              : _section('Friends', _overview.friends, _friendRow),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
      ),
    );
  }

  Widget _addForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Add a friend',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _usernameController,
                enabled: !_adding,
                onSubmitted: (_) => _add(),
                style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                decoration: darkInputDecoration('Username'),
              ),
            ),
            const SizedBox(width: 8),
            Material(
              color: const Color(0xFFE5E5E5),
              borderRadius: BorderRadius.circular(8),
              child: InkWell(
                onTap: _adding ? null : _add,
                borderRadius: BorderRadius.circular(8),
                child: const Padding(
                  padding: EdgeInsets.all(12),
                  child: Icon(Icons.person_add_alt_1, size: 18, color: Color(0xFF0A0A0A)),
                ),
              ),
            ),
          ],
        ),
        if (_addError != null) ...[
          const SizedBox(height: 8),
          Text(_addError!, style: const TextStyle(color: errorRed, fontSize: 12)),
        ],
      ],
    );
  }

  Widget _section(String title, List<Friend> friends, Widget Function(Friend) rowBuilder) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
        ),
        const SizedBox(height: 8),
        for (final friend in friends) ...[rowBuilder(friend), const SizedBox(height: 8)],
      ],
    );
  }

  Widget _incomingRow(Friend friend) {
    return _FriendRow(
      username: friend.user.username,
      busy: _busy.contains(friend.uid),
      trailing: [
        _actionIcon(
          Icons.check_rounded,
          const Color(0xFF1DB954),
          () => _run(friend.uid, () => SocialService.acceptFriendRequest(friend.uid)),
        ),
        _actionIcon(
          Icons.close_rounded,
          errorRed,
          () => _run(friend.uid, () => SocialService.removeFriend(friend.uid)),
        ),
      ],
    );
  }

  Widget _outgoingRow(Friend friend) {
    return _FriendRow(
      username: friend.user.username,
      busy: _busy.contains(friend.uid),
      trailing: [
        TextButton(
          onPressed: _busy.contains(friend.uid)
              ? null
              : () => _run(friend.uid, () => SocialService.removeFriend(friend.uid)),
          style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 0)),
          child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888), fontSize: 13)),
        ),
      ],
    );
  }

  Widget _friendRow(Friend friend) {
    return _FriendRow(
      username: friend.user.username,
      busy: _busy.contains(friend.uid),
      trailing: [
        _actionIcon(Icons.person_remove_alt_1, const Color(0xFF888888), () => _confirmUnfriend(friend)),
      ],
    );
  }

  Widget _actionIcon(IconData icon, Color colour, VoidCallback onTap) {
    return IconButton(
      onPressed: onTap,
      icon: Icon(icon, size: 18),
      color: colour,
      visualDensity: VisualDensity.compact,
    );
  }
}

class _FriendRow extends StatelessWidget {
  final String username;
  final bool busy;
  final List<Widget> trailing;

  const _FriendRow({required this.username, required this.busy, required this.trailing});

  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: busy ? 0.5 : 1,
      child: Container(
        padding: const EdgeInsets.fromLTRB(14, 6, 6, 6),
        decoration: BoxDecoration(
          color: const Color(0xFF141414),
          border: Border.all(color: const Color(0xFF333333)),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                username,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 14),
              ),
            ),
            ...trailing,
          ],
        ),
      ),
    );
  }
}
