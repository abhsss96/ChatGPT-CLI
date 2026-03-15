from __future__ import annotations
import json
import os
from pathlib import Path

from platformdirs import user_config_dir

CONFIG_DIR = Path(user_config_dir("chatgpt-cli"))
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        return key
    cfg = _load()
    return cfg.get("api_key", "")


def save_api_key(key: str) -> None:
    cfg = _load()
    cfg["api_key"] = key
    _save(cfg)


def get_model() -> str:
    return _load().get("model", "gpt-4o")


def save_model(model: str) -> None:
    cfg = _load()
    cfg["model"] = model
    _save(cfg)


def _load() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
