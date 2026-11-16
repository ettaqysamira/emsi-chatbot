import 'package:flutter/material.dart';

/// Modèle d'un message dans le chat.
class _ChatMessage {
  final String text;
  final bool isUser;
  final DateTime time;

  _ChatMessage({
    required this.text,
    required this.isUser,
    required this.time,
  });
}

/// Page de chat style WhatsApp — EMSI Chatbot.
class ChatPage extends StatefulWidget {
  const ChatPage({super.key});

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _botTyping = false;

  final List<_ChatMessage> _messages = [
    _ChatMessage(
      text:
          'Bonjour ! 👋 Je suis le Chatbot officiel de l\'EMSI.\nComment puis-je vous aider aujourd\'hui ?',
      isUser: false,
      time: DateTime.now(),
    ),
  ];

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  // ---------- Logique du chatbot EMSI ----------
  String _getBotResponse(String input) {
    final msg = input.toLowerCase().trim();

    if (msg.contains('bonjour') ||
        msg.contains('salut') ||
        msg.contains('bonsoir') ||
        msg.contains('hello') ||
        msg.contains('salam')) {
      return 'Bonjour ! 😊 Je suis là pour répondre à toutes vos questions sur l\'EMSI.';
    }
    if (msg.contains('inscription') ||
        msg.contains('inscrire') ||
        msg.contains('candidature')) {
      return 'Pour vous inscrire à l\'EMSI :\n'
          '1️⃣ Visitez www.emsi.ma\n'
          '2️⃣ Rubrique "Admissions"\n'
          '3️⃣ Remplissez le formulaire en ligne\n\n'
          'Vous pouvez aussi appeler le secrétariat central. 📞';
    }
    if (msg.contains('filière') ||
        msg.contains('formation') ||
        msg.contains('spécialité') ||
        msg.contains('programme')) {
      return 'L\'EMSI propose plusieurs filières 🎓 :\n'
          '• Génie Informatique\n'
          '• Génie Civil\n'
          '• Génie Électrique\n'
          '• Finance & Comptabilité\n'
          '• Management & Marketing\n\n'
          'Pour plus de détails → www.emsi.ma';
    }
    if (msg.contains('stage') || msg.contains('emploi') || msg.contains('recrutement')) {
      return 'Pour les offres de stages et d\'emploi 💼 :\n'
          '• Portail carrières : emsi.ma/carrieres\n'
          '• Contactez le Bureau des Relations Entreprises\n'
          '• Consultez aussi LinkedIn EMSI';
    }
    if (msg.contains('horaire') ||
        msg.contains('emploi du temps') ||
        msg.contains('cours')) {
      return 'Votre emploi du temps est disponible sur le portail étudiant EMSI. 📅\n'
          'Connectez-vous avec vos identifiants académiques.';
    }
    if (msg.contains('frais') ||
        msg.contains('scolarité') ||
        msg.contains('prix') ||
        msg.contains('coût')) {
      return 'Les frais de scolarité varient selon la filière et le niveau. 💰\n'
          'Contactez le service administratif pour un devis précis :\n'
          '📍 Ou visitez www.emsi.ma → Admissions → Frais';
    }
    if (msg.contains('contact') ||
        msg.contains('téléphone') ||
        msg.contains('adresse') ||
        msg.contains('email')) {
      return 'Coordonnées EMSI 📞 :\n'
          '• Site : www.emsi.ma\n'
          '• Email : contact@emsi.ma\n'
          '• Casablanca : +212 5 22 25 26 27\n'
          '• Plusieurs campus au Maroc 🇲🇦';
    }
    if (msg.contains('bourse') || msg.contains('aide financière')) {
      return 'Des aides financières et bourses sont disponibles pour les étudiants méritants. 🎓\n'
          'Renseignez-vous auprès du service administratif de l\'EMSI.';
    }
    if (msg.contains('merci') || msg.contains('شكرا') || msg.contains('thank')) {
      return 'Avec plaisir ! 😊 N\'hésitez pas si vous avez d\'autres questions.';
    }
    if (msg.contains('au revoir') || msg.contains('bye') || msg.contains('bonne journée')) {
      return 'Au revoir ! 👋 Bonne journée et bon courage dans vos études ! 🎓';
    }
    if (msg.contains('master') || msg.contains('licence') || msg.contains('ingénieur')) {
      return 'L\'EMSI propose des formations allant de la Licence au Master et Ingéniorat. 🎓\n'
          'Durée : 3 à 5 ans selon le cursus.\n'
          'Plus d\'infos → www.emsi.ma';
    }

    // Réponse par défaut
    return 'Je n\'ai pas bien compris votre question. 🤔\n'
        'Vous pouvez me demander des infos sur :\n'
        '• Les inscriptions\n'
        '• Les filières\n'
        '• Les stages & emplois\n'
        '• Les horaires\n'
        '• Les contacts EMSI\n\n'
        'Ou visitez directement www.emsi.ma 🌐';
  }

