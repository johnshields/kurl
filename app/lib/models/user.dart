class KurlUser {
  final String uid;
  final String email;
  final String username;
  final String? preferredPlatform;
  final String createdAt;

  const KurlUser({
    required this.uid,
    required this.email,
    required this.username,
    this.preferredPlatform,
    required this.createdAt,
  });

  factory KurlUser.fromJson(Map<String, dynamic> json) {
    return KurlUser(
      uid: json['uid'],
      email: json['email'],
      username: json['username'],
      preferredPlatform: json['preferredPlatform'],
      createdAt: json['createdAt'] ?? '',
    );
  }
}
