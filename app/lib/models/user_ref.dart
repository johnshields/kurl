/// A lightweight {uid, username} reference, as returned inside friend and
/// thread payloads.
class UserRef {
  final String uid;
  final String username;

  const UserRef({required this.uid, required this.username});

  factory UserRef.fromJson(Map<String, dynamic> json) {
    return UserRef(uid: json['uid'], username: json['username'] ?? '');
  }
}
