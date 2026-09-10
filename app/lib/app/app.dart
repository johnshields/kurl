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

    // Seed the real location so MaterialApp keeps deep-link query params
    // instead of resetting the URL to / on the first frame.
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
