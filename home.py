export OPENAI_API_KEY="your-key"
export SMART_HOME_TOKEN="your-home-assistant-token"
uvicorn jarvis:app --reload --host 0.0.0.0 --port 8000
