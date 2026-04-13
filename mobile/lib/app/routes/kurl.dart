import 'package:flutter/material.dart';
import 'package:kurl/models/kurl_result.dart';
import 'package:kurl/services/api_service.dart';
import 'package:kurl/widgets/shared/platform_picker.dart';
import 'package:kurl/widgets/shared/result_card.dart';

class KurlScreen extends StatefulWidget {
  const KurlScreen({super.key});

  @override
  State<KurlScreen> createState() => _KurlScreenState();
}

class _KurlScreenState extends State<KurlScreen> {
  final _urlController = TextEditingController();
  String? _selectedPlatform;
  KurlResult? _result;
  bool _loading = false;
  String? _error;

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
    final canKurl =
        _urlController.text.trim().isNotEmpty && _selectedPlatform != null && !_loading;

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
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: Color(0xFF333333)),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: Color(0xFF333333)),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: const BorderSide(color: Color(0xFF555555)),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    PlatformPicker(
                      selected: _selectedPlatform,
                      onSelect: (id) => setState(() => _selectedPlatform = id),
                      disabled: _loading,
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: canKurl ? _handleKurl : null,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFE5E5E5),
                          foregroundColor: const Color(0xFF0A0A0A),
                          disabledBackgroundColor: const Color(0xFFE5E5E5).withValues(alpha: 0.3),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        child: Text(
                          _loading ? 'kurling...' : 'kurl it',
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 16),
                      Text(
                        _error!,
                        style: const TextStyle(color: Color(0xFFEF4444), fontSize: 13),
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

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }
}
