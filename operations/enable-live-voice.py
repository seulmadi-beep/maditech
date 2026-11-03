#!/usr/bin/env python3
"""Install the MadiTech Live voice gateway on the existing Hetzner backend.
Runs on that server only. Keeps the Google key server-side and backs up files.
"""
import ast
import base64
import hashlib
import socket
import ssl
import struct
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path('/root/ai-money-machine/backend')
GATEWAY = ROOT / 'app/infrastructure/ai/maditech_live_gateway.py'
MAIN = ROOT / 'app/main.py'
KEY = Path('/root/.config/maditech/gemini.key')
ORIGIN = 'https://maditech.onrender.com'
PATH = '/api/v1/chatbot/maditech/live-session'

GATEWAY_CODE = r'''from __future__ import annotations
import asyncio
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ORIGIN = "https://maditech.onrender.com"
ROUTE = "/api/v1/chatbot/maditech/live-session"
FOLDER = Path(__file__).resolve().parents[3] / ".maditech-private"


def mint(language):
    key = (FOLDER / "gemini.key").read_text().strip()
    model = (FOLDER / "live-model").read_text().strip()
    api_version = (FOLDER / "live-version").read_text().strip()
    prompt = (
        "You are MadiTech's digital guardian, a friendly AI assistant. "
        "MadiTech is Mahdi Alizadeh's technology brand based in Geneva, Switzerland. "
        "It covers AI and automation, robotics concepts, creative studio work and apps. "
        "Speak naturally, warmly and concisely, usually one or two sentences per turn. "
        "Match the visitor's language; start in " + {"fa": "Persian", "fr": "French", "en": "English"}[language] + ". "
        "Never invent completed client work, prices, contact details or bookings. "
        "This voice session cannot submit requests or verify calendar availability. "
        "For projects, direct visitors to the Project desk; its brief is a local download, not an online submission. "
        "Do not claim to be human. Do not ask for passwords or payment details."
    )
    setup = {
        "model": model,
        "generationConfig": {"responseModalities": ["AUDIO"], "maxOutputTokens": 512,
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}}},
        "systemInstruction": {"parts": [{"text": prompt}]},
        "inputAudioTranscription": {}, "outputAudioTranscription": {},
        "realtimeInputConfig": {"automaticActivityDetection": {"silenceDurationMs": 350}},
    }
    now = datetime.now(timezone.utc)
    payload = {"uses": 1,
        "expireTime": (now + timedelta(minutes=3)).isoformat(),
        "newSessionExpireTime": (now + timedelta(seconds=60)).isoformat(),
        "bidiGenerateContentSetup": setup}
    request = Request("https://generativelanguage.googleapis.com/" + api_version + "/auth_tokens",
        data=json.dumps(payload).encode(), headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    with urlopen(request, timeout=15) as response:
        token = json.load(response)["name"]
    return {"token": token, "setup": setup, "apiVersion": api_version, "maxSeconds": 170}


def reserve(client):
    # Shared across backend workers; bounded public voice-demo budget.
    database = FOLDER / "live-quota.sqlite3"
    now = int(time.time())
    identity = hashlib.sha256(client.encode()).hexdigest()
    with sqlite3.connect(database, timeout=3, isolation_level=None) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS calls (client TEXT, at INTEGER)")
        db.execute("DELETE FROM calls WHERE at < ?", (now - 3600,))
        total = db.execute("SELECT count(*) FROM calls").fetchone()[0]
        personal = db.execute("SELECT count(*) FROM calls WHERE client = ?", (identity,)).fetchone()[0]
        if total >= 20 or personal >= 4:
            db.rollback()
            return False
        db.execute("INSERT INTO calls VALUES (?, ?)", (identity, now))
        db.commit()
    return True


class LiveGateway:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] != ROUTE:
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        origin = headers.get("origin", "")
        cors = [(b"cache-control", b"no-store"), (b"vary", b"Origin")]
        if origin == ORIGIN:
            cors += [(b"access-control-allow-origin", ORIGIN.encode()),
                (b"access-control-allow-methods", b"GET, POST, OPTIONS"),
                (b"access-control-allow-headers", b"Content-Type"),
                (b"access-control-max-age", b"600")]

        async def respond(status, data):
            body = json.dumps(data).encode()
            await send({"type": "http.response.start", "status": status,
                "headers": cors + [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
            await send({"type": "http.response.body", "body": body})

        if scope["method"] == "GET":
            return await respond(200, {"ready": (FOLDER / "live-model").is_file(), "version": 1})
        if origin != ORIGIN:
            return await respond(403, {"error": "origin_not_allowed"})
        if scope["method"] == "OPTIONS":
            return await respond(204, {})
        if scope["method"] != "POST":
            return await respond(405, {"error": "method_not_allowed"})
        body = b""
        try:
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body += message.get("body", b"")
                if len(body) > 1024:
                    return await respond(413, {"error": "body_too_large"})
                if not message.get("more_body"):
                    break
            language = json.loads(body).get("language", "en")
            if language not in ("en", "fr", "fa"):
                return await respond(400, {"error": "invalid_language"})
            # Nginx sets X-Real-IP from the direct peer; ignore spoofable forwarded chains.
            client = headers.get("x-real-ip") or (scope.get("client") or ("unknown",))[0]
            if not await asyncio.to_thread(reserve, client):
                return await respond(429, {"error": "voice_demo_limit", "retryAfter": 3600})
            session = await asyncio.wait_for(asyncio.to_thread(mint, language), timeout=18)
            return await respond(200, session)
        except HTTPError as error:
            return await respond(502, {"error": "voice_provider_unavailable", "providerStatus": error.code})
        except Exception:
            return await respond(503, {"error": "voice_session_unavailable"})
'''


