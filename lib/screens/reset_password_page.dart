import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

/// Page affichée après que l'utilisateur a cliqué sur le lien de
/// réinitialisation reçu par email.  Elle lui permet de choisir un
/// nouveau mot de passe.  L'AuthGate la présente automatiquement
/// lorsque Supabase émet l'événement [AuthChangeEvent.passwordRecovery].
class ResetPasswordPage extends StatefulWidget {
  const ResetPasswordPage({super.key});

  @override
  State<ResetPasswordPage> createState() => _ResetPasswordPageState();
}

class _ResetPasswordPageState extends State<ResetPasswordPage> {
  final _formKey = GlobalKey<FormState>();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _loading = false;
  bool _passwordVisible = false;

  @override
  void dispose() {
    _passwordController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  void _snack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _updatePassword() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await Supabase.instance.client.auth.updateUser(
        UserAttributes(password: _passwordController.text),
      );
      // Supabase émet ensuite AuthChangeEvent.userUpdated →
      // AuthGate reviendra automatiquement à HomePage.
      _snack('Mot de passe mis à jour avec succès !');
    } on AuthException catch (e) {
      _snack('Erreur : ${e.message}');
    } catch (_) {
      _snack('Erreur réseau. Veuillez réessayer.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Nouveau mot de passe'),
        centerTitle: true,
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        automaticallyImplyLeading: false, // pas de retour arrière possible
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(Icons.lock_reset, size: 74, color: Colors.teal),
                  const SizedBox(height: 16),
                  const Text(
                    'Choisissez un nouveau mot de passe',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 30),

                  // --- Nouveau mot de passe ---
                  TextFormField(
                    controller: _passwordController,
                    obscureText: !_passwordVisible,
                    decoration: InputDecoration(
                      labelText: 'Nouveau mot de passe (6 caractères min.)',
                      prefixIcon: const Icon(Icons.lock_outline),
                      border: const OutlineInputBorder(),
                      suffixIcon: IconButton(
                        onPressed: () =>
                            setState(() => _passwordVisible = !_passwordVisible),
                        icon: Icon(_passwordVisible
                            ? Icons.visibility
                            : Icons.visibility_off),
                      ),
                    ),
                    validator: (v) =>
                        v == null || v.length < 6 ? 'Au moins 6 caractères' : null,
                  ),
                  const SizedBox(height: 16),

                  // --- Confirmation ---
                  TextFormField(
                    controller: _confirmController,
                    obscureText: !_passwordVisible,
                    decoration: const InputDecoration(
                      labelText: 'Confirmer le mot de passe',
                      prefixIcon: Icon(Icons.lock),
                      border: OutlineInputBorder(),
                    ),
                    validator: (v) => v != _passwordController.text
                        ? 'Les mots de passe ne correspondent pas'
                        : null,
                  ),
                  const SizedBox(height: 24),

                  // --- Bouton ---
                  FilledButton(
                    onPressed: _loading ? null : _updatePassword,
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: _loading
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child:
                                  CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Mettre à jour le mot de passe'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
