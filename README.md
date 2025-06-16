# AutonoMind

This project contains a FastAPI backend and a Next.js frontend.

## Starting the backend

Make sure you launch the FastAPI application from `app/main_fastapi.py` so that all routers are loaded:

```bash
uvicorn app.main_fastapi:app --host 0.0.0.0 --port 8000
```

## Frontend configuration

The frontend detects the API URL at runtime. When `NEXT_PUBLIC_FASTAPI_URL` is
set (for example during local development) it will be used for server-side
requests. In production you can leave this variable unset and the frontend will
route `/api/*` requests through the Next.js server, which proxies to the local
FastAPI instance. To explicitly point to a remote API, set
`NEXT_PUBLIC_FASTAPI_URL` to your public RunPod proxy URL.

```bash
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000 npm run dev
```

A sample `.env` file is provided at `webapp/.env.example`.

## Using the API manually

Remember that text, voice and image inputs share the `/input` prefix:

- `POST /input/text`
- `POST /input/voice`
- `POST /input/image`

Text or voice messages that mention terms like "pdf" or "image" trigger the RAG
pipeline to search any uploaded files. Queries without those keywords fall back
to the web search agent.

Upload PDFs or images for retrieval using `POST /upload` and send chat messages via `POST /chat`.
If the request omits a `session_id`, the server now generates a new one automatically.
