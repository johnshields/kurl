class KurlUser {
  final String uid;
  final String email;
  final String username;
  final String? preferredPlatform;
  final bool emailVerified;
  final bool notifyEmail;
  final String createdAt;

  const KurlUser({
    required this.uid,
    required this.email,
    required this.username,
    this.preferredPlatform,
    this.emailVerified = false,
    this.notifyEmail = true,
    required this.createdAt,
  });

  factory KurlUser.fromJson(Map<String, dynamic> json) {
    return KurlUser(
      uid: json['uid'],
      email: json['email'] ?? '',
      username: json['username'],
      preferredPlatform: json['preferredPlatform'],
      emailVerified: json['emailVerified'] ?? false,
      notifyEmail: json['notifyEmail'] ?? true,
      createdAt: json['createdAt'] ?? '',
    );
  }
}
