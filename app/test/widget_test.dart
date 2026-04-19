import 'package:flutter_test/flutter_test.dart';
import 'package:kurl/app/app.dart';

void main() {
  testWidgets('App renders', (WidgetTester tester) async {
    await tester.pumpWidget(const KurlApp());
    expect(find.text('kurl'), findsOneWidget);
  });
}
