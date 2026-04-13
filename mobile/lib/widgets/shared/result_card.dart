import 'dart:developer' as developer;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:kurl/models/platform.dart';
import 'package:kurl/models/kurl_result.dart';

class ResultCard extends StatelessWidget {
  final KurlResult result;

  const ResultCard({super.key, required this.result});

  Future<void> _share(BuildContext context) async {
    try {
      final res = await Share.shareUri(Uri.parse(result.resolvedUrl));
      developer.log('share status=${res.status}', name: 'kurl.share');
    } catch (e, st) {
      developer.log('share failed: $e', name: 'kurl.share', error: e, stackTrace: st);
      if (context.mounted) _copy(context);
    }
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
          if (result.artist != null || result.title != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text.rich(
                TextSpan(children: [
                  if (result.artist != null)
                    TextSpan(
                      text: result.artist,
                      style: const TextStyle(color: Color(0xFF888888), fontSize: 14),
                    ),
                  if (result.artist != null && result.title != null)
                    const TextSpan(
                      text: ' — ',
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
              ),
            ),
          Row(
            children: [
              Expanded(
                child: Material(
                  color: colour,
                  borderRadius: BorderRadius.circular(8),
                  child: InkWell(
                    onTap: () => _share(context),
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (platform != null) ...[
                            Icon(platform.icon, size: 18, color: onColour),
                            const SizedBox(width: 8),
                          ],
                          Text(
                            'Share ${platform?.name ?? result.platform} link',
                            style: TextStyle(
                              color: onColour,
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Material(
                color: const Color(0xFF222222),
                borderRadius: BorderRadius.circular(8),
                child: InkWell(
                  onTap: () => launchUrl(Uri.parse(result.resolvedUrl)),
                  borderRadius: BorderRadius.circular(8),
                  child: const Padding(
                    padding: EdgeInsets.all(12),
                    child: Icon(Icons.visibility_outlined, size: 18, color: Color(0xFFE5E5E5)),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Material(
                color: const Color(0xFF222222),
                borderRadius: BorderRadius.circular(8),
                child: InkWell(
                  onTap: () => _copy(context),
                  borderRadius: BorderRadius.circular(8),
                  child: const Padding(
                    padding: EdgeInsets.all(12),
                    child: Icon(Icons.copy, size: 18, color: Color(0xFFE5E5E5)),
                  ),
                ),
              ),
            ],
          ),
          if (result.isSearch)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text(
                "No exact match — this is a search on the target platform",
                style: TextStyle(color: Color(0xFF888888), fontSize: 11),
              ),
            ),
          if (result.cached)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Align(
                alignment: Alignment.centerRight,
                child: Text(
                  'cached',
                  style: TextStyle(color: Color(0xFF555555), fontSize: 11),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
