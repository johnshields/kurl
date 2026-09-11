import 'package:flutter/material.dart';
import 'package:kurl/app/layout.dart';
import 'package:kurl/app/routes/settings/friends_view.dart';
import 'package:kurl/app/routes/settings/settings_dialogs.dart';
import 'package:kurl/app/routes/settings/settings_style.dart';
import 'package:kurl/models/platform.dart';
import 'package:kurl/models/streaming_account.dart';
import 'package:kurl/models/streaming_provider.dart';
import 'package:kurl/models/user.dart';
import 'package:kurl/services/auth_service.dart';
import 'package:kurl/utils/url_state.dart';
import 'package:kurl/widgets/shared/platform_picker.dart';

class ProfileView extends StatefulWidget {
  final KurlUser user;
  final ValueChanged<KurlUser> onUpdated;
  final VoidCallback onLogout;

  const ProfileView({super.key, required this.user, required this.onUpdated, required this.onLogout});

  @override
  State<ProfileView> createState() => _ProfileViewState();
}

class _ProfileViewState extends State<ProfileView> {
  bool _savingPlatform = false;
  bool _savingNotify = false;
  final Map<StreamingProvider, StreamingAccount> _accounts = {
    for (final provider in StreamingProvider.values) provider: StreamingAccount.disconnected,
  };
  final Set<StreamingProvider> _loading = StreamingProvider.values.toSet();
  final Set<StreamingProvider> _connecting = {};
  bool _resendingVerification = false;

  @override
  void initState() {
    super.initState();
    for (final provider in StreamingProvider.values) {
      _loadStatus(provider);
      WidgetsBinding.instance.addPostFrameCallback((_) => _showReturnMessage(provider));
    }
    WidgetsBinding.instance.addPostFrameCallback((_) => _showVerifyEmailMessage());
  }

  void _showReturnMessage(StreamingProvider provider) {
    final param = Uri.base.queryParameters[provider.key];
    if (param == null || !mounted) return;
    showToast(
      context,
      param == 'connected' ? '${provider.label} connected' : '${provider.label} connection failed',
    );
  }

  void _showVerifyEmailMessage() {
    if (Uri.base.queryParameters['verify'] == null || !mounted) return;
    updateUrlState();
    showToast(context, widget.user.emailVerified ? 'Email verified' : 'Verification link invalid or expired');
  }

  Future<void> _loadStatus(StreamingProvider provider) async {
    final status = await AuthService.streamingStatus(provider.key);
    if (mounted) {
      setState(() {
        _accounts[provider] = status;
        _loading.remove(provider);
      });
    }
  }

  Future<void> _connect(StreamingProvider provider) async {
    setState(() => _connecting.add(provider));
    try {
      await launchStreamingAuth(provider.key);
    } finally {
      if (mounted) setState(() => _connecting.remove(provider));
    }
  }

  Future<void> _resendVerification() async {
    setState(() => _resendingVerification = true);
    try {
      await AuthService.resendVerification();
      if (mounted) showToast(context, 'Verification email sent');
    } catch (_) {
    } finally {
      if (mounted) setState(() => _resendingVerification = false);
    }
  }

