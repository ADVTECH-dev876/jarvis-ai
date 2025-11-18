import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import speech_recognition as sr
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from openai import AsyncOpenAI
from pydantic import BaseModel
from dateutil import parser as date_parser
import requests

# ============================
# CONFIGURATION
# ============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SMART_HOME_URL = os.getenv("SMART_HOME_URL", "http://homeassistant.local:8123/api")
SMART_HOME_TOKEN = os.getenv("SMART_HOME_TOKEN")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# In-memory session context (in real app: use Redis or DB)
session_context: Dict[str, List[Dict]] = {}

# ============================
# API INTEGRATIONS (stubs - expand as needed)
# ============================

async def create_calendar_event(summary: str, start_time: str):
    """Integrate with Google Calendar API or CalDAV"""
    # Your real integration here
    print(f"[ACTION] Creating calendar event: '{summary}' at {start_time}")
    return {"status": "scheduled", "event": summary, "time": start_time}

async def toggle_smart_device(device_id: str, state: str):
    """Control smart home via Home Assistant REST API"""
    headers = {
        "Authorization": f"Bearer {SMART_HOME_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"entity_id": device_id, "state": state}
    try:
        response = requests.post(
            f"{SMART_HOME_URL}/services/homeassistant/turn_{state}",
            headers=headers,
            json=payload,
            timeout=10,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

async def query_knowledge(query: str):
    """Search internal docs or web via your RAG system or SerpAPI"""
    return f"Result for: {query}"

# ============================
# INTENT ROUTER & EXECUTOR
# ============================

async def route_and_execute(intent: str, params: dict, user_id: str = "default"):
    """Map parsed intent to action using real APIs"""
    intent = intent.lower()
    
    if "schedule" in intent or "calendar" in intent:
        time = params.get("time") or params.get("when")
        summary = params.get("event") or params.get("summary") or "Unnamed event"
        if not time:
            return {"clarify": "When would you like to schedule this?"}
        parsed_time = date_parser.parse(time).isoformat()
        return await create_calendar_event(summary, parsed_time)

    elif "turn on" in intent or "turn off" in intent:
        device = params.get("device")
        state = "on" if "turn on" in intent else "off"
        if not device:
            return {"clarify": "Which device would you like to control?"}
        # Assume device mapping (e.g., "lights" → "light.living_room")
        device_map = {"lights": "light.living_room", "ac": "climate.ac_unit"}
        entity_id = device_map.get(device.lower(), f"switch.{device}")
        return await toggle_smart_device(entity_id, state)

    elif "search" in intent or "look up" in intent:
        query = params.get("query") or intent
        return await query_knowledge(query)

    else:
        return {"response": "I can help with scheduling, smart home control, or information lookup. Could you clarify?"}

# ============================
# LLM PROMPT FOR INTENT PARSING
# ============================

INTENT_PROMPT = """
You are JARVIS, a calm, professional AI assistant. Parse the user's request into structured intent and parameters.
Respond ONLY in valid JSON with keys: "intent", "parameters".
Parameters should include: event, time, device, query, etc. as applicable.
If unclear, set "intent": "clarify" and include a "question".

Examples:
- "Schedule a meeting with Alex tomorrow at 3 PM" → {"intent": "schedule", "parameters": {"event": "Meeting with Alex", "time": "tomorrow at 3 PM"}}
- "Turn on the lights" → {"intent": "control_device", "parameters": {"device": "lights", "action": "on"}}
- "What's the weather?" → {"intent": "search", "parameters": {"query": "current weather"}}
- "Remind me..." → {"intent": "schedule", ...}

User: {user_input}
"""

async def parse_intent(user_input: str) -> dict:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": INTENT_PROMPT.format(user_input=user_input)}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"intent": "error", "parameters": {"error": str(e)}}

# ============================
# MAIN ASSISTANT LOGIC
# ============================

async def process_request(user_input: str, user_id: str = "default") -> dict:
    # Update context
    if user_id not in session_context:
        session_context[user_id] = []
    session_context[user_id].append({"role": "user", "content": user_input})

    # Parse intent
    parsed = await parse_intent(user_input)
    intent = parsed.get("intent")
    params = parsed.get("parameters", {})

    if intent == "clarify":
        return {"response": parsed.get("question", "Could you clarify?")}

    # Execute action
    result = await route_and_execute(intent, params, user_id)

    # Store assistant response
    response_text = result.get("response") or f"Done: {intent}"
    session_context[user_id].append({"role": "assistant", "content": response_text})

    return {"response": response_text}

# ============================
# FASTAPI + WEBSOCKET (Web + Voice Interface)
# ============================

app = FastAPI(title="JARVIS AI Assistant")

@app.get("/", response_class=HTMLResponse)
async def ui():
    return """
    <html>
    <body>
        <h2>JARVIS Assistant</h2>
        <button onclick="startListening()">Speak</button>
        <div id="output"></div>
        <script>
            async function startListening() {
                const res = await fetch('/voice');
                const data = await res.json();
                document.getElementById('output').innerText = data.response;
            }
        </script>
    </body>
    </html>
    """

@app.get("/voice")
async def voice_command():
    """Simulate voice input via microphone (for local dev)"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source, timeout=5, phrase_time_limit=10)
    try:
        text = r.recognize_google(audio)
        print(f"User said: {text}")
        result = await process_request(text)
        return result
    except Exception as e:
        return {"response": "Sorry, I didn't catch that."}

@app.post("/text")
async def text_command(request: Request):
    data = await request.json()
    result = await process_request(data["message"])
    return result

# Optional: WebSocket for real-time streaming (advanced)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        result = await process_request(data)
        await websocket.send_text(result["response"])
