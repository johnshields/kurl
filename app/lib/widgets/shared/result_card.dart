import 'dart:developer' as developer;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:kurl/models/platform.dart';
import 'package:kurl/models/kurl_result.dart';
import 'package:kurl/services/analytics_service.dart';
import 'package:kurl/utils/date_format.dart';
import 'package:kurl/widgets/shared/marquee_text.dart';
import 'package:kurl/widgets/shared/tappable.dart';

class ResultCard extends StatelessWidget {
  final KurlResult result;
  final VoidCallback? onDelete;
  final VoidCallback? onSend;

  const ResultCard({super.key, required this.result, this.onDelete, this.onSend});

  Future<void> _share(BuildContext context) async {
    try {
      final res = await Share.shareUri(Uri.parse(result.resolvedUrl));
      developer.log('share status=${res.status}', name: 'kurl.share');
    } catch (e, st) {
      developer.log('share failed: $e', name: 'kurl.share', error: e, stackTrace: st);
      if (context.mounted) _copy(context);
    }
  }

  Future<void> _shareOptions(BuildContext context) async {
    final send = await showModalBottomSheet<bool>(
      context: context,
      backgroundColor: const Color(0xFF141414),
      constraints: const BoxConstraints(maxWidth: 480),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(10)),
        side: BorderSide(color: Color(0xFF333333)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _ShareOption(
                icon: Icons.send_rounded,
                label: 'Send to a friend',
                onTap: () => Navigator.pop(ctx, true),
              ),
              const SizedBox(height: 4),
              _ShareOption(
                icon: Icons.ios_share,
                label: 'Share kurl',
                onTap: () => Navigator.pop(ctx, false),
              ),
            ],
          ),
        ),
      ),
    );
    if (send == null || !context.mounted) return;
    send ? onSend!() : _share(context);
  }

  void _copy(BuildContext context) {
    Clipboard.setData(ClipboardData(text: result.resolvedUrl));
    final width = MediaQuery.of(context).size.width;
    final horizontal = ((width - 200) / 2).clamp(16.0, double.infinity);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.check, size: 16, color: Color(0xFF1DB954)),
            SizedBox(width: 8),
            Text('Link copied'),
          ],
        ),
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
        margin: EdgeInsets.only(bottom: 80, left: horizontal, right: horizontal),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final platform = findPlatform(result.platform);
    final colour = platform?.colour ?? const Color(0xFFE5E5E5);
    const onColour = Colors.black;
    final date = shortDate(result.createdAt);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF141414),
        border: Border.all(color: const Color(0xFF333333)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (result.artworkUrl != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Center(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: Image.network(
                    result.artworkUrl!,
                    width: 120,
                    height: 120,
                    fit: BoxFit.cover,
                    errorBuilder: (a, b, c) => const SizedBox(width: 120, height: 120),
                  ),
                ),
              ),
            ),
          if (result.artist != null || result.title != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Row(
                children: [
                  Expanded(
                    child: MarqueeText(
                      key: ValueKey('${result.artist}|${result.title}'),
                      child: Text.rich(
                        TextSpan(children: [
                          if (result.artist != null)
                            TextSpan(
                              text: result.artist,
                              style: const TextStyle(color: Color(0xFF888888), fontSize: 14),
                            ),
                          if (result.artist != null && result.title != null)
                            const TextSpan(
                              text: ' - ',
                              style: TextStyle(color: Color(0xFF888888), fontSize: 14),
                            ),
                          if (result.title != null)
                            TextSpan(
                              text: result.title,
                              style: const TextStyle(
                                color: Color(0xFFE5E5E5),
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                        ]),
                        maxLines: 1,
                        softWrap: false,
                        overflow: TextOverflow.visible,
                      ),
                    ),
                  ),
                  if (date != null) ...[
                    const SizedBox(width: 8),
                    Text(date, style: const TextStyle(color: Color(0xFF888888), fontSize: 12)),
                  ],
                ],
              ),
            ),
          Row(
            children: [
              Expanded(
                child: _ActionButton(
                  icon: platform?.icon,
                  label: 'Share',
                  background: colour,
                  foreground: onColour,
                  onTap: () => onSend == null ? _share(context) : _shareOptions(context),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _ActionButton(
                  icon: Icons.headphones,
                  label: 'Listen',
                  background: const Color(0xFF222222),
                  foreground: const Color(0xFFE5E5E5),
                  onTap: () {
                    Analytics.trackOpenResult(result.platform);
                    launchUrl(Uri.parse(result.resolvedUrl));
                  },
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _ActionButton(
                  icon: Icons.copy,
                  label: 'Copy',
                  background: const Color(0xFF222222),
                  foreground: const Color(0xFFE5E5E5),
                  onTap: () => _copy(context),
                ),
              ),
              if (onDelete != null) ...[
                const SizedBox(width: 8),
                _IconAction(icon: Icons.delete_outline_rounded, onTap: onDelete!),
              ],
            ],
          ),
          if (result.isSearch)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                "Approx match on ${platform?.name ?? result.platform}",
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFF888888), fontSize: 11),
              ),
            ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData? icon;
  final String label;
  final Color background;
  final Color foreground;
  final VoidCallback onTap;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.background,
    required this.foreground,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Tappable(
      color: background,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
      onTap: onTap,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 18, color: foreground),
            const SizedBox(width: 6),
          ],
          Flexible(
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(
                label,
                maxLines: 1,
                softWrap: false,
                style: TextStyle(color: foreground, fontSize: 14, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ShareOption extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _ShareOption({required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Tappable(
      color: Colors.transparent,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      onTap: onTap,
      child: Row(
        children: [
          Icon(icon, size: 18, color: const Color(0xFFE5E5E5)),
          const SizedBox(width: 12),
          Text(label, style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 14)),
        ],
      ),
    );
  }
}

class _IconAction extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _IconAction({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Tappable(
      color: const Color(0xFF222222),
      padding: const EdgeInsets.all(12),
      onTap: onTap,
      child: Icon(icon, size: 18, color: const Color(0xFFE5E5E5)),
    );
  }
}
