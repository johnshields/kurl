import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:ui_web' as ui_web;

import 'package:flutter/widgets.dart';
import 'package:web/web.dart' as web;

import 'package:kurl/app/config.dart';

// AdSense responsive display ad. Each instance registers a unique view type
// keyed on slot id so multiple banners render independently on the page.
class AdBanner extends StatefulWidget {
  final String slot;
  final double height;

  const AdBanner({super.key, required this.slot, this.height = 90});

  @override
  State<AdBanner> createState() => _AdBannerState();
}

class _AdBannerState extends State<AdBanner> {
  late final String _viewType;

  @override
  void initState() {
    super.initState();
    _viewType = 'adsense-${widget.slot}';
    ui_web.platformViewRegistry.registerViewFactory(_viewType, (int viewId) {
      final ins = web.document.createElement('ins') as web.HTMLElement;
      ins.className = 'adsbygoogle';
      ins.style.display = 'block';
      ins.style.width = '100%';
      ins.style.height = '100%';
      ins.setAttribute('data-ad-client', adsenseClient);
      ins.setAttribute('data-ad-slot', widget.slot);
      ins.setAttribute('data-ad-format', 'auto');
      ins.setAttribute('data-full-width-responsive', 'true');

      // Push to adsbygoogle queue once element is mounted.
      Future<void>.delayed(Duration.zero, () {
        try {
          final adsbygoogle = globalContext.getProperty('adsbygoogle'.toJS);
          if (adsbygoogle.isDefinedAndNotNull) {
            (adsbygoogle as JSObject).callMethod(
              'push'.toJS,
              JSObject(),
            );
          }
        } catch (_) {
          // AdSense script not loaded (blocked / dev env) -- silent fail.
        }
      });

      return ins;
    });
  }

  @override
  Widget build(BuildContext context) {
    // Render nothing if AdSense isn't configured.
    if (adsenseClient.isEmpty || widget.slot.isEmpty) {
      return const SizedBox.shrink();
    }
    return SizedBox(
      height: widget.height,
      width: double.infinity,
      child: HtmlElementView(viewType: _viewType),
    );
  }
}
