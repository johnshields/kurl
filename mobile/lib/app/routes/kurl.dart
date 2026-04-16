import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:kurl/models/kurl_result.dart';
import 'package:kurl/models/platform.dart';
import 'package:kurl/services/api_service.dart';
import 'package:kurl/utils/url_validator.dart';
import 'package:kurl/widgets/shared/platform_picker.dart';
import 'package:kurl/widgets/shared/result_card.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';

class KurlScreen extends StatefulWidget {
  const KurlScreen({super.key});

  @override
  State<KurlScreen> createState() => _KurlScreenState();
}

const _errorRed = Color(0xFFEF4444);
const _borderIdle = Color(0xFF333333);
const _borderFocused = Color(0xFF555555);
const _neutralBg = Color(0xFFE5E5E5);

class _KurlScreenState extends State<KurlScreen> with SingleTickerProviderStateMixin {
  final _urlController = TextEditingController();
  String? _selectedPlatform;
  KurlResult? _result;
  bool _loading = false;
  bool _pressed = false;
  String? _error;
  StreamSubscription<List<SharedMediaFile>>? _shareSub;
  StreamSubscription<Uri>? _linkSub;
  final _appLinks = AppLinks();
  late final AnimationController _spinController;

  @override
  void initState() {
    super.initState();
    _spinController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat();
    if (!kIsWeb) {
      _listenForShares();
      _listenForUniversalLinks();
    }
    _handleUri(Uri.base);
  }

  void _listenForShares() {
    // Live shares while the app is open
    _shareSub = ReceiveSharingIntent.instance
        .getMediaStream()
        .listen(_handleSharedMedia, onError: (_) {});

    // Share that launched the app cold
    ReceiveSharingIntent.instance.getInitialMedia().then((items) {
      _handleSharedMedia(items);
      ReceiveSharingIntent.instance.reset();
    }).catchError((_) {});
  }

  void _listenForUniversalLinks() {
    _linkSub = _appLinks.uriLinkStream.listen(_handleUri, onError: (_) {});
    _appLinks.getInitialLink().then((uri) {
      if (uri != null) _handleUri(uri);
    }).catchError((_) {});
  }

  void _handleSharedMedia(List<SharedMediaFile> items) {
    final url = items
        .map((i) => i.path)
        .firstWhere((p) => p.startsWith('http'), orElse: () => '');
    if (url.isEmpty) return;
    _populateUrl(url);
  }

  void _handleUri(Uri uri) {
    final encoded = uri.queryParameters['u'];
    if (encoded == null || encoded.isEmpty) return;
    _populateUrl(Uri.decodeComponent(encoded));
  }

  void _populateUrl(String url) {
    setState(() {
      _urlController.text = url;
      _result = null;
      _error = null;
    });
  }

