import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'supabase_config.dart';
import 'screens/home_page.dart';
import 'screens/login_page.dart';
import 'screens/register_page.dart';
import 'screens/reset_password_page.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Supabase.initialize(
    url: SupabaseConfig.url,
    publishableKey: SupabaseConfig.publishableKey,
  );
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'Smart_App Supabase',
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
      useMaterial3: true,
    ),
    home: const AuthGate(),
    routes: {
      '/register': (_) => const RegisterPage(),
    },
  );
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = Supabase.instance.client.auth;
    return StreamBuilder<AuthState>(
      stream: auth.onAuthStateChange,
      builder: (context, snapshot) {
        // Si Supabase signale un flux de réinitialisation de mot de passe
        // (lien email cliqué), on affiche la page de reset.
        if (snapshot.data?.event == AuthChangeEvent.passwordRecovery) {
          return const ResetPasswordPage();
        }
        // La session persistée peut déjà être disponible avant
        // le premier événement du flux.
        final session = auth.currentSession;
        return session == null ? const LoginPage() : const HomePage();
      },
    );
  }
}
