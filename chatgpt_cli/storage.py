from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path

from platformdirs import user_data_dir

DATA_DIR = Path(user_data_dir("chatgpt-cli"))
CONVERSATIONS_DIR = DATA_DIR / "conversations"


def _ensure() -> None:
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)


def new_conversation(title: str = "New Chat") -> dict:
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "system_prompt": "",
        "messages": [],
    }


def save_conversation(conv: dict) -> None:
    _ensure()
    conv["updated_at"] = datetime.now().isoformat()
    path = CONVERSATIONS_DIR / f"{conv['id']}.json"
    path.write_text(json.dumps(conv, indent=2))


def load_conversations() -> list[dict]:
    _ensure()
    convs = []
    for path in sorted(
        CONVERSATIONS_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        try:
            convs.append(json.loads(path.read_text()))
        except Exception:
            pass
    return convs


def load_conversation(conv_id: str) -> dict | None:
    path = CONVERSATIONS_DIR / f"{conv_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


def delete_conversation(conv_id: str) -> None:
    path = CONVERSATIONS_DIR / f"{conv_id}.json"
    if path.exists():
        path.unlink()