  Future<void> _handlePaste() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    final text = data?.text?.trim();
    if (text == null || text.isEmpty) return;
    _populateUrl(text);
  }

  void _handleClear() {
    _urlController.clear();
    setState(() {
      _result = null;
      _error = null;
    });
  }

  Future<void> _handleKurl() async {
    final url = _urlController.text.trim();
    if (url.isEmpty || _selectedPlatform == null) return;

    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });

    try {
      final data = await ApiService.kurl(url, _selectedPlatform!);
      setState(() => _result = data);
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final urlText = _urlController.text.trim();
    final urlError = validateMusicUrl(urlText);
    final sourcePlatform = detectPlatform(urlText);
    final sourceInfo = sourcePlatform != null ? findPlatform(sourcePlatform) : null;
    final canKurl =
        urlText.isNotEmpty && urlError == null && _selectedPlatform != null && !_loading;

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'kurl',
                      style: TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFE5E5E5),
                        letterSpacing: -0.5,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const FittedBox(
                      fit: BoxFit.scaleDown,
                      alignment: Alignment.centerLeft,
                      child: Text(
                        'Share any song. To anyone. On any streaming service.',
                        maxLines: 1,
                        style: TextStyle(fontSize: 14, color: Color(0xFF888888)),
                      ),
                    ),
                    const SizedBox(height: 20),
                    TextField(
                      controller: _urlController,
                      enabled: !_loading,
                      onChanged: (_) => setState(() {}),
                      style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
                      decoration: InputDecoration(
                        hintText: 'Paste a Spotify, Apple, YouTube link...',
                        hintStyle: const TextStyle(color: Color(0xFF555555), fontSize: 14),
                        filled: true,
                        fillColor: const Color(0xFF141414),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        prefixIcon: sourceInfo != null
                            ? Padding(
                                padding: const EdgeInsets.only(left: 14, right: 10),
                                child: Icon(
                                  sourceInfo.icon,
                                  size: 16,
                                  color: sourceInfo.colour,
                                ),
                              )
                            : null,
                        prefixIconConstraints: const BoxConstraints(minWidth: 0, minHeight: 0),
                        suffixIcon: _urlController.text.isEmpty
                            ? IconButton(
                                onPressed: _loading ? null : _handlePaste,
                                icon: const Icon(Icons.content_paste, size: 18),
                                color: const Color(0xFF888888),
                                tooltip: 'Paste',
                              )
                            : IconButton(
                                onPressed: _loading ? null : _handleClear,
                                icon: const Icon(Icons.close, size: 18),
                                color: const Color(0xFF888888),
                                tooltip: 'Clear',
                              ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: _borderIdle),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(
                            color: urlError != null ? _errorRed : _borderIdle,
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide(
                            color: urlError != null ? _errorRed : _borderFocused,
                          ),
                        ),
                      ),
                    ),
                    if (urlError != null) ...[
                      const SizedBox(height: 6),
                      Text(
                        urlError,
                        style: const TextStyle(color: _errorRed, fontSize: 12),
                      ),
                    ],
                    const SizedBox(height: 16),
                    PlatformPicker(
                      selected: _selectedPlatform,
                      onSelect: (id) => setState(() => _selectedPlatform = id),
                      disabled: _loading,
                    ),
                    const SizedBox(height: 16),
                    _buildKurlButton(canKurl),
                    if (_error != null) ...[
                      const SizedBox(height: 16),
                      Text(
                        _error!,
                        style: const TextStyle(color: _errorRed, fontSize: 13),
                      ),
                    ],
                    if (_result != null) ...[
                      const SizedBox(height: 16),
                      ResultCard(result: _result!),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildKurlButton(bool canKurl) {
    final platform = findPlatform(_selectedPlatform ?? '');
    final platformColour = platform?.colour;
    final bg = platformColour ?? _neutralBg;

    return GestureDetector(
      onTapDown: canKurl ? (_) => setState(() => _pressed = true) : null,
      onTapUp: canKurl ? (_) => setState(() => _pressed = false) : null,
      onTapCancel: canKurl ? () => setState(() => _pressed = false) : null,
      child: AnimatedScale(
        scale: _pressed ? 0.97 : 1.0,
        duration: const Duration(milliseconds: 120),
        curve: Curves.easeOut,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(6),
            boxShadow: canKurl && platformColour != null
                ? [
                    BoxShadow(
                      color: platformColour.withValues(alpha: 0.35),
                      blurRadius: 24,
                      spreadRadius: -4,
                      offset: const Offset(0, 6),
                    ),
                  ]
                : null,
          ),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: canKurl ? _handleKurl : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: bg,
                foregroundColor: const Color(0xFF0A0A0A),
                disabledBackgroundColor: _neutralBg.withValues(alpha: 0.3),
                padding: const EdgeInsets.symmetric(vertical: 18),
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(6),
                ),
                animationDuration: const Duration(milliseconds: 200),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (_loading)
                    RotationTransition(
                      turns: _spinController,
                      child: Icon(platform?.icon ?? Icons.music_note, size: 18),
                    )
                  else
                    const Icon(Icons.waves_rounded, size: 20),
                  const SizedBox(width: 8),
                  Text(
                    _loading ? 'kurling...' : 'kurl it',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      letterSpacing: -0.2,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _shareSub?.cancel();
    _linkSub?.cancel();
    _spinController.dispose();
    _urlController.dispose();
    super.dispose();
  }
}
