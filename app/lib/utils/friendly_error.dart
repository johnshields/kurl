import 'package:kurl/services/api_service.dart';

// Map backend error codes (and stray network exceptions) to user-facing copy.
// Codes are the contract -- backend strings can change without breaking the UI.

const _codeMessages = <String, String>{
  'TRACK_NOT_FOUND': "Couldn't find this track. Try a different link.",
  'PLATFORM_NOT_FOUND': "That platform isn't supported yet.",
  'UNKNOWN_PLATFORM': "That platform isn't supported yet.",
  'SEARCH_URL': "That's a search page — paste a link to a specific track.",
  'INVALID_REQUEST': "Something's off with that link. Try copying it again.",
  'AUTH_REQUIRED': "Session expired. Refresh and retry.",
  'AUTH_INVALID': "Session expired. Refresh and retry.",
  'RATE_LIMITED': "Too many requests. Wait a moment and try again.",
  'ODESLI_ERROR': "Couldn't find this track. Try a different link.",
  'NOT_FOUND': "That endpoint doesn't exist.",
  'INVALID_RESPONSE': "Server hiccup. Try again in a moment.",
  'INTERNAL_ERROR': "Server hiccup. Try again in a moment.",
};

const _genericFallback = "Something went wrong. Try again in a moment.";

String friendlyError(Object error) {
  if (error is ApiException) {
    return _codeMessages[error.code] ?? _genericFallback;
  }

  // Network / connectivity errors don't carry a code.
  final lower = error.toString().toLowerCase();
  if (lower.contains('socket') ||
      lower.contains('network') ||
      lower.contains('connection') ||
      lower.contains('failed host lookup') ||
      lower.contains('timeout')) {
    return "Network hiccup. Check your connection and retry.";
  }

  return _genericFallback;
}
