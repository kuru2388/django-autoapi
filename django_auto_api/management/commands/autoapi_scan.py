# django_auto_api/management/commands/autoapi_scan.py
from pathlib import Path

from django.core.management.base import BaseCommand
from django.apps import apps as django_apps

from django_auto_api.config import get_config
from django_auto_api.llm_client import generate_code, OpenAIConfigError
from django_auto_api.prompts import build_serializer_prompt


class Command(BaseCommand):
    help = (
        "Scan installed apps and list their models, then optionally use OpenAI to "
        "generate DRF ModelSerializers into <app>/api_serializers_ai.py "
        "(respects DJANGO_AUTO_API settings)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            dest="app_label",
            help="Optional: only show / generate for this app label (e.g. 'blog').",
        )
        parser.add_argument(
            "--include-empty",
            action="store_true",
            help="Include apps that have no models in the scan output.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip interactive confirmation before generation.",
        )
        parser.add_argument(
            "--model",
            dest="model_name",
            help="Optional: only generate for this single model name (for testing).",
        )
        parser.add_argument(
            "--budget-only",
            action="store_true",
            help="Only show estimated token usage and API cost, do not call OpenAI.",
        )

    def handle(self, *args, **options):
        cfg = get_config()
        app_label_filter = options.get("app_label")
        include_empty = options.get("include_empty")
        skip_confirm = options.get("yes")
        model_name_filter = options.get("model_name")
        budget_only = options.get("budget_only")

        include_apps = cfg.get("INCLUDE_APPS")
        exclude_apps = set(cfg.get("EXCLUDE_APPS") or [])

        self.stdout.write(self.style.NOTICE("🔍 Scanning installed apps...\n"))

        # Collect app configs (skip contrib by default)
        all_app_configs = [
            app
            for app in django_apps.get_app_configs()
            if not app.name.startswith("django.contrib")
        ]

        # Apply INCLUDE_APPS filter from settings (if provided)
        if include_apps:
            include_set = set(include_apps)
            app_configs = [app for app in all_app_configs if app.label in include_set]
        else:
            app_configs = all_app_configs

        # Apply --app CLI filter
        if app_label_filter:
            app_configs = [
                app for app in app_configs if app.label == app_label_filter
            ]

        # Remove excluded apps
        app_configs = [
            app for app in app_configs if app.label not in exclude_apps
        ]

        if not app_configs:
            self.stdout.write(self.style.WARNING("No matching apps found to scan."))
            return

        total_apps = 0
        total_models = 0
        app_models_map = {}

        # ---- Scan + print ----
        for app_config in app_configs:
            models = list(app_config.get_models())

            if not models and not include_empty:
                # Skip apps with no models unless --include-empty is given
                continue

            total_apps += 1
            total_models += len(models)
            app_models_map[app_config] = models

            self.stdout.write(self.style.SUCCESS(f"App: {app_config.label}"))
            if models:
                for model in models:
                    self.stdout.write(f"  • {model.__name__}")
            else:
                self.stdout.write("  (no models)")
            self.stdout.write("")  # blank line

        if total_apps == 0:
            self.stdout.write(self.style.WARNING("No apps with models found."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Scan complete: {total_apps} apps, {total_models} models.\n"
            )
        )

        # ---- Budget-only mode: just show estimate and exit ----
        if budget_only:
            if total_models == 0:
                self.stdout.write(self.style.WARNING("No models found, nothing to estimate."))
                return

            # Rough estimate: ~1000 tokens per model (prompt + output)
            avg_tokens_per_model = 1000
            total_tokens = total_models * avg_tokens_per_model

            # Example pricing: gpt-4o-mini ≈ $0.0009 per 1K tokens (input+output combined rough)
            price_per_1k = 0.0009
            est_cost = (total_tokens / 1000.0) * price_per_1k

            self.stdout.write(self.style.NOTICE("💰 Budget estimation (rough):"))
            self.stdout.write(f"  • Models to generate: {total_models}")
            self.stdout.write(f"  • Estimated tokens: ~{total_tokens:,} tokens")
            self.stdout.write(f"  • Model: gpt-4o-mini (example)")
            self.stdout.write(f"  • Estimated cost: ≈ ${est_cost:.4f} USD\n")
            self.stdout.write(
                self.style.SUCCESS(
                    "This is a rough estimate. Real cost depends on model and prompt size."
                )
            )
            return

        # ---- If not budget-only and no models, nothing to do ----
        if total_models == 0:
            return

        # ---- Ask to generate serializers ----
        if not skip_confirm:
            confirm = input(
                f"Generate serializers for {total_models} models using OpenAI? [y/N]: "
            ).strip().lower()
            if confirm not in ("y", "yes"):
                self.stdout.write(self.style.WARNING("Aborted before generation."))
                return

        # ---- Generation phase ----
        for app_config, models in app_models_map.items():
            self._generate_for_app(app_config, models, model_name_filter)

        self.stdout.write(self.style.SUCCESS("\n✅ Serializer generation complete."))

    def _generate_for_app(self, app_config, models, model_name_filter=None):
        app_label = app_config.label
        app_path = Path(app_config.path)

        serializers_file = app_path / "api_serializers_ai.py"

        # Ensure file header exists (only once)
        if not serializers_file.exists():
            serializers_file.write_text(
                "from rest_framework import serializers\n\n",
                encoding="utf-8",
            )

        for model in models:
            model_name = model.__name__

            if model_name_filter and model_name != model_name_filter:
                continue

            # Collect field metadata
            fields_meta = []
            for field in model._meta.get_fields():
                # Skip reverse relations / auto-created stuff
                if getattr(field, "auto_created", False) and not field.concrete:
                    continue
                fields_meta.append(
                    {
                        "name": field.name,
                        "type": field.__class__.__name__,
                    }
                )

            prompt = build_serializer_prompt(app_label, model_name, fields_meta)

            self.stdout.write(
                self.style.NOTICE(
                    f"🤖 Generating serializer for {app_label}.{model_name}..."
                )
            )

            try:
                code = generate_code(prompt)
            except OpenAIConfigError as e:
                self.stdout.write(self.style.ERROR(str(e)))
                return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"OpenAI error for {model_name}: {e}")
                )
                continue

            if not code.strip():
                self.stdout.write(
                    self.style.WARNING(
                        f"No code returned for {app_label}.{model_name}, skipping."
                    )
                )
                continue

            # Append generated serializer
            with serializers_file.open("a", encoding="utf-8") as f:
                f.write(code)
                if not code.endswith("\n"):
                    f.write("\n")
                f.write("\n\n")

            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✅ Wrote serializer for {app_label}.{model_name} "
                    f"to {serializers_file}"
                )
            )
