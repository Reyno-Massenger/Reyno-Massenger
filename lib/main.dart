import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'core/theme/app_theme.dart';

/// Reyno Messenger Lite (Flutter Web) — same API & look as the served web app:
/// Sapphire #2481CC, Midnight Slate dark theme, Telegram-like chat UI.
/// Username+password only. No profile/bio/phone/2FA/notifications/Persian/ghost/
/// folders/devices/documents/GIF/polls/secret/spoiler/scheduled features.
void main() => runApp(const ReynoLite());

class Api {
  static String get base => '${Uri.base.origin}/api/v1';
  static String? token;
  static Future<Map<String, dynamic>> call(String m, String p,
      [Map<String, dynamic>? b]) async {
    final h = {'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token'};
    final u = Uri.parse('$base$p');
    final r = m == 'GET'
        ? await http.get(u, headers: h)
        : await http.post(u, headers: h, body: jsonEncode(b ?? {}));
    final j = jsonDecode(r.body.isEmpty ? '{}' : r.body) as Map<String, dynamic>;
    if (r.statusCode >= 300) throw Exception(j['error'] ?? 'Error ${r.statusCode}');
    return j;
  }
}

class ReynoLite extends StatefulWidget {
  const ReynoLite({super.key});
  @override State<ReynoLite> createState() => _S();
}
class _S extends State<ReynoLite> {
  bool dark = true;
  @override Widget build(BuildContext c) => MaterialApp(
      title: 'Reyno Messenger Lite', debugShowCheckedModeBanner: false,
      themeMode: dark ? ThemeMode.dark : ThemeMode.light,
      // Pixel-identical to the original Reyno app: the original AppTheme
      // (lib/core/theme/app_theme.dart, copied verbatim) is used as-is.
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      home: LoginPage(onTheme: () => setState(() => dark = !dark)));
}

class LoginPage extends StatefulWidget {
  final VoidCallback onTheme; const LoginPage({super.key, required this.onTheme});
  @override State<LoginPage> createState() => _L();
}
class _L extends State<LoginPage> {
  final u = TextEditingController(), p = TextEditingController();
  bool reg = false; String? err;
  Future<void> go() async {
    try {
      final j = await Api.call('POST', '/auth/${reg ? 'register' : 'login'}',
          {'username': u.text.trim(), 'password': p.text});
      Api.token = j['access_token'] as String;
      (await SharedPreferences.getInstance()).setString('token', Api.token!);
      if (mounted) Navigator.pushReplacement(context,
          MaterialPageRoute(builder: (_) => HomePage(onTheme: widget.onTheme)));
    } catch (e) { setState(() => err = '$e'); }
  }
  @override Widget build(BuildContext c) => Scaffold(body: Center(child: SizedBox(
      width: 400, child: Card(child: Padding(padding: const EdgeInsets.all(24),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Image.asset('assets/icons/reyno_logo_dark.png', height: 56),
        const Text('Reyno Messenger Lite', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        TextField(controller: u, decoration: const InputDecoration(labelText: 'Username')),
        TextField(controller: p, obscureText: true, decoration: const InputDecoration(labelText: 'Password')),
        if (err != null) Text(err!, style: const TextStyle(color: Colors.red)),
        const SizedBox(height: 12),
        FilledButton(onPressed: go, child: Text(reg ? 'Create account' : 'Sign in')),
        TextButton(onPressed: () => setState(() => reg = !reg),
            child: Text(reg ? 'Sign in instead' : 'Create account')),
        IconButton(onPressed: widget.onTheme, icon: const Icon(Icons.brightness_6)),
      ]))))));
}

class HomePage extends StatefulWidget {
  final VoidCallback onTheme; const HomePage({super.key, required this.onTheme});
  @override State<HomePage> createState() => _H();
}
class _H extends State<HomePage> {
  List chats = []; Map? cur; List msgs = [];
  final t = TextEditingController();
  @override void initState() { super.initState(); load(); }
  Future<void> load() async {
    final j = await Api.call('GET', '/chats'); setState(() => chats = j['chats'] as List);
  }
  Future<void> open(Map c) async {
    setState(() => cur = c);
    final j = await Api.call('GET', '/messages/chat/${c['id']}');
    setState(() => msgs = j['messages'] as List);
  }
  Future<void> send() async {
    if (cur == null || t.text.trim().isEmpty) return;
    await Api.call('POST', '/messages/chat/${cur!['id']}',
        {'message_type': 'text', 'content': t.text.trim()});
    t.clear(); await open(cur!); await load();
  }
  @override Widget build(BuildContext c) => Scaffold(
    appBar: AppBar(title: const Text('Reyno Messenger Lite'), actions: [
      IconButton(onPressed: widget.onTheme, icon: const Icon(Icons.brightness_6))]),
    body: Row(children: [
      SizedBox(width: 340, child: ListView(children: [
        for (final ch in chats) ListTile(
          leading: CircleAvatar(child: Text('${ch['name'] ?? '?'}'[0])),
          title: Text('${ch['name'] ?? 'Chat'}'),
          subtitle: Text(ch['other_user']?['is_online'] == true ? 'online' : ''),
          onTap: () => open(ch as Map)),
      ])),
      const VerticalDivider(width: 1),
      Expanded(child: cur == null
          ? const Center(child: Text('Select a chat or search in the web app'))
          : Column(children: [
              Expanded(child: ListView(children: [
                for (final m in msgs) Align(
                  alignment: m['sender_id'] != null ? Alignment.centerLeft : Alignment.centerLeft,
                  child: Card(child: Padding(padding: const EdgeInsets.all(10),
                      child: Text('${m['content'] ?? m['message_type'] ?? ''}')))),
              ])),
              Row(children: [
                Expanded(child: TextField(controller: t,
                    decoration: const InputDecoration(hintText: 'Message...'))),
                IconButton(onPressed: send, icon: const Icon(Icons.send)),
              ]),
            ])),
    ]));
}
