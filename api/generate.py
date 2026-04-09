"""
CoachNote API - Vercel Python serverless function.
Receives game details, calls Claude API, returns parent message + practice plan.
"""

import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler


SYSTEM_PROMPT = """You are CoachNote, an AI assistant that helps youth sports coaches.
You write two outputs: a parent communication message and a structured practice plan.

Rules for PARENT MESSAGE:
- Warm, positive, brief (3-5 short paragraphs max)
- Start with the result (win/loss/tie) and acknowledge the effort
- Mention 2-3 specific highlights naturally (not as a bulleted list)
- Include ONE constructive growth area framed positively
- Mention player of the game if provided
- End with logistics (next practice/game) if provided
- Sign off as "Coach" (not the user's name - they can edit that)
- NO em dashes. Use commas or periods only.
- NO bullet points. Flowing prose paragraphs.
- Conversational parent-to-parent tone, not corporate.

Rules for PRACTICE PLAN:
- 60-minute session structured in clear blocks
- DIRECTLY target the weak areas mentioned in the input
- Format as:
  WARM-UP (10 min): [activity]
  SKILL BLOCK 1 (15 min): [drill targeting weakness 1]
  SKILL BLOCK 2 (15 min): [drill targeting weakness 2]
  SMALL-SIDED GAME (15 min): [game that reinforces both skills]
  COOL-DOWN + TALK (5 min): [what to emphasize]
- Each block: name of drill, coaching cue, what to watch for
- Keep language practical, not academic
- Age-appropriate language (assume U8-U14 unless specified)
- NO em dashes anywhere.

Return ONLY valid JSON with keys "parent_message" and "practice_plan". No markdown fences, no extra keys."""


def build_user_prompt(data):
    sport = data.get('sport', 'soccer')
    team = data.get('team', 'the team')
    our = data.get('our_score', '')
    their = data.get('their_score', '')
    opponent = data.get('opponent', '')
    went_well = data.get('went_well', '')
    work_on = data.get('work_on', '')
    potg = data.get('potg', '')
    next_event = data.get('next_event', '')
    tone = data.get('tone', 'warm and encouraging')

    score_str = ''
    if our and their:
        try:
            us, them = int(our), int(their)
            outcome = 'won' if us > them else ('lost' if us < them else 'tied')
            score_str = f'Result: {outcome} {our}-{their}'
            if opponent:
                score_str += f' against {opponent}'
        except ValueError:
            score_str = f'Score: {our}-{their}'
            if opponent:
                score_str += f' vs {opponent}'

    parts = [
        f'Sport: {sport}',
        f'Team: {team}',
    ]
    if score_str:
        parts.append(score_str)
    parts.append(f'What went well: {went_well}')
    parts.append(f'Areas to work on: {work_on}')
    if potg:
        parts.append(f'Player of the game: {potg}')
    if next_event:
        parts.append(f'Next event: {next_event}')
    parts.append(f'Message tone: {tone}')

    return '\n'.join(parts)


def call_claude(api_key, user_prompt):
    url = 'https://api.anthropic.com/v1/messages'
    payload = {
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 1200,
        'system': SYSTEM_PROMPT,
        'messages': [{'role': 'user', 'content': user_prompt}]
    }
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    return result['content'][0]['text']


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        api_key = self.headers.get('x-api-key', '').strip()
        if not api_key or not api_key.startswith('sk-ant-'):
            self._json_error(401, 'Invalid or missing API key. Key must start with sk-ant-.')
            return

        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode('utf-8'))
        except Exception:
            self._json_error(400, 'Invalid JSON body.')
            return

        if not data.get('went_well') or not data.get('work_on'):
            self._json_error(400, 'went_well and work_on are required.')
            return

        user_prompt = build_user_prompt(data)

        try:
            raw_text = call_claude(api_key, user_prompt)
        except urllib.error.HTTPError as e:
            code = e.code
            body = e.read().decode('utf-8', errors='replace')
            try:
                err_data = json.loads(body)
                msg = err_data.get('error', {}).get('message', body)
            except Exception:
                msg = body[:200]
            self._json_error(code, f'Claude API error ({code}): {msg}')
            return
        except Exception as e:
            self._json_error(500, f'Upstream error: {str(e)}')
            return

        # Parse the JSON Claude returns
        text = raw_text.strip()
        # Strip markdown fences if present
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object from text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                try:
                    result = json.loads(text[start:end])
                except Exception:
                    self._json_error(500, 'Claude returned malformed JSON. Try again.')
                    return
            else:
                self._json_error(500, 'Could not parse Claude response. Try again.')
                return

        if 'parent_message' not in result or 'practice_plan' not in result:
            self._json_error(500, 'Incomplete response from Claude. Try again.')
            return

        self.send_response(200)
        self._set_cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode('utf-8'))

    def _set_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-api-key')

    def _json_error(self, code, message):
        self.send_response(code)
        self._set_cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode('utf-8'))

    def log_message(self, format, *args):
        pass  # silence default logging
