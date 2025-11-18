# Build
docker build -t jarvis-assistant .

# Run (mount .env for security)
docker run -d \
  --name jarvis \
  --env-file .env \
  -p 8000:8000 \
  --restart unless-stopped \
  jarvis-assistant
