import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const MusicRecommenderApp());
}

class MusicRecommenderApp extends StatelessWidget {
  const MusicRecommenderApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Music Mood',
      theme: ThemeData(
        primarySwatch: Colors.deepPurple,
        brightness: Brightness.dark,
        cardTheme: CardTheme(
          elevation: 8,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final String baseUrl = 'https://kj87tnfl-8000.asse.devtunnels.ms';
  List<dynamic> recommendations = [];
  Map<String, dynamic> userData = {};
  Map<String, dynamic> userProfile = {};
  int currentUserId = 1;

  @override
  void initState() {
    super.initState();
    fetchUserData();
    fetchRecommendations();
  }

  Future<void> fetchUserData() async {
    final response = await http.get(Uri.parse('$baseUrl/users/$currentUserId'));
    if (response.statusCode == 200) {
      setState(() {
        userData = json.decode(response.body);
      });
    }
  }

  Future<void> fetchRecommendations() async {
    final response = await http.get(Uri.parse('$baseUrl/recommendations/$currentUserId'));
    if (response.statusCode == 200) {
      setState(() {
        recommendations = json.decode(response.body);
      });
    }
  }

  Widget buildMusicMetricsCard() {
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Your Music Profile',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: Colors.deepPurpleAccent,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            buildMetricRow('Energy', userData['profile']?['energy'] ?? 0),
            buildMetricRow('Danceability', userData['profile']?['danceability'] ?? 0),
            buildMetricRow('Tempo', userData['profile']?['tempo'] ?? 0),
            buildMetricRow('Popularity', userData['profile']?['popularity'] ?? 0),
            const Divider(height: 32),
            Text(
              'Favorite Genres',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            Wrap(
              spacing: 8,
              children: (userData['favorite_genres'] as List<dynamic>? ?? [])
                  .map((genre) => Chip(
                        label: Text(genre),
                        backgroundColor: Colors.deepPurple.withOpacity(0.2),
                      ))
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget buildMetricRow(String label, double value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          const SizedBox(height: 4),
          LinearProgressIndicator(
            value: value,
            backgroundColor: Colors.grey.withOpacity(0.2),
            valueColor: AlwaysStoppedAnimation<Color>(Colors.deepPurpleAccent),
            borderRadius: BorderRadius.circular(4),
          ),
          Text(
            '${(value * 100).toStringAsFixed(1)}%',
            style: const TextStyle(fontSize: 12),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Music Mood'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              fetchUserData();
              fetchRecommendations();
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await fetchUserData();
          await fetchRecommendations();
        },
        child: ListView(
          children: [
            buildMusicMetricsCard(),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Recommended for You',
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
            ...recommendations.map((rec) => Card(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: Colors.deepPurple.withOpacity(0.2),
                      child: Icon(Icons.music_note, color: Colors.deepPurpleAccent),
                    ),
                    title: Text(rec['title']),
                    subtitle: Text(rec['artist']),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(rec['genre']),
                        Text(
                          'Match: ${(rec['similarity_score'] * 100).toStringAsFixed(0)}%',
                          style: TextStyle(
                            color: Colors.greenAccent,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                )),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          setState(() {
            currentUserId = (currentUserId % 20) + 1;
            fetchUserData();
            fetchRecommendations();
          });
        },
        child: const Icon(Icons.skip_next),
        backgroundColor: Colors.deepPurpleAccent,
      ),
    );
  }
}