"""Direct ChatGPT-plan OAuth; no Codex credentials or agent harness involved."""
import argparse
import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile
import time
import uuid
import webbrowser
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import jwt
from openai import OpenAI

AUTH = 'https://auth.openai.com'
RESOURCE = 'https://api.openai.com/v1'
MODEL = 'gpt-6-luna'
SCOPE = 'openid profile email offline_access resource.invoke chatgpt.tokens.use.direct'
STATE_PATH = Path(__file__).resolve().parents[1] / '.lasrca-oauth' / 'account.bin'


class OAuthError(RuntimeError):
    pass


def protect(data, decrypt=False):
    # Windows DPAPI ties the encrypted credential record to this OS account.
    if os.name != 'nt':
        raise OAuthError('This credential store requires Windows DPAPI.')
    class Blob(ctypes.Structure):
        _fields_ = [('size', ctypes.c_ulong), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    fn = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise OAuthError('Windows credential protection failed.')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.windll.kernel32.LocalFree(target.data)


@contextmanager
def account_lock():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = STATE_PATH.with_suffix('.lock')
    deadline = time.monotonic() + 30
    while True:
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise OAuthError('OAuth credential store is busy; retry later.') from None
            time.sleep(.1)
    try:
        yield
    finally:
        os.close(fd)
        lock.unlink()


def load_account():
    if not STATE_PATH.exists():
        return {}
    return json.loads(protect(STATE_PATH.read_bytes(), decrypt=True))


def save_account(record):
    encrypted = protect(json.dumps(record).encode())
    fd, path = tempfile.mkstemp(dir=STATE_PATH.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(encrypted)
        os.replace(path, STATE_PATH)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def new_host_id():
    return 'urn:uuid:' + str(uuid.uuid4())


def exchange(fields):
    try:
        response = httpx.post(AUTH + '/api/accounts/oauth/token', data=fields, timeout=30)
        response.raise_for_status()
        tokens = response.json()
    except Exception:
        raise OAuthError('OAuth token exchange failed; please sign in again.') from None
    if 'chatgpt.tokens.use.direct' not in tokens.get('scope', '').split():
        raise OAuthError('ChatGPT plan usage permission was not granted.')
    return tokens


def validate_callback(values, state, client_id):
    if values.get('state') != [state]:
        raise OAuthError('OAuth callback state did not match.')
    if values.get('error'):
        raise OAuthError('OAuth authorization was declined or failed.')
    clients = values.get('client_id', [client_id])
    if len(clients) != 1:
        raise OAuthError('OAuth callback did not contain one client identity.')
    issued = clients[0]
    if not issued or issued == 'dynamic_agent_client' or (client_id and issued != client_id):
        raise OAuthError('OAuth callback client identity did not match.')
    code = values.get('code', [])
    if len(code) != 1:
        raise OAuthError('OAuth callback did not contain one authorization code.')
    return code[0], issued


def login():
    with account_lock():
        old = load_account()
        host = old.get('host_id')
        if not host or (not old.get('client_id') and not host.startswith('urn:')):
            host = new_host_id()
            old['host_id'] = host
            save_account(old)
    state, nonce, verifier = [secrets.token_urlsafe(32) for _ in range(3)]
    callback = {}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Callback contains credentials; never log it.
        def do_GET(self):
            url = urlparse(self.path)
            values = parse_qs(url.query)
            if url.path != '/auth/callback' or values.get('state') != [state]:
                self.send_error(400, 'Invalid OAuth callback')
                return
            callback.update(values)
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'Authorization received. Return to LasRCA for validation.')
    with HTTPServer(('127.0.0.1', 0), Handler) as server:
        redirect = f'http://127.0.0.1:{server.server_port}/auth/callback'
        params = dict(client_id=old.get('client_id','dynamic_agent_client'),
            ext_agent_host_id=host, response_type='code', redirect_uri=redirect,
            scope=SCOPE, resource=RESOURCE, state=state, nonce=nonce,
            code_challenge_method='S256', code_challenge=base64.urlsafe_b64encode(
                hashlib.sha256(verifier.encode()).digest()).decode().rstrip('='))
        if old.get('client_id'):
            if old.get('id_token'):
                params['id_token_hint'] = old['id_token']
        else:
            params['agent_name_hint'] = 'LasRCA'
        print('Continue with ChatGPT in the browser. Waiting up to 10 minutes.', flush=True)
        webbrowser.open(AUTH + '/api/accounts/authorize?' + urlencode(params))
        server.timeout = 1
        deadline = time.monotonic() + 600
        while not callback and time.monotonic() < deadline:
            server.handle_request()
    if not callback:
        raise OAuthError('OAuth sign-in timed out.')
    code, client_id = validate_callback(callback, state, old.get('client_id'))
    tokens = exchange(dict(grant_type='authorization_code',client_id=client_id,
        code=code, code_verifier=verifier, redirect_uri=redirect,resource=RESOURCE))
    validation_step = 'discovery'
    try:
        config = httpx.get(AUTH+'/.well-known/openid-configuration',timeout=30).json()
        if not config['jwks_uri'].startswith(AUTH + '/'):
            raise ValueError('Invalid JWKS origin')
        validation_step = 'signature key lookup'
        key = jwt.PyJWKClient(config['jwks_uri']).get_signing_key_from_jwt(tokens['id_token'])
        validation_step = 'signature and claims'
        identity = jwt.decode(tokens['id_token'], key.key, algorithms=['RS256'],
            audience=client_id, issuer=AUTH, options={'require':['exp','iss','aud','sub','nonce']})
        validation_step = 'nonce and account identity'
        if identity['nonce'] != nonce or (old.get('sub') and old['sub'] != identity['sub']):
            raise ValueError('Invalid identity')
    except Exception as error:
        raise OAuthError(f'OAuth ID token validation failed at {validation_step} ({type(error).__name__}); credentials were not activated.') from None
    with account_lock():
        save_account(dict(tokens,host_id=host,client_id=client_id,sub=identity['sub'],
            email=identity.get('email',''),expires_at=time.time()+tokens['expires_in']))
    print('LasRCA OAuth sign-in verified.', flush=True)


def sdk_client():
    with account_lock():
        account = load_account()
        if not account.get('access_token'):
            raise OAuthError('Run python -m llm.luna_oauth login first.')
        if account['expires_at'] <= time.time() + 60:
            replacement = exchange(dict(grant_type='refresh_token',client_id=account['client_id'],
                refresh_token=account['refresh_token'],resource=RESOURCE))
            account.update(replacement)
            account['expires_at'] = time.time() + replacement['expires_in']
            save_account(account)
        token = account['access_token']
    return OpenAI(api_key=token,base_url=RESOURCE,max_retries=0,timeout=180)


class LunaClient:
    def __init__(self, factory=sdk_client):
        self.factory = factory

    def complete(self, content):
        pieces = []
        completed = False
        stream = None
        sdk = None
        try:
            sdk = self.factory()
            stream = sdk.responses.create(model=MODEL,
                input=[{'role':'user','content':content}],store=False,stream=True)
            for event in stream:
                if event.type == 'response.output_text.delta':
                    pieces.append(event.delta)
                elif event.type == 'response.completed':
                    completed = event.response.status == 'completed'
                    usage = getattr(event.response, 'usage', None)
                    self.last_metadata = dict(returned_model=getattr(event.response,'model',None),
                        usage=usage.model_dump() if usage is not None else None)
                elif event.type in ('response.failed','response.incomplete','error'):
                    raise OAuthError('Luna response failed or was incomplete; no output saved.')
        except OAuthError:
            raise
        except Exception:
            raise OAuthError('Luna request failed; check OAuth access, quota, and network.') from None
        finally:
            if stream is not None and hasattr(stream,'close'):
                stream.close()
            if sdk is not None and hasattr(sdk,'close'):
                sdk.close()
        text = ''.join(pieces)
        if not completed or not text.strip():
            raise OAuthError('Luna stream ended without a complete text response.')
        return text


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['login','check'])
    args = parser.parse_args()
    try:
        if args.action == 'login':
            login()
        else:
            result = LunaClient().complete('Reply with exactly: LUNA_OK')
            if result.strip() != 'LUNA_OK':
                raise OAuthError('Luna connectivity check returned an unexpected response.')
            print('gpt-6-luna OAuth inference completed: LUNA_OK')
    except OAuthError as error:
        parser.exit(1, str(error)+'\n')
