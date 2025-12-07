# django-autoapi

`django-autoapi` is a Django helper app that scans your project and uses OpenAI to auto-generate Django REST Framework serializers for your models.

It is designed for **classic Django projects that render HTML templates (HTML/CSS/JS, no React)** and want to quickly become an API backend for React, mobile apps, or other frontends.  
You can also run a **budget check** first to estimate OpenAI token cost before generating anything.

---

## Features

- 🔍 Scan installed Django apps and list their models.
- 🤖 Use OpenAI to generate `ModelSerializer` classes into `<app>/api_serializers_ai.py`.
- 💰 `--budget-only` mode: estimate rough token usage and approximate cost before calling the API.
- ⚙️ Optional settings to include or exclude specific apps.

---

## Installation

1. **Copy the app into your Django project**

   Copy the `django_auto_api` folder into your Django project root  
   (same level as `manage.py`, next to your other apps).

2. **Install dependencies**

   ```bash
   pip install openai djangorestframework
   ```

3. **Add to `INSTALLED_APPS`**

   In your `settings.py`:

   ```python
   INSTALLED_APPS = [
       # ...
       "rest_framework",
       "django_auto_api",
   ]
   ```

4. **Set your OpenAI API key**

   Edit `django_auto_api/llm_client.py` and set:

   ```python
   # django_auto_api/llm_client.py
   API_KEY = "sk-xxxx_your_real_key_here"
   ```

   (Alternatively, you can set an environment variable `OPENAI_API_KEY`, but for now pasting into `API_KEY` is enough.)

---

## Optional settings (`DJANGO_AUTO_API`)

In `settings.py` you can control which apps are scanned:

```python
DJANGO_AUTO_API = {
    # Only scan these apps (by app label). If None → scan all non-contrib apps.
    "INCLUDE_APPS": None,   # e.g. ["blog", "orders"]

    # Apps to skip even if they are installed.
    "EXCLUDE_APPS": [],
}
```

Examples:

- **Default (no setting):** scan all non-`django.contrib` apps.
- **Only scan `blog` and `orders`:**

  ```python
  DJANGO_AUTO_API = {
      "INCLUDE_APPS": ["blog", "orders"],
  }
  ```

---

## Usage

Run these commands from your Django project root (where `manage.py` is).

### 1. Budget-only (no OpenAI calls)

Estimate how much it will cost before generating serializers:

```bash
python manage.py autoapi_scan --budget-only
```

This will:

- Scan apps and models  
- Show how many models will be processed  
- Print a rough estimate of tokens and cost (e.g. using `gpt-4o-mini`)

No API requests are made in this mode.

---

### 2. Generate serializers for all models

Generate `ModelSerializer` classes using OpenAI:

```bash
python manage.py autoapi_scan
```

You’ll see a list of apps and models, then a question like:

```text
Generate serializers for X models using OpenAI? [y/N]:
```

Type `y` to proceed.

For each app, `django-autoapi` will:

- Create `<app>/api_serializers_ai.py` if it does not exist
- Append a `ModelSerializer` for each model

---

### 3. Extra options

- Only process one app:

  ```bash
  python manage.py autoapi_scan --app blog
  ```

- Only generate for one model (e.g. `Post`):

  ```bash
  python manage.py autoapi_scan --model Post
  ```

- Skip the confirmation prompt:

  ```bash
  python manage.py autoapi_scan --yes
  ```

You can combine options, for example:

```bash
python manage.py autoapi_scan --app blog --model Post --yes
```

---

## How it works (high level)

1. `autoapi_scan` uses `django.apps.get_app_configs()` to discover apps and models.
2. For each model, it collects field metadata (name + type).
3. It builds a prompt and sends it to OpenAI via `llm_client.generate_code()`.
4. The returned Python code is appended to `<app>/api_serializers_ai.py`.
5. In `--budget-only` mode, it only estimates tokens and cost without calling the API.

---

## Roadmap

Planned features:

- Generate `ModelViewSet` classes and DRF routers.
- Generate OpenAPI schema and AI-enriched endpoint docs (descriptions, examples).
- Export docs to Markdown / HTML / PDF.
- Publish as a real package: `pip install django-autoapi`.

---

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.
