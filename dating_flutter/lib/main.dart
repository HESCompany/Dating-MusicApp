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
      title: 'Music Recommender',
      theme: ThemeData(
        primarySwatch: Colors.purple,
        brightness: Brightness.dark,
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
  int currentUserId = 1;
  String selectedRecommendationType = 'hybrid';

  @override
  void initState() {
    super.initState();
    fetchUserData();
    fetchRecommendations();
  }

  Future<void> fetchUserData() async {
    final response = await http.get(
      Uri.parse('$baseUrl/users/$currentUserId')
    );
    
    if (response.statusCode == 200) {
      setState(() {
        userData = json.decode(response.body);
      });
    }
  }

  Future<void> fetchRecommendations() async {
    final response = await http.get(
      Uri.parse('$baseUrl/recommendations/$selectedRecommendationType/$currentUserId')
    );
    
    if (response.statusCode == 200) {
      setState(() {
        recommendations = json.decode(response.body);
      });
    }
  }

  void updateUser(int newUserId) {
    setState(() {
      currentUserId = newUserId;
    });
    fetchUserData();
    fetchRecommendations();
  }

  Widget buildUserCard() {
    return Card(
      margin: const EdgeInsets.all(16.0),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Username: ${userData['username'] ?? ''}',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text('Preferred Mood: ${userData['preferred_mood'] ?? ''}'),
            const SizedBox(height: 8),
            Text('Favorite Genres: ${(userData['favorite_genres'] as List?)?.join(', ') ?? ''}'),
            const SizedBox(height: 8),
            Text('Listening History Count: ${(userData['listening_history'] as List?)?.length ?? 0} songs'),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Music Recommender'),
        actions: [
          PopupMenuButton<String>(
            onSelected: (String value) {
              setState(() {
                selectedRecommendationType = value;
                fetchRecommendations();
              });
            },
            itemBuilder: (BuildContext context) => [
              const PopupMenuItem(
                value: 'hybrid',
                child: Text('Hybrid'),
              ),
              const PopupMenuItem(
                value: 'content',
                child: Text('Content-based'),
              ),
              const PopupMenuItem(
                value: 'collaborative',
                child: Text('Collaborative'),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Text('User ID: $currentUserId'),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.remove),
                  onPressed: () {
                    if (currentUserId > 1) {
                      updateUser(currentUserId - 1);
                    }
                  },
                ),
                IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: () {
                    updateUser(currentUserId + 1);
                  },
                ),
              ],
            ),
          ),
          buildUserCard(),
          const Padding(
            padding: EdgeInsets.all(16.0),
            child: Text(
              'Recommendations',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: recommendations.length,
              itemBuilder: (context, index) {
                final recommendation = recommendations[index];
                return ListTile(
                  leading: CircleAvatar(
                    child: Text(recommendation['song_id'].toString()),
                  ),
                  title: Text(recommendation['title']),
                  subtitle: Text(recommendation['artist']),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(recommendation['genre']),
                      if (recommendation['similarity_score'] != null)
                        Text(
                          'Score: ${recommendation['similarity_score'].toStringAsFixed(2)}',
                          style: const TextStyle(fontSize: 12),
                        ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          fetchUserData();
          fetchRecommendations();
        },
        child: const Icon(Icons.refresh),
      ),
    );
  }
}
