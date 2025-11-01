# ShopAssistAI

ShopAssistAI is a lightweight assistant for recommending and answering questions about laptops. It combines a small Flask web front-end with prompt-driven AI steps for:

- capturing structured user requirements,
- mapping product descriptions to structured feature profiles,
- comparing user requirements to products and ranking recommendations,
- answering follow-up product detail questions using local CSV data and a web-search fallback.

This README explains how to set up, run, and troubleshoot the project.

## Features

- Requirements capture using an LLM-driven conversation
- Product mapping: convert free-text descriptions -> JSON feature profiles
- Recommendation pipeline: simple, interpretable matching and ranking
- Product detail lookup with local CSV lookup + web fallback
- A Flask endpoint for web clients

## Repository layout (key files)

- `main.py` — Flask app + chat endpoint (`/` and `/chat`).
- `requirements.txt` — Python dependencies.
- `data/` — `laptop_data.csv` (source dataset).
- `product_mapping/` — product mapping & recommendation logic (`product_mapping_agent.py`).
- `product_details/` — product detail toolchain (`product_details_agent.py`).
- `prompt_templates/` — system and user prompt templates.
- `utils/` — helper utilities (AI wrapper `ai_utils.py`, JSON helpers `json_utils.py`, etc.).
- `templates/` — HTML templates for Flask.
- `static/` — static assets used by the web UI.

## Requirements

- Python 3.10+ recommended
- A Python virtual environment (optional but recommended)
- OpenAI-compatible and LangSearch API key in `.env` file.

Install dependencies:

```powershell
# from repository root
python -m pip install -r requirements.txt
```

If `python-dotenv` import fails, run:

```powershell
pip install python-dotenv
```

## Environment

Create a `.env` in the project root with at least the following:

```
OPENAI_API_KEY=your_api_key_here
LANGSEARCH_API_KEY=your_api_key_here
```

The project loads `.env` in `utils/ai_utils.py` (`load_dotenv('../.env')`) when running as a module; when running in a notebook you may want to call `load_dotenv()` from the notebook or ensure the working directory is set appropriately.

## Running the Flask app

From the project root (PowerShell):

```powershell
# set the FLASK_APP if needed and run
python -m flask --app main run
```

Open `http://127.0.0.1:5000/` in your browser.

### Chat endpoint

- `GET /chat?text=Hello` — returns JSON
- Clients sometimes call with a `callback` query parameter for JSONP (e.g. `?text=Hello&callback=chatux_...`). When `callback` is present, the server returns JSONP: `callback(JSON)`.

If you see a client-side error like `Uncaught SyntaxError: Unexpected token ':'` when requesting `/chat?callback=...`, the server is returning raw JSON while the client expects JSONP. The Flask route checks for `callback` and wraps the JSON response in the callback function name when needed.

## Utility functions to be aware of

- `utils/json_utils.py::is_strict_json_object(s)` — verifies the model's response is exactly a JSON object (strips markdown fences and checks there is no trailing text).
- `utils/ai_utils.py` — thin wrapper around the OpenAI client. Ensure `OPENAI_API_KEY` is available.
- `product_mapping/product_mapping_agent.py::get_available_products` — reads `data/laptop_data.csv` and populates a `laptop_feature_map` JSON column by calling the model when needed.

## Troubleshooting

- ImportError: `cannot import name 'load_dotenv' from 'dotenv'`
  - Install the correct package: `pip install python-dotenv`.
  - Restart your kernel or process after installing.

- Client JSONP error `Unexpected token ':'`
  - This happens when the client expects JSONP (a JavaScript function call) but receives raw JSON. Ensure the server wraps responses when `callback` is present:

```python
# Flask snippet
callback = request.args.get('callback')
if callback:
    return f"{callback}({jsonify(response).get_data(as_text=True)})"
return jsonify(response)
```

- OpenAI / API key errors
  - Verify `OPENAI_API_KEY` in `.env` and that `utils/ai_utils.py` loads environment variables correctly. If you see permission or API errors, check the key and your account limits.

## Example: quick test call to the Flask chat endpoint (PowerShell)

```powershell
# Raw JSON call
Invoke-RestMethod "http://127.0.0.1:5000/chat?text=Hello"

# JSONP-style call (client expects JSONP)
# This will return JavaScript like: callback({...})
Invoke-RestMethod "http://127.0.0.1:5000/chat?text=Hello&callback=chatux_test"
```

## License & attribution

This project is provided "as-is" for educational use. Add your preferred license if you intend to publish it.
