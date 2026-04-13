import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:kurl/app/routes/kurl.dart';

class KurlApp extends StatelessWidget {
  const KurlApp({super.key});

  @override
  Widget build(BuildContext context) {
    final base = ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: const Color(0xFF0A0A0A),
    );

    return MaterialApp(
      title: 'kurl',
      debugShowCheckedModeBanner: false,
      theme: base.copyWith(
        textTheme: GoogleFonts.jetBrainsMonoTextTheme(base.textTheme),
      ),
      home: const KurlScreen(),
    );
  }
}
