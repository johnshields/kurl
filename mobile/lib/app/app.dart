import 'package:flutter/material.dart';
import 'package:kurl/app/routes/resolve.dart';

class KurlApp extends StatelessWidget {
  const KurlApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'kurl',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0A0A),
      ),
      home: const ResolveScreen(),
    );
  }
}