def atomic(path, content, mode=0o644):
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def docker(*args):
    result = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError('Docker operation failed: ' + args[0])
    return result.stdout


def api(key, version, endpoint, payload=None):
    request = Request('https://generativelanguage.googleapis.com/' + version + '/' + endpoint,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
    with urlopen(request, timeout=25) as response:
        return json.load(response)



def probe_live(version, token, setup):
    """Verify the actual provider WebSocket setup without opening a microphone."""
    host = 'generativelanguage.googleapis.com'
    path = '/ws/google.ai.generativelanguage.' + version + '.GenerativeService.BidiGenerateContentConstrained?access_token=' + quote(token, safe='')
    nonce = base64.b64encode(os.urandom(16)).decode()
    with socket.create_connection((host, 443), timeout=15) as raw:
        with ssl.create_default_context().wrap_socket(raw, server_hostname=host) as connection:
            connection.settimeout(15)
            connection.sendall(('GET ' + path + ' HTTP/1.1\r\nHost: ' + host + '\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ' + nonce + '\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
            received = b''
            while b'\r\n\r\n' not in received:
                part = connection.recv(1)
                if not part or len(received) > 16384:
                    return False
                received += part
            expected = base64.b64encode(hashlib.sha1((nonce + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
            if b' 101 ' not in received.split(b'\r\n', 1)[0] or expected.lower().encode() not in received.lower():
                return False
            def send_frame(payload, opcode=1):
                mask = os.urandom(4)
                length = len(payload)
                header = bytes([0x80 | opcode, 0x80 | length]) if length < 126 else bytes([0x80 | opcode, 0xfe]) + struct.pack('!H', length)
                connection.sendall(header + mask + bytes(value ^ mask[i % 4] for i, value in enumerate(payload)))
            def exact(length):
                data = b''
                while len(data) < length:
                    part = connection.recv(length - len(data))
                    if not part:
                        raise RuntimeError('WebSocket closed')
                    data += part
                return data
            send_frame(json.dumps({'setup': setup}).encode())
            fragments = b''
            for _ in range(12):
                first, second = exact(2)
                opcode = first & 15
                length = second & 127
                if length == 126:
                    length = struct.unpack('!H', exact(2))[0]
                elif length == 127:
                    length = struct.unpack('!Q', exact(8))[0]
                if length > 1048576 or second & 128:
                    return False
                payload = exact(length)
                if opcode == 8:
                    return False
                if opcode == 9:
                    send_frame(payload, 10)
                    continue
                if opcode in (0, 1, 2):
                    fragments += payload
                    if first & 128:
                        message = json.loads(fragments)
                        fragments = b''
                        if 'setupComplete' in message:
                            send_frame(b'', 8)
                            return True
                        if 'error' in message:
                            return False
            return False


def main():
    if not ROOT.is_dir() or not MAIN.is_file() or not KEY.is_file():
        raise SystemExit('Existing backend or saved Gemini key was not found. No changes made.')
    key = KEY.read_text().strip()
    print('1/4 Checking available Live models and constrained tokens...')
    selected = None
    for version in ('v1beta', 'v1alpha'):
        try:
            catalog = api(key, version, 'models').get('models', [])
            models = [m['name'] for m in catalog if any('bidigeneratecontent' in v.lower() for v in m.get('supportedGenerationMethods', [])) and 'transcrib' not in m['name'] and 'translat' not in m['name']]
            models.sort(key=lambda name: ('native-audio' in name, 'flash' in name, name), reverse=True)
            for model in models[:4]:
                now = datetime.now(timezone.utc)
                setup = {'model': model, 'generationConfig': {'responseModalities': ['AUDIO'], 'maxOutputTokens': 512, 'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': 'Kore'}}}}, 'systemInstruction': {'parts': [{'text': 'You are MadiTech assistant. Reply briefly.'}]}, 'inputAudioTranscription': {}, 'outputAudioTranscription': {}, 'realtimeInputConfig': {'automaticActivityDetection': {'silenceDurationMs': 350}}}
                try:
                    result = api(key, version, 'auth_tokens', {'uses': 1, 'expireTime': (now + timedelta(minutes=3)).isoformat(), 'newSessionExpireTime': (now + timedelta(seconds=60)).isoformat(), 'bidiGenerateContentSetup': setup})
                    if result.get('name') and probe_live(version, result['name'], setup):
                        selected = (version, model)
                        break
                except (HTTPError, OSError, ValueError, RuntimeError):
                    continue
            if selected:
                break
        except HTTPError:
            continue
    if not selected:
        raise SystemExit('Google did not accept a constrained Live session for this key. No application files changed. Check Live API access/billing in AI Studio.')
    version, model = selected
    print('Google verified the Live WebSocket session:', model)
    original = MAIN.read_text()
    ast.parse(original)
    inspection = docker('exec', 'amm_backend', 'python', '-c', "import json, app.main; from fastapi import FastAPI; print('__MADITECH_APP__'+json.dumps([name for name,value in vars(app.main).items() if isinstance(value,FastAPI)]))")
    records = [line.split('__MADITECH_APP__', 1)[1] for line in inspection.splitlines() if '__MADITECH_APP__' in line]
    app_names = json.loads(records[-1]) if records else []
    if len(app_names) != 1 or not app_names[0].isidentifier():
        raise SystemExit('Could not identify the backend FastAPI app. No files changed.')
    marker = '# MADITECH_LIVE_VOICE_GATEWAY'
    modified = original if marker in original else original + '\n' + marker + '\nfrom app.infrastructure.ai.maditech_live_gateway import LiveGateway\n' + app_names[0] + '.add_middleware(LiveGateway)\n'
    compile(modified, str(MAIN), 'exec')
    compile(GATEWAY_CODE, str(GATEWAY), 'exec')
    uid, gid = map(int, docker('exec', 'amm_backend', 'python', '-c', 'import os; print(os.geteuid(), os.getegid())').strip().split())
    private = ROOT / '.maditech-private'
    if not private.is_dir():
        raise SystemExit('Private backend config is missing. No files changed.')
    backup = Path('/root/maditech-backups') / ('live-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True, mode=0o700)
    shutil.copy2(MAIN, backup / 'main.py')
    targets = [GATEWAY, private / 'live-model', private / 'live-version']
    previous = {path: (path.read_bytes(), path.stat().st_mode & 0o777) if path.exists() else None for path in targets}
    print('2/4 Installing the gateway. Backup:', backup)
    try:
        atomic(GATEWAY, GATEWAY_CODE)
        for path, value in ((private / 'live-model', model), (private / 'live-version', version)):
            atomic(path, value, 0o600)
            os.chown(path, uid, gid)
        atomic(MAIN, modified, MAIN.stat().st_mode & 0o777)
        docker('exec', 'amm_backend', 'python', '-c', 'from app.main import app; from app.infrastructure.ai.maditech_live_gateway import LiveGateway')
        print('3/4 Restarting backend...')
        docker('restart', 'amm_backend')
        ready = False
        for _ in range(40):
            try:
                with urlopen('http://127.0.0.1:8000' + PATH, timeout=2) as response:
                    ready = bool(json.load(response).get('ready'))
                if ready:
                    break
            except Exception:
                pass
            time.sleep(1)
        if not ready:
            raise RuntimeError('Gateway did not become ready')
        print('4/4 Checking HTTPS, browser access and token creation...')
        request = Request('https://maditech.ddns.net' + PATH, data=b'{"language":"fa"}', headers={'Origin': ORIGIN, 'Content-Type': 'application/json'})
        with urlopen(request, timeout=25) as response:
            session = json.load(response)
            if response.headers.get('Access-Control-Allow-Origin') != ORIGIN or not session.get('token'):
                raise RuntimeError('Public gateway check failed')
        print('SUCCESS: Live voice gateway is installed. Refresh the MadiTech site; the Live voice button will appear.')
        print('Each demo session lasts under 3 minutes; limited to 4 sessions per IP and 20 total per hour.')
        print('Google Live usage may consume your API quota or billing. No permanent API key is sent to the browser.')
    except Exception:
        shutil.copy2(backup / 'main.py', MAIN)
        for path, value in previous.items():
            if value is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(value[0])
                path.chmod(value[1])
                if path.parent == private:
                    os.chown(path, uid, gid)
        docker('restart', 'amm_backend')
        raise SystemExit('Live installation failed. Previous backend files restored. Backup: ' + str(backup))


if __name__ == '__main__':
    try:
        main()
    except HTTPError as error:
        raise SystemExit('Google HTTP ' + str(error.code) + '. Key is not printed.')
    except Exception as error:
        raise SystemExit('Stopped: ' + type(error).__name__ + '. Do not share your API key.')
