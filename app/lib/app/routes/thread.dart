import 'dart:async';

import 'package:flutter/material.dart';
import 'package:kurl/app/layout.dart';
import 'package:kurl/models/message.dart';
import 'package:kurl/models/thread.dart';
import 'package:kurl/services/api_exception.dart';
import 'package:kurl/services/social_service.dart';
import 'package:kurl/utils/date_format.dart';
import 'package:kurl/utils/friendly_error.dart';
import 'package:kurl/widgets/shared/result_card.dart';

class ThreadScreen extends StatefulWidget {
  final String threadUid;
  final String? otherUsername; // shown in the app bar before the load resolves

  const ThreadScreen({super.key, required this.threadUid, this.otherUsername});

  @override
  State<ThreadScreen> createState() => _ThreadScreenState();
}

class _ThreadScreenState extends State<ThreadScreen> {
  final _composeController = TextEditingController();
  final _scroll = ScrollController();
  bool _loading = true;
  bool _sending = false;
  bool _wide = false;
  String? _error;
  ThreadDetail? _detail;
  Timer? _poll;

  @override
  void initState() {
    super.initState();
    _load();
    _poll = Timer.periodic(const Duration(seconds: 5), (_) => _refresh());
  }

  Future<void> _load() async {
    try {
      final detail = await SocialService.thread(widget.threadUid);
      if (mounted) {
        setState(() {
          _detail = detail;
          _loading = false;
        });
        _scrollToBottom();
      }
      _markRead();
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = friendlyError(e);
          _loading = false;
        });
      }
    }
  }

  Future<void> _refresh() async {
    try {
      final detail = await SocialService.thread(widget.threadUid);
      if (!mounted) return;
      final gotNew = (_detail?.messages.length ?? 0) < detail.messages.length;
      setState(() => _detail = detail);
      if (gotNew) {
        _scrollToBottom();
        _markRead();
      }
    } catch (_) {
      // Silent -- the next poll retries.
    }
  }

  void _markRead() {
    // Best-effort -- a read-marker failure should not disrupt the thread.
    SocialService.markThreadRead(widget.threadUid).catchError((_) {});
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.jumpTo(_scroll.position.maxScrollExtent);
      }
    });
  }

  Future<void> _send() async {
    final text = _composeController.text.trim();
    if (text.isEmpty || _sending) return;

    setState(() => _sending = true);
    try {
      final message = await SocialService.sendMessage(
        threadUid: widget.threadUid,
        body: text,
      );
      if (mounted) {
        setState(() => _detail?.messages.add(message));
        _composeController.clear();
        _scrollToBottom();
      }
      _markRead();
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
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  void dispose() {
    _poll?.cancel();
    _composeController.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final title =
        widget.otherUsername ?? _detail?.thread.user.username ?? 'Messages';
    final otherUid = _detail?.thread.user.uid;

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0A0A0A),
        title: Text(
          title,
          style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 16),
        ),
        iconTheme: const IconThemeData(color: Color(0xFFE5E5E5)),
        elevation: 0,
        actions: [
          IconButton(
            onPressed: () => setState(() => _wide = !_wide),
            icon: Icon(_wide ? Icons.close_fullscreen : Icons.open_in_full, size: 18),
            color: const Color(0xFF888888),
            tooltip: _wide ? 'Narrow' : 'Widen',
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(child: _centred(_body(otherUid))),
            _centred(
              _ComposeBar(
                controller: _composeController,
                sending: _sending,
                onSend: _send,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _centred(Widget child) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: _wide ? double.infinity : kContentMaxWidth),
        child: child,
      ),
    );
  }

  Widget _body(String? otherUid) {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(
          color: Color(0xFF555555),
          strokeWidth: 2,
        ),
      );
    }
    if (_error != null) {
      return Center(
        child: Text(
          _error!,
          style: const TextStyle(color: Color(0xFF888888), fontSize: 13),
        ),
      );
    }

    final messages = _detail?.messages ?? const [];
    if (messages.isEmpty) {
      return const Center(
        child: Text(
          'No messages yet. Say hello.',
          style: TextStyle(color: Color(0xFF888888), fontSize: 13),
        ),
      );
    }

    return ListView.builder(
      controller: _scroll,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      itemCount: messages.length,
      itemBuilder: (context, i) {
        final message = messages[i];
        return _Bubble(message: message, mine: message.senderUid != otherUid);
      },
    );
  }
}

class _Bubble extends StatelessWidget {
  final Message message;
  final bool mine;

  const _Bubble({required this.message, required this.mine});

  @override
  Widget build(BuildContext context) {
    final kurl = message.displayKurl;
    final body = message.body;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: mine
            ? CrossAxisAlignment.end
            : CrossAxisAlignment.start,
        children: [
          if (body != null && body.isNotEmpty)
            Container(
              constraints: const BoxConstraints(maxWidth: 320),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: mine ? const Color(0xFF2A2A2A) : const Color(0xFF1A1A1A),
                border: Border.all(color: const Color(0xFF333333)),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                body,
                style: const TextStyle(color: Color(0xFFE5E5E5), fontSize: 14),
              ),
            ),
          if (kurl != null) ...[
            if (body != null && body.isNotEmpty) const SizedBox(height: 6),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 360),
              child: ResultCard(result: kurl),
            ),
          ],
          const SizedBox(height: 4),
          Text(
            relativeTime(message.createdAt),
            style: const TextStyle(color: Color(0xFF555555), fontSize: 11),
          ),
        ],
      ),
    );
  }
}

class _ComposeBar extends StatelessWidget {
  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;

  const _ComposeBar({
    required this.controller,
    required this.sending,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: Color(0xFF222222))),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              enabled: !sending,
              minLines: 1,
              maxLines: 4,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => onSend(),
              style: const TextStyle(fontSize: 14, color: Color(0xFFE5E5E5)),
              decoration: InputDecoration(
                hintText: 'Message',
                hintStyle: const TextStyle(
                  color: Color(0xFF555555),
                  fontSize: 14,
                ),
                filled: true,
                fillColor: const Color(0xFF141414),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
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
          ),
          const SizedBox(width: 8),
          Material(
            color: const Color(0xFFE5E5E5),
            borderRadius: BorderRadius.circular(8),
            child: InkWell(
              onTap: sending ? null : onSend,
              borderRadius: BorderRadius.circular(8),
              child: const Padding(
                padding: EdgeInsets.all(12),
                child: Icon(
                  Icons.arrow_upward_rounded,
                  size: 18,
                  color: Color(0xFF0A0A0A),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
