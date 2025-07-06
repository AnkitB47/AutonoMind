# AutonoMind

This project contains a FastAPI backend and a Next.js frontend with seamless communication.

## Architecture

The application uses a unified API architecture where:
- Next.js frontend proxies `/api/*` requests to FastAPI backend (port 8000)
- File uploads go to `/api/upload` and are processed by `agents/rag_agent.process_file`
- Chat messages stream through `/api/chat` and call `agents/rag_agent.handle_query`
- RAG answers are post-processed via `rewrite_answer()` for conciseness
- All responses include `X-Source` and `X-Session-ID` headers

## Starting the backend

Make sure you launch the FastAPI application from `app/main.py` so that all routers are loaded:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The server exposes a `/ping` endpoint for simple health checks and `/debug-env` for environment verification.

## Frontend configuration

The frontend discovers the backend URL at runtime using the following priority:
1. `window.RUNTIME_FASTAPI_URL` (set by `entrypoint.sh` at runtime)
2. `process.env.NEXT_PUBLIC_FASTAPI_URL` (build-time environment)
3. `/api` (development proxy fallback)

The `entrypoint.sh` script writes `webapp/public/env.js` containing `window.RUNTIME_FASTAPI_URL` which points to the FastAPI service. During development, Next.js proxies `/api/*` to your local backend, while in production the app fetches this runtime variable.

If `RUNPOD_POD_ID` is present the entrypoint derives the URL as `https://$RUNPOD_POD_ID-8000.proxy.runpod.net` and exports `NEXT_PUBLIC_FASTAPI_URL` for server‑side rendering.

## Development

For local development, the frontend will automatically proxy API calls to the backend:

```bash
# Terminal 1: Start FastAPI backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Next.js frontend
cd webapp
npm run dev
```

The frontend will be available at `http://localhost:3000` and will proxy `/api/*` requests to the FastAPI backend.

## Production Deployment

### Fly.io Deployment

Example Fly deployment with proper FastAPI URL configuration:

```bash
fly deploy --build-arg NEXT_PUBLIC_FASTAPI_URL=https://your-app.fly.dev \
  -e NEXT_PUBLIC_FASTAPI_URL=https://your-app.fly.dev
```

**Important:** Do not append `:3000` to the public URL. The Fly proxy maps incoming traffic on ports 80 and 443 to the container's internal port 3000, so your frontend is available directly at `https://your-app.fly.dev`.

### Docker Deployment

The Dockerfiles accept the `NEXT_PUBLIC_FASTAPI_URL` build argument:

```bash
docker build --build-arg NEXT_PUBLIC_FASTAPI_URL=https://your-domain.com \
  -f docker/Dockerfile.cpu -t autonomind .
```

## API Endpoints

### File Upload
- `POST /api/upload` - Upload PDFs or images for RAG processing
- `POST /api/debug-upload` - Debug endpoint for troubleshooting uploads

### Chat
- `POST /api/chat` - Stream chat messages with RAG processing
- Supports modes: `text`, `voice`, `image`, `search`

### Health & Debug
- `GET /api/ping` - Health check
- `GET /api/debug-env` - Environment verification
- `POST /api/debug-chat` - Chat endpoint verification
- `GET /api/debug-connection` - Connection details

## Session Management

Each chat session has a unique `session_id` that:
- Is automatically generated if not provided
- Remains valid for approximately 1 hour
- Links uploaded files to chat conversations
- Is returned in response headers as `X-Session-ID`

## File Processing

Uploaded files are processed as follows:
- **PDFs**: Text extraction, chunking, and vector storage
- **Images**: OCR text extraction and CLIP similarity indexing
- **Audio**: Whisper transcription to text

All processed content is stored in vector databases for semantic search and retrieval.

## Environment Variables

- `NEXT_PUBLIC_FASTAPI_URL`: Backend URL for client-side requests
- `MIN_CONFIDENCE`: Minimum confidence threshold for RAG results
- `GEMINI_API_KEY`: Required for image processing and text summarization
- `OPENAI_API_KEY`: Required for chat completions
- `PINECONE_API_KEY`: Required for vector storage (optional)

## Testing

Run the test suite to verify all endpoints work correctly:

```bash
pytest tests/test_endpoints.py -q
```

Test API connectivity manually:

```bash
node test_api_connectivity.js http://localhost:3000
```

Run comprehensive production tests:

```bash
node test_production_api.js https://your-app.fly.dev
```

## Production Troubleshooting

### Upload Failures (ECONNRESET)

If file uploads fail in production with "Failed to fetch" or ECONNRESET:

1. **Check FastAPI startup logs**:
   ```bash
   fly logs | grep "FastAPI started successfully"
   ```

2. **Verify Uvicorn configuration**:
   - Ensure `--proxy-headers` and `--timeout-keep-alive=75` are set
   - Check that FastAPI is fully ready before Next.js starts

3. **Test upload endpoint directly**:
   ```bash
   curl -X POST -F "file=@test.pdf" -F "session_id=test" https://your-app.fly.dev/api/debug-upload
   ```

4. **Check file size limits**:
   - PDFs: 50MB maximum
   - Images: 10MB maximum

### Chat Hanging "Thinking..."

If chat hangs indefinitely:

1. **Check FastAPI logs for errors**:
   ```bash
   fly logs | grep "rag_agent"
   ```

2. **Verify session management**:
   ```bash
   curl https://your-app.fly.dev/api/debug-env
   ```

3. **Test chat endpoint**:
   ```bash
   curl -X POST https://your-app.fly.dev/api/debug-chat
   ```

### Common Production Issues

- **Race conditions**: FastAPI must be fully ready before Next.js starts
- **File size limits**: Large files may timeout without proper configuration
- **Memory issues**: PDF processing can be memory-intensive
- **Network timeouts**: RunPod proxy has connection limits

### Debug Commands

```bash
# Check if FastAPI is responding
curl http://localhost:8000/ping

# Test Next.js proxy
curl http://localhost:3000/api/ping

# Verify environment
curl http://localhost:3000/api/debug-env

# Test file upload
curl -X POST -F "file=@test.pdf" -F "session_id=test" http://localhost:3000/api/debug-upload

# Check connection details
curl http://localhost:3000/api/debug-connection

# Production verification
curl https://your-app.fly.dev/api/ping
curl https://your-app.fly.dev/api/debug-env
```

### Log Analysis

Key log patterns to monitor:

- `✅ FastAPI started successfully on port 8000`
- `✅ Upload endpoint verified`
- `Upload request: filename=... size=... session_id=...`
- `Processing file: ... for session: ...`
- `Upload successful: ... for session: ...`

### Performance Optimization

- **File size limits**: Enforce client-side file size validation
- **Concurrent uploads**: Limit to 1 upload at a time
- **Memory monitoring**: Watch for memory leaks in PDF processing
- **Connection pooling**: Uvicorn handles multiple concurrent requests
