import 'package:kurl/models/user_ref.dart';

class Friend {
  final String uid; // friendship uid -- the accept/remove target
  final UserRef user; // the other party
  final String status; // pending | accepted
  final String createdAt;
  final String? respondedAt;

  const Friend({
    required this.uid,
    required this.user,
    required this.status,
    required this.createdAt,
    this.respondedAt,
  });

  factory Friend.fromJson(Map<String, dynamic> json) {
    return Friend(
      uid: json['uid'],
      user: UserRef.fromJson(json['user']),
      status: json['status'] ?? 'pending',
      createdAt: json['createdAt'] ?? '',
      respondedAt: json['respondedAt'],
    );
  }
}

class FriendsOverview {
  final List<Friend> friends;
  final List<Friend> incoming;
  final List<Friend> outgoing;

  const FriendsOverview({
    required this.friends,
    required this.incoming,
    required this.outgoing,
  });

  factory FriendsOverview.fromJson(Map<String, dynamic> json) {
    return FriendsOverview(
      friends: _list(json['friends']),
      incoming: _list(json['incoming']),
      outgoing: _list(json['outgoing']),
    );
  }

  static List<Friend> _list(dynamic raw) =>
      (raw as List? ?? const []).map((e) => Friend.fromJson(e)).toList();

  static const empty = FriendsOverview(friends: [], incoming: [], outgoing: []);
}