  Future<void> _disconnect(StreamingProvider provider) async {
    setState(() => _connecting.add(provider));
    try {
      await AuthService.disconnectStreaming(provider.key);
      if (mounted) setState(() => _accounts[provider] = StreamingAccount.disconnected);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _connecting.remove(provider));
    }
  }

  Future<void> _selectPlatform(String id) async {
    setState(() => _savingPlatform = true);
    try {
      final updated = await AuthService.updateProfile(preferredPlatform: id);
      if (mounted) widget.onUpdated(updated);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _savingPlatform = false);
    }
  }

  Future<void> _deselectPlatform() async {
    setState(() => _savingPlatform = true);
    try {
      final updated = await AuthService.updateProfile(clearPreferredPlatform: true);
      if (mounted) widget.onUpdated(updated);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _savingPlatform = false);
    }
  }

  Future<void> _setNotifyEmail(bool value) async {
    setState(() => _savingNotify = true);
    try {
      final updated = await AuthService.updateProfile(notifyEmail: value);
      if (mounted) widget.onUpdated(updated);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _savingNotify = false);
    }
  }

  Widget _card({required List<Widget> children}) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: children);
  }

  Widget _serviceChip({
    required BuildContext context,
    required String name,
    required IconData? icon,
    required Color? colour,
    required bool loading,
    required bool connected,
    required bool busy,
    required VoidCallback? onTap,
  }) {
    const onColour = Colors.black;
    final fontSize = MediaQuery.of(context).size.width < 420 ? 11.0 : 13.0;
    return Opacity(
      opacity: busy ? 0.5 : 1,
      child: Material(
        color: connected ? colour : const Color(0xFF141414),
        borderRadius: BorderRadius.circular(8),
        child: InkWell(
          onTap: (loading || busy) ? null : onTap,
          borderRadius: BorderRadius.circular(8),
          child: Container(
            clipBehavior: Clip.hardEdge,
            decoration: BoxDecoration(
              border: Border.all(color: connected ? colour! : const Color(0xFF333333)),
              borderRadius: BorderRadius.circular(8),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (loading)
                  const SizedBox(
                    height: 14,
                    width: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF555555)),
                  )
                else
                  Icon(icon, size: 16, color: connected ? onColour : colour),
                const SizedBox(width: 4),
                Flexible(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      name,
                      maxLines: 1,
                      softWrap: false,
                      style: TextStyle(
                        fontSize: fontSize,
                        fontWeight: FontWeight.w500,
                        color: connected ? onColour : const Color(0xFFE5E5E5),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _confirmDisconnect(String name, Future<void> Function() onDisconnect) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF141414),
        title: Text('Disconnect $name?', style: const TextStyle(color: Color(0xFFE5E5E5))),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFF888888))),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Disconnect', style: TextStyle(color: errorRed)),
          ),
        ],
      ),
    );
    if (confirmed == true) await onDisconnect();
  }

  @override
  Widget build(BuildContext context) {
    final initial = widget.user.email.isNotEmpty
        ? widget.user.email[0].toUpperCase()
        : widget.user.username.isNotEmpty
            ? widget.user.username[0].toUpperCase()
            : '?';

    return SingleChildScrollView(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: kContentMaxWidth),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 48, 24, 140),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'settings',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFFE5E5E5),
                    letterSpacing: -0.5,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFF141414),
                        border: Border.all(color: borderIdle),
                      ),
                      child: Text(
                        initial,
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Color(0xFFE5E5E5)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          widget.user.email.isNotEmpty
                              ? Text(
                                  widget.user.email,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(fontSize: 14, color: Color(0xFF888888)),
                                )
                              : TextButton(
                                  onPressed: () => showDialog(
                                    context: context,
                                    builder: (_) => AddEmailDialog(onUpdated: widget.onUpdated),
                                  ),
                                  style: TextButton.styleFrom(
                                    padding: EdgeInsets.zero,
                                    alignment: Alignment.centerLeft,
                                    minimumSize: const Size(0, 0),
                                  ),
                                  child: const Text('Add email', style: TextStyle(fontSize: 14, color: Color(0xFF888888))),
                                ),
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  widget.user.username,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                    color: Color(0xFFE5E5E5),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 4),
                              IconButton(
                                onPressed: () => showDialog(
                                  context: context,
                                  builder: (_) => EditUsernameDialog(
                                    currentUsername: widget.user.username,
                                    onUpdated: widget.onUpdated,
                                  ),
                                ),
                                icon: const Icon(Icons.edit_outlined, size: 14),
                                color: const Color(0xFF888888),
                                padding: EdgeInsets.zero,
                                constraints: const BoxConstraints(),
                                visualDensity: VisualDensity.compact,
                                tooltip: 'Edit username',
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: widget.onLogout,
                      icon: const Icon(Icons.logout_rounded, size: 20, color: errorRed),
                      tooltip: 'Log out',
                    ),
                  ],
                ),
                if (widget.user.email.isNotEmpty && !widget.user.emailVerified) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.error_outline, size: 14, color: Color(0xFF888888)),
                      const SizedBox(width: 6),
                      const Text(
                        'Email not verified',
                        style: TextStyle(fontSize: 12, color: Color(0xFF888888)),
                      ),
                      const SizedBox(width: 8),
                      TextButton(
                        onPressed: _resendingVerification ? null : _resendVerification,
                        style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 0)),
                        child: Text(
                          _resendingVerification ? 'Sending...' : 'Resend',
                          style: const TextStyle(fontSize: 12, color: Color(0xFFE5E5E5)),
                        ),
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 28),
                _card(
                  children: [
                    const Text(
                      'Password',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Text(
                          '••••••••',
                          style: TextStyle(fontSize: 14, color: Color(0xFFE5E5E5), letterSpacing: 2),
                        ),
                        const SizedBox(width: 4),
                        IconButton(
                          onPressed: () => showDialog(
                            context: context,
                            builder: (_) => ChangePasswordDialog(onUpdated: widget.onUpdated),
                          ),
                          icon: const Icon(Icons.edit_outlined, size: 14),
                          color: const Color(0xFF888888),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                          visualDensity: VisualDensity.compact,
                          tooltip: 'Change password',
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                _card(
                  children: [
                    const Text(
                      'Connected services',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    GridView(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 3,
                        mainAxisSpacing: 8,
                        crossAxisSpacing: 8,
                        mainAxisExtent: 48,
                      ),
                      children: [
                        for (final provider in const [StreamingProvider.spotify, StreamingProvider.google, StreamingProvider.soundcloud])
                          _serviceChip(
                            context: context,
                            name: provider.label,
                            icon: findPlatform(provider.platformId)?.icon,
                            colour: findPlatform(provider.platformId)?.colour,
                            loading: _loading.contains(provider),
                            connected: _accounts[provider]!.connected,
                            busy: _connecting.contains(provider),
                            onTap: _accounts[provider]!.connected
                                ? () => _confirmDisconnect(provider.label, () => _disconnect(provider))
                                : () => _connect(provider),
                          ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                _card(
                  children: [
                    const Text(
                      'Preferred service',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                    ),
                    const SizedBox(height: 8),
                    Opacity(
                      opacity: _savingPlatform ? 0.5 : 1,
                      child: PlatformPicker(
                        selected: widget.user.preferredPlatform,
                        onSelect: _selectPlatform,
                        onDeselect: _deselectPlatform,
                        disabled: _savingPlatform,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                _card(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Friends',
                          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFFE5E5E5)),
                        ),
                        TextButton(
                          onPressed: () => Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => const FriendsScreen()),
                          ),
                          style: TextButton.styleFrom(padding: EdgeInsets.zero, minimumSize: const Size(0, 0)),
                          child: const Text('Manage', style: TextStyle(fontSize: 13, color: Color(0xFFE5E5E5))),
                        ),
                      ],
                    ),
                  ],
                ),
                if (widget.user.email.isNotEmpty) ...[
                  const SizedBox(height: 24),
                  _card(
                    children: [
                      Opacity(
                        opacity: _savingNotify ? 0.5 : 1,
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Message emails',
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: Color(0xFFE5E5E5),
                                    ),
                                  ),
                                  SizedBox(height: 2),
                                  Text(
                                    'Email me when a friend sends a message.',
                                    style: TextStyle(fontSize: 12, color: Color(0xFF888888)),
                                  ),
                                ],
                              ),
                            ),
                            Switch(
                              value: widget.user.notifyEmail,
                              onChanged: _savingNotify ? null : _setNotifyEmail,
                              activeTrackColor: const Color(0xFF1DB954),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
