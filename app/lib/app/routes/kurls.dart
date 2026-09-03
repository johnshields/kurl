import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:kurl/models/kurl_history_item.dart';
import 'package:kurl/models/platform.dart';
import 'package:kurl/services/auth_service.dart';

class KurlsScreen extends StatefulWidget {
  const KurlsScreen({super.key});

  @override
  State<KurlsScreen> createState() => _KurlsScreenState();
}

class _KurlsScreenState extends State<KurlsScreen> {
  bool _loading = true;
  bool _loggedIn = false;
  List<KurlHistoryItem> _kurls = [];

  @override
  void initState() {
    super.initState();
    _load();
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
                    : _KurlsList(kurls: _kurls),
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

  const _KurlsList({required this.kurls});

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
                  _KurlTile(kurl: kurl),
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

  const _KurlTile({required this.kurl});

  @override
  Widget build(BuildContext context) {
    final platform = findPlatform(kurl.platform);

    return Material(
      color: const Color(0xFF141414),
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: () => launchUrl(Uri.parse(kurl.targetUrl)),
        borderRadius: BorderRadius.circular(10),
        child: Container(
          clipBehavior: Clip.hardEdge,
          decoration: BoxDecoration(
            border: Border.all(color: const Color(0xFF333333)),
            borderRadius: BorderRadius.circular(10),
          ),
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Icon(
                platform?.icon ?? Icons.music_note,
                size: 20,
                color: platform?.colour ?? const Color(0xFF888888),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      kurl.title ?? kurl.targetUrl,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    if (kurl.artist != null)
                      Text(
                        kurl.artist!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12, color: Color(0xFF888888)),
                      ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, size: 18, color: Color(0xFF555555)),
            ],
          ),
        ),
      ),
    );
  }
}
