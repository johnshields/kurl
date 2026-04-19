import 'dart:async';

import 'package:flutter/material.dart';

/// Scrolls horizontally when content overflows its available width.
/// Pauses at each end, ping-pongs back and forth.
/// Fades edges so overflowing text bleeds in/out smoothly.
class MarqueeText extends StatefulWidget {
  final Widget child;
  final Duration pause;
  final double pixelsPerSecond;

  const MarqueeText({
    super.key,
    required this.child,
    this.pause = const Duration(milliseconds: 1500),
    this.pixelsPerSecond = 18,
  });

  @override
  State<MarqueeText> createState() => _MarqueeTextState();
}

class _MarqueeTextState extends State<MarqueeText> {
  final _controller = ScrollController();
  bool _running = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeStart());
  }

  @override
  void didUpdateWidget(covariant MarqueeText oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Reset scroll position when content changes.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_controller.hasClients) return;
      _controller.jumpTo(0);
    });
  }

  Future<void> _maybeStart() async {
    if (_running || !mounted || !_controller.hasClients) return;
    _running = true;
    while (mounted && _controller.hasClients) {
      final max = _controller.position.maxScrollExtent;
      if (max <= 0) {
        // Fits -- no scroll needed.
        _running = false;
        return;
      }
      await Future.delayed(widget.pause);
      if (!mounted || !_controller.hasClients) break;
      await _controller.animateTo(
        max,
        duration: Duration(milliseconds: (max / widget.pixelsPerSecond * 1000).round()),
        curve: Curves.easeInOut,
      );
      if (!mounted || !_controller.hasClients) break;
      await Future.delayed(widget.pause);
      if (!mounted || !_controller.hasClients) break;
      await _controller.animateTo(
        0,
        duration: Duration(milliseconds: (max / widget.pixelsPerSecond * 1000).round()),
        curve: Curves.easeInOut,
      );
    }
    _running = false;
  }

  @override
  Widget build(BuildContext context) {
    return ShaderMask(
      shaderCallback: (bounds) => const LinearGradient(
        begin: Alignment.centerLeft,
        end: Alignment.centerRight,
        colors: [
          Colors.transparent,
          Colors.black,
          Colors.black,
          Colors.transparent,
        ],
        stops: [0.0, 0.005, 0.995, 1.0],
      ).createShader(bounds),
      blendMode: BlendMode.dstIn,
      child: SingleChildScrollView(
        controller: _controller,
        scrollDirection: Axis.horizontal,
        physics: const NeverScrollableScrollPhysics(),
        child: widget.child,
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
