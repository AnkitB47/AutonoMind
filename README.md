# AutonoMind

This project contains a FastAPI backend, a Streamlit dashboard, and a Next.js frontend.

## Starting the backend

Make sure you launch the FastAPI application from `app/main_fastapi.py` so that all routers are loaded:

```bash
uvicorn app.main_fastapi:app --host 0.0.0.0 --port 8000
```

Starting `gpu_server.py` or `app/main_streamlit.py` directly exposes only utility endpoints and will return `404` for the rest.

## Frontend configuration

The frontend detects the API URL at runtime. When `NEXT_PUBLIC_FASTAPI_URL` is
set (for example during local development) it will be used for server-side
requests. In the browser, the frontend falls back to the origin that served the
page.

```bash
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000 npm run dev
```

A sample `.env` file is provided at `webapp/.env.example`.

## Using the API manually

Remember that text, voice, image and search endpoints are grouped under the `/input` prefix:

- `POST /input/text`
- `POST /input/voice`
- `POST /input/image`
- `POST /input/search`

With the correct entry point and base URL, these routes should respond without 404 errors.