  // ---------- Envoi d'un message ----------
  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(_ChatMessage(text: text, isUser: true, time: DateTime.now()));
      _controller.clear();
      _botTyping = true;
    });
    _scrollToBottom();

    // Délai simulant la frappe du bot
    Future.delayed(const Duration(milliseconds: 900), () {
      if (!mounted) return;
      setState(() {
        _botTyping = false;
        _messages.add(_ChatMessage(
          text: _getBotResponse(text),
          isUser: false,
          time: DateTime.now(),
        ));
      });
      _scrollToBottom();
    });
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 120), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  // ---------- Build d'une bulle ----------
  Widget _buildBubble(_ChatMessage message) {
    final isUser = message.isUser;
    final timeStr =
        '${message.time.hour.toString().padLeft(2, '0')}:${message.time.minute.toString().padLeft(2, '0')}';

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.only(
          left: isUser ? 64 : 10,
          right: isUser ? 10 : 64,
          top: 3,
          bottom: 3,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF00897B) : Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(18),
            topRight: const Radius.circular(18),
            bottomLeft: Radius.circular(isUser ? 18 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 18),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.08),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Text(
              message.text,
              style: TextStyle(
                color: isUser ? Colors.white : Colors.black87,
                fontSize: 15.5,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  timeStr,
                  style: TextStyle(
                    color: isUser ? Colors.white60 : Colors.grey.shade500,
                    fontSize: 11,
                  ),
                ),
                if (isUser) ...[
                  const SizedBox(width: 4),
                  Icon(Icons.done_all,
                      size: 14, color: Colors.white.withOpacity(0.7)),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ---------- Indicateur "en train d'écrire" ----------
  Widget _buildTypingIndicator() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(left: 10, top: 3, bottom: 3),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(18),
            topRight: Radius.circular(18),
            bottomRight: Radius.circular(18),
            bottomLeft: Radius.circular(4),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.08),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _dot(0),
            const SizedBox(width: 4),
            _dot(150),
            const SizedBox(width: 4),
            _dot(300),
          ],
        ),
      ),
    );
  }

  Widget _dot(int delayMs) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: const Duration(milliseconds: 600),
      curve: Curves.easeInOut,
      builder: (_, v, __) => Opacity(
        opacity: (v * 2 - 1).abs().clamp(0.3, 1.0),
        child: Container(
          width: 8,
          height: 8,
          decoration: const BoxDecoration(
            color: Colors.teal,
            shape: BoxShape.circle,
          ),
        ),
      ),
    );
  }

  // ---------- Build principal ----------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFECE5DD), // fond WhatsApp
      appBar: AppBar(
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        elevation: 2,
        titleSpacing: 0,
        title: Row(
          children: [
            const CircleAvatar(
              radius: 20,
              backgroundColor: Colors.white,
              child: Icon(Icons.smart_toy_outlined, color: Colors.teal, size: 22),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  'EMSI Chatbot',
                  style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white),
                ),
                Text(
                  'En ligne',
                  style: TextStyle(fontSize: 12, color: Colors.white70),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
              icon: const Icon(Icons.search), onPressed: () {}),
          IconButton(
              icon: const Icon(Icons.more_vert), onPressed: () {}),
        ],
      ),
      body: Column(
        children: [
          // ---- Zone des messages ----
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 2),
              itemCount: _messages.length + (_botTyping ? 1 : 0),
              itemBuilder: (context, index) {
                if (_botTyping && index == _messages.length) {
                  return _buildTypingIndicator();
                }
                return _buildBubble(_messages[index]);
              },
            ),
          ),

          // ---- Barre de saisie ----
          Container(
            color: const Color(0xFFF0F0F0),
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
            child: SafeArea(
              child: Row(
                children: [
                  // Emoji
                  IconButton(
                    icon: const Icon(Icons.emoji_emotions_outlined,
                        color: Colors.grey, size: 26),
                    onPressed: () {},
                  ),
                  // Champ texte
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: TextField(
                        controller: _controller,
                        textCapitalization: TextCapitalization.sentences,
                        maxLines: 4,
                        minLines: 1,
                        decoration: const InputDecoration(
                          hintText: 'Entrez un message',
                          hintStyle: TextStyle(color: Colors.grey),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(
                              horizontal: 16, vertical: 10),
                        ),
                        onSubmitted: (_) => _sendMessage(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  // Bouton envoyer
                  GestureDetector(
                    onTap: _sendMessage,
                    child: const CircleAvatar(
                      radius: 24,
                      backgroundColor: Colors.teal,
                      child: Icon(Icons.send, color: Colors.white, size: 22),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
