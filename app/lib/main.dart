import 'package:flutter/material.dart';
import 'package:flutter_web_plugins/url_strategy.dart';
import 'package:kurl/app/app.dart';

void main() {
  // Use real URLs (kurl.online/?url=...) instead of hash-based (#/?url=...)
  // so Flutter's history engine stops choking on our manual replaceState calls.
  usePathUrlStrategy();
  runApp(const KurlApp());
}
