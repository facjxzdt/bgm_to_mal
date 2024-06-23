import http.server
import socketserver
import webbrowser
import requests
import urllib.parse
import json

# 替换为你的 Anilist client_id 和 client_secret
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'http://127.0.0.1:8000/callback'

# Anilist OAuth 2.0 endpoints
AUTHORIZATION_URL = 'https://anilist.co/api/v2/oauth/authorize'
TOKEN_URL = 'https://anilist.co/api/v2/oauth/token'

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/login'):
            self.handle_login()
        elif self.path.startswith('/callback'):
            self.handle_callback()
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Welcome to Anilist OAuth example! <a href="/login">Login with Anilist</a>')

    def handle_login(self):
        auth_url = f'{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code'
        self.send_response(302)
        self.send_header('Location', auth_url)
        self.end_headers()

    def handle_callback(self):
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = query_components.get('code', [None])[0]
        if not code:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Authorization failed.')
            return

        # Exchange authorization code for access token
        token_response = requests.post(TOKEN_URL, data={
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'code': code
        })

        token_json = token_response.json()
        access_token = token_json.get('access_token')

        if not access_token:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Failed to obtain access token.')
            return

        # Print access token to the console
        print(f'Access Token: {access_token}')
        with open('anl_token.json', 'w') as token_file:
            json.dump({'access_token': access_token}, token_file)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Access token obtained. You can close this window.')

if __name__ == '__main__':
    PORT = 8000
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        webbrowser.open(f'http://127.0.0.1:{PORT}')
        httpd.serve_forever()
