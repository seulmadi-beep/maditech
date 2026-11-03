#!/usr/bin/env python3
"""Read-only application diagnostics. Never prints API keys or session tokens."""
import inspect
import json
import re
import runpy
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from urllib.error import HTTPError

installer = runpy.run_path('/tmp/maditech-live-voice.py', run_name='diagnostic_import')
key = installer['KEY'].read_text().strip()
api = installer['api']


def safe(value):
    text = str(value).replace(key, '[HIDDEN]')
    text = re.sub(r'auth_tokens/[^\s"\'<>]+', '[TOKEN]', text)
    text = re.sub(r'(?:access_token|key)=[^\s&"\'<>]+', 'credential=[HIDDEN]', text)
    return text[:700]


def explain(error):
    if isinstance(error, HTTPError):
        print('HTTP:', error.code)
        try:
            details = json.load(error).get('error', {})
            print('Status:', safe(details.get('status', '')))
            print('Message:', safe(details.get('message', '')))
        except Exception:
            print('Error body not readable.')
    else:
        print('Connection:', type(error).__name__, safe(error))


# Use the same WebSocket implementation, exposing only safe failure reasons.
source = inspect.getsource(installer['probe_live'])
source = source.replace("if opcode == 8:\n                    return False", "if opcode == 8:\n                    raise RuntimeError('WebSocket close: ' + str(struct.unpack('!H', payload[:2])[0] if len(payload) >= 2 else 0) + ' ' + payload[2:].decode('utf-8', 'replace'))")
source = source.replace("if 'error' in message:\n                            return False", "if 'error' in message:\n                            raise RuntimeError('WebSocket error: ' + json.dumps(message['error']))")
source = source.replace("if b' 101 ' not in received.split(b'\\r\\n', 1)[0] or expected.lower().encode() not in received.lower():\n                return False", "if b' 101 ' not in received.split(b'\\r\\n', 1)[0] or expected.lower().encode() not in received.lower():\n                raise RuntimeError('WebSocket handshake: ' + received.split(b'\\r\\n', 1)[0].decode('utf-8', 'replace'))")
namespace = dict(installer['probe_live'].__globals__)
exec(compile(source, '<voice-diagnostic>', 'exec'), namespace)
probe = namespace['probe_live']

print('Diagnostic only: no application files or settings are changed.')
print('Checking all model catalog pages; no audio is recorded or generated.')
for version in ('v1beta', 'v1alpha'):
    print('\nAPI:', version)
    catalog = []
    page = None
    try:
        for _ in range(10):
            endpoint = 'models' + ('?' + urlencode({'pageToken': page}) if page else '')
            data = api(key, version, endpoint)
            catalog.extend(data.get('models', []))
            page = data.get('nextPageToken')
            if not page:
                break
    except Exception as error:
        explain(error)
        continue
    candidates = [m for m in catalog if (any('bidigeneratecontent' in str(method).lower() for method in m.get('supportedGenerationMethods', [])) or 'live' in m.get('name', '').lower() or 'native-audio' in m.get('name', '').lower()) and not any(word in m.get('name', '') for word in ('transcrib', 'translat', 'tts'))]
    print('Models listed:', len(catalog), '| Live candidates:', len(candidates), '| More pages:', bool(page))
    for model in candidates[:8]:
        print('Candidate:', model['name'], '| Methods:', ', '.join(model.get('supportedGenerationMethods', [])))
    if not candidates:
        print('No Live model was listed for this API/key.')
        continue
    for entry in candidates[:3]:
        name = entry['name']
        print('\nTesting:', name)
        for label, setup in (
            ('minimal', {'model': name, 'generationConfig': {'responseModalities': ['AUDIO']}}),
            ('site-config', {'model': name, 'generationConfig': {'responseModalities': ['AUDIO'], 'maxOutputTokens': 512, 'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': 'Kore'}}}}, 'systemInstruction': {'parts': [{'text': 'You are MadiTech assistant. Reply briefly.'}]}, 'inputAudioTranscription': {}, 'outputAudioTranscription': {}, 'realtimeInputConfig': {'automaticActivityDetection': {'silenceDurationMs': 350}}}),
        ):
            print('Config:', label)
            now = datetime.now(timezone.utc)
            try:
                token = api(key, version, 'auth_tokens', {'uses': 1, 'expireTime': (now + timedelta(minutes=3)).isoformat(), 'newSessionExpireTime': (now + timedelta(seconds=60)).isoformat(), 'bidiGenerateContentSetup': setup})
                if not token.get('name'):
                    print('No token returned. Fields:', ', '.join(token.keys()))
                    continue
                print('Token accepted; checking actual WebSocket setup...')
                print('WebSocket setup:', 'SUCCESS' if probe(version, token['name'], setup) else 'FAILED')
            except Exception as error:
                explain(error)
print('\nDiagnostic finished. Application files remain unchanged. Share this output, not your API key.')
