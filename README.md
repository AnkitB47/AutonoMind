# AutonoMind

This project contains a FastAPI backend and a Next.js frontend.

## Starting the backend

Make sure you launch the FastAPI application from `app/main.py` so that all routers are loaded:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Frontend configuration

The frontend detects the API URL at runtime. When `NEXT_PUBLIC_FASTAPI_URL` is
set (for example during local development) it will be used for server-side
requests. In production you can leave this variable unset and the frontend will
route `/api/*` requests through the Next.js server, which proxies to the local
FastAPI instance. To explicitly point to a remote API, set
`NEXT_PUBLIC_FASTAPI_URL` to your public RunPod proxy URL.

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
