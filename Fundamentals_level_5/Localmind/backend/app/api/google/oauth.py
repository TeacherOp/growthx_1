"""
Google OAuth 2.0 flow endpoints.

Educational Note: OAuth 2.0 is the industry standard for authorization.
It allows users to grant our app access to their Google Drive without
sharing their password.

The OAuth Dance:
1. /google/status  - Check if we're configured and connected
2. /google/auth    - Get the authorization URL
3. (User visits Google, grants permission)
4. /google/callback - Google redirects here with auth code
5. /google/disconnect - Remove stored tokens

Security Considerations:
- Never expose client secret to frontend
- Use HTTPS in production for callback URL
- Store refresh tokens securely
- Handle token expiration gracefully

Routes:
- GET  /google/status     - Check configuration and connection
- GET  /google/auth       - Get OAuth authorization URL
- GET  /google/callback   - Handle OAuth callback (redirects)
- POST /google/disconnect - Remove stored tokens
"""
from flask import jsonify, request, redirect, current_app
from app.api.google import google_bp
from app.services.integrations.google import google_auth_service


@google_bp.route('/google/status', methods=['GET'])
def google_status():
    """
    Check Google Drive configuration and connection status.

    Educational Note: This endpoint checks two things:
    1. Is Google OAuth configured? (client ID + secret set in .env)
    2. Is user connected? (valid tokens stored in google_tokens.json)

    Returns:
        {
            "success": true,
            "configured": true,   # OAuth credentials exist
            "connected": true,    # Valid tokens stored
            "email": "user@gmail.com"  # User's email if connected
        }
    """
    try:
        is_configured = google_auth_service.is_configured()
        is_connected, email = google_auth_service.is_connected()

        return jsonify({
            'success': True,
            'configured': is_configured,
            'connected': is_connected,
            'email': email
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error checking Google status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@google_bp.route('/google/auth', methods=['GET'])
def google_auth():
    """
    Start Google OAuth flow by returning the authorization URL.

    Educational Note: The authorization URL contains:
    - client_id: Identifies our app to Google
    - redirect_uri: Where to send user after granting permission
    - scope: What permissions we're requesting (drive.readonly)
    - access_type=offline: Request a refresh token
    - prompt=consent: Always show consent screen (ensures refresh token)

    The frontend will redirect user to this URL.
    After user grants permission, Google redirects back to our callback.

    Returns:
        { "success": true, "auth_url": "https://accounts.google.com/..." }
    """
    try:
        if not google_auth_service.is_configured():
            return jsonify({
                'success': False,
                'error': 'Google OAuth not configured. Please add Client ID and Secret in App Settings.'
            }), 400

        auth_url = google_auth_service.get_auth_url()
        if not auth_url:
            return jsonify({
                'success': False,
                'error': 'Failed to generate auth URL'
            }), 500

        return jsonify({
            'success': True,
            'auth_url': auth_url
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error generating auth URL: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@google_bp.route('/google/callback', methods=['GET'])
def google_callback():
    """
    Handle OAuth callback from Google.

    Educational Note: This is where the OAuth "dance" completes:
    1. Google redirects here with ?code=AUTHORIZATION_CODE
    2. We exchange the code for access + refresh tokens
    3. Tokens are stored in data/google_tokens.json
    4. We redirect user back to frontend with success/error

    Why redirect instead of JSON response?
    - This endpoint is called by Google's redirect, not our frontend
    - User's browser is at accounts.google.com when they click "Allow"
    - We need to send them back to our app with a visual confirmation

    Query Params:
        code: Authorization code from Google (on success)
        error: Error message if user denied access

    Returns:
        Redirect to frontend with ?google_auth=success or ?google_auth=error
    """
    try:
        # Check for error (user denied access)
        error = request.args.get('error')
        if error:
            current_app.logger.warning(f"Google OAuth denied: {error}")
            return redirect(f'http://localhost:5173?google_auth=error&message={error}')

        # Get authorization code
        code = request.args.get('code')
        if not code:
            return redirect('http://localhost:5173?google_auth=error&message=No+authorization+code')

        # Exchange code for tokens
        success, message = google_auth_service.handle_callback(code)

        if success:
            current_app.logger.info(f"Google OAuth successful: {message}")
            return redirect('http://localhost:5173?google_auth=success')
        else:
            current_app.logger.error(f"Google OAuth failed: {message}")
            return redirect(f'http://localhost:5173?google_auth=error&message={message}')

    except Exception as e:
        current_app.logger.error(f"Error in Google callback: {e}")
        return redirect(f'http://localhost:5173?google_auth=error&message={str(e)}')


@google_bp.route('/google/disconnect', methods=['POST'])
def google_disconnect():
    """
    Disconnect Google Drive by removing stored tokens.

    Educational Note: This removes tokens from google_tokens.json.
    User will need to re-authenticate to use Google Drive again.

    Note: This does NOT revoke access at Google's end - user can
    manually revoke at https://myaccount.google.com/permissions

    Returns:
        { "success": true, "message": "Disconnected successfully" }
    """
    try:
        success, message = google_auth_service.disconnect()

        return jsonify({
            'success': success,
            'message': message
        }), 200 if success else 500

    except Exception as e:
        current_app.logger.error(f"Error disconnecting Google: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
