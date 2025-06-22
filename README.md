# AutonoMind

This project contains a FastAPI backend and a Next.js frontend.

## Starting the backend

Make sure you launch the FastAPI application from `app/main.py` so that all routers are loaded:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
The server exposes a `/ping` endpoint for simple health checks.

## Frontend configuration

The frontend reads `NEXT_PUBLIC_FASTAPI_URL` for all API requests. In
development you can point this at your local FastAPI instance. In production it
**must** be the public RunPod/Fly URL of your backend; otherwise the browser
will try to call `http://localhost:8000`.

In production the backend also checks that either `RUNPOD_URL` or
`NEXT_PUBLIC_FASTAPI_URL` is configured. If neither is set the server will fail
to start.

All calls go through the `/api` path which Next.js rewrites to
`NEXT_PUBLIC_FASTAPI_URL` at runtime. When building the Docker image pass this
value as a build argument and also set it at runtime so `next start` exposes the
correct base URL.

Example Fly deployment:

**Do not append `:3000` to the public URL.** The Fly proxy maps
incoming traffic on ports 80 and 443 to the container's internal port 3000,
so your frontend is available directly at `https://your-app.fly.dev`.

```bash
fly deploy --build-arg NEXT_PUBLIC_FASTAPI_URL=https://your-app.fly.dev \
  -e NEXT_PUBLIC_FASTAPI_URL=https://your-app.fly.dev
```

When `RUNPOD_URL` is configured on the backend, heavy tasks like audio
transcription and image OCR will be delegated to that remote pod.

The container exposes `/ping` on port 8000 which can be used for health checks
before starting the frontend.

Example Fly deployment:

**Do not append `:3000` to the public URL.** The Fly proxy maps
incoming traffic on ports 80 and 443 to the container's internal port 3000,
so your frontend is available directly at `https://your-app.fly.dev`.

```bash
fly deploy --build-arg NEXT_PUBLIC_FASTAPI_URL=https://your-app.fly.dev \
  -e NEXT_PUBLIC_FASTAPI_URL=https://your-app.fly.dev
```

When `RUNPOD_URL` is configured on the backend, heavy tasks like audio
transcription and image OCR will be delegated to that remote pod.

```bash
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000 npm run dev
```

A sample `.env` file is provided at `webapp/.env.example`.

## Using the API manually

Remember that text, voice and image inputs share the `/input` prefix:

- `POST /input/text`
- `POST /input/voice`
- `POST /input/image`

`/input/text` and `/input/search` run a regular web search for the given query.
`/input/voice` returns the transcribed text of the uploaded audio file.
Use `/chat` to question any PDFs or images you've uploaded previously.

Upload PDFs or images for retrieval using `POST /upload` and send chat messages via `POST /chat`.
If the request omits a `session_id`, the server now generates a new one automatically and
returns it in the response. Keep this id and include it in later requests so your uploaded
files can be queried. Each session id remains valid for roughly an hour.

Images uploaded for CLIP similarity search are stored under the `/images`
path exposed by the API. Results returned by `/search/image-similarity` use
these URLs so they can be viewed directly in the browser.
When you POST an image to `/chat`, the server now tries an image similarity
lookup first and only falls back to OCR-based search when no strong match is
found.
