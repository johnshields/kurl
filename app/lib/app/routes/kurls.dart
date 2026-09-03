import 'package:flutter/material.dart';
import 'package:kurl/models/kurl_history_item.dart';
import 'package:kurl/models/kurl_result.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/widgets/shared/result_card.dart';

const _errorRed = Color(0xFFEF4444);

class KurlsScreen extends StatefulWidget {
  const KurlsScreen({super.key});

  @override
  State<KurlsScreen> createState() => KurlsScreenState();
}

class KurlsScreenState extends State<KurlsScreen> {
  bool _loading = true;
  bool _loggedIn = false;
  List<KurlHistoryItem> _kurls = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  // Called by MainShell when this tab becomes active -- IndexedStack keeps
  // the screen mounted, so initState alone would only ever load it once.
  Future<void> refresh() => _load();

  Future<void> _delete(String uid) async {
    final previous = _kurls;
    setState(() => _kurls = _kurls.where((k) => k.uid != uid).toList());
    try {
      await AuthService.deleteKurl(uid);
    } catch (_) {
      // Delete failed -- restore the tile rather than leaving it silently gone.
      if (mounted) setState(() => _kurls = previous);
    }
  }

  Future<void> _load() async {
    final loggedIn = await AuthService.isLoggedIn();
    if (!loggedIn) {
      if (mounted) {
        setState(() {
          _loggedIn = false;
          _loading = false;
        });
      }
      return;
    }

    final kurls = await AuthService.getKurls();
    if (mounted) {
      setState(() {
        _loggedIn = true;
        _kurls = kurls;
        _loading = false;
      });
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
                ? const _EmptyState(
                    icon: Icons.lock_outline_rounded,
                    title: 'Sign in to see your kurls',
                    subtitle: 'Head to Settings to create an account.',
                  )
                : _kurls.isEmpty
                    ? const _EmptyState(
                        icon: Icons.link_rounded,
                        title: 'No kurls yet',
                        subtitle: 'Kurl something and it will show up here.',
                      )
                    : _KurlsList(kurls: _kurls, onDelete: _delete),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const _EmptyState({required this.icon, required this.title, required this.subtitle});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 40, color: const Color(0xFF555555)),
          const SizedBox(height: 12),
          Text(
            title,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Color(0xFFE5E5E5),
              letterSpacing: -0.5,
            ),
          ),
          const SizedBox(height: 4),
          Text(subtitle, style: const TextStyle(fontSize: 13, color: Color(0xFF888888))),
        ],
      ),
    );
  }
}

class _KurlsList extends StatelessWidget {
  final List<KurlHistoryItem> kurls;
  final ValueChanged<String> onDelete;

  const _KurlsList({required this.kurls, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 48, 24, 100),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Kurls',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFE5E5E5),
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 20),
                for (final kurl in kurls) ...[
                  _KurlTile(kurl: kurl, onDelete: () => onDelete(kurl.uid)),
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

class _KurlTile extends StatelessWidget {
  final KurlHistoryItem kurl;
  final VoidCallback onDelete;

  const _KurlTile({required this.kurl, required this.onDelete});

  Future<void> _confirmDelete(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF141414),
        title: const Text('Delete kurl?', style: TextStyle(color: Color(0xFFE5E5E5))),
        content: Text(
          kurl.title ?? kurl.targetUrl,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(color: Color(0xFF888888)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Delete', style: TextStyle(color: _errorRed)),
          ),
        ],
      ),
    );
    if (confirmed == true) onDelete();
  }

  @override
  Widget build(BuildContext context) {
    return ResultCard(
      result: KurlResult(
        title: kurl.title,
        artist: kurl.artist,
        resolvedUrl: kurl.targetUrl,
        platform: kurl.platform,
        via: kurl.via,
      ),
      onDelete: () => _confirmDelete(context),
    );
  }
}
