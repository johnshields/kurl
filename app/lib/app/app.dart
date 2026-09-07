import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:kurl/app/main_shell.dart';

class KurlApp extends StatelessWidget {
  const KurlApp({super.key});

  @override
  Widget build(BuildContext context) {
    final base = ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF0A0A0A),
    );

    // MainShell manages its own tab routing via history.pushState, entirely
    // outside Flutter's Navigator. Without telling MaterialApp the current
    // location is already the "correct" route, it assumes the default route
    // (/) and syncs the address bar back to that on first frame -- wiping
    // any deep-linked path or query (e.g. /settings?reset=...).
    final initialRoute = kIsWeb ? '${Uri.base.path}${Uri.base.hasQuery ? '?${Uri.base.query}' : ''}' : '/';

    return MaterialApp(
      title: 'kurl',
      debugShowCheckedModeBanner: false,
      theme: base.copyWith(
        textTheme: GoogleFonts.jetBrainsMonoTextTheme(base.textTheme),
      ),
      initialRoute: initialRoute,
      onGenerateRoute: (_) => MaterialPageRoute(builder: (_) => const MainShell()),
    );
  }
}
