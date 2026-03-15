from __future__ import annotations
from datetime import datetime
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    Select,
    Static,
    TextArea,
)
from textual import on, work
from textual.worker import Worker

from . import api, storage
from .config import get_api_key, get_model, save_api_key, save_model

MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]


def _relative_time(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        diff = datetime.now() - dt
        seconds = diff.total_seconds()
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        elif seconds < 604800:
            return f"{int(seconds / 86400)}d ago"
        else:
            return dt.strftime("%b %d")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------


class ApiKeyScreen(ModalScreen[Optional[str]]):
    """Modal to collect the OpenAI API key on first run."""

    DEFAULT_CSS = """
    ApiKeyScreen {
        align: center middle;
    }
    #dialog {
        width: 64;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 4;
    }
    #dialog Label {
        margin-bottom: 1;
    }
    #dialog .hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    #dialog Input {
        margin-bottom: 1;
    }
    #dialog-buttons {
        height: auto;
        align: right middle;
    }
    #dialog-buttons Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("[bold]OpenAI API Key Required[/bold]")
            yield Label(
                "Get yours at [link=https://platform.openai.com/api-keys]platform.openai.com/api-keys[/link]",
                classes="hint",
            )
            yield Input(placeholder="sk-...", password=True, id="key-input")
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", id="cancel-btn")

    @on(Button.Pressed, "#save-btn")
    @on(Input.Submitted, "#key-input")
    def _save(self) -> None:
        key = self.query_one("#key-input", Input).value.strip()
        if key:
            save_api_key(key)
            self.dismiss(key)

    @on(Button.Pressed, "#cancel-btn")
    def _cancel(self) -> None:
        self.dismiss(None)


class ModelScreen(ModalScreen[Optional[str]]):
    """Modal to pick a model."""

    DEFAULT_CSS = """
    ModelScreen {
        align: center middle;
    }
    #model-dialog {
        width: 48;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 4;
    }
    #model-dialog Label {
        margin-bottom: 1;
    }
    #model-dialog Select {
        margin-bottom: 1;
    }
    #model-btns {
        height: auto;
        align: right middle;
    }
    #model-btns Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        current = get_model()
        options = [(m, m) for m in MODELS]
        with Vertical(id="model-dialog"):
            yield Label("[bold]Select Model[/bold]")
            yield Select(options, value=current, id="model-select")
            with Horizontal(id="model-btns"):
                yield Button("Apply", variant="primary", id="apply-btn")
                yield Button("Cancel", id="cancel-model-btn")

    @on(Button.Pressed, "#apply-btn")
    def _apply(self) -> None:
        sel = self.query_one("#model-select", Select)
        if sel.value and sel.value != Select.BLANK:
            self.dismiss(str(sel.value))

    @on(Button.Pressed, "#cancel-model-btn")
    def _cancel(self) -> None:
        self.dismiss(None)


class SystemPromptScreen(ModalScreen[Optional[str]]):
    """Modal to set a system prompt for the current conversation."""

    DEFAULT_CSS = """
    SystemPromptScreen {
        align: center middle;
    }
    #sp-dialog {
        width: 72;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 2 4;
    }
    #sp-dialog Label {
        margin-bottom: 1;
    }
    #sp-dialog .hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    #sp-textarea {
        height: 8;
        margin-bottom: 1;
    }
    #sp-btns {
        height: auto;
        align: right middle;
    }
    #sp-btns Button {
        margin-left: 1;
    }
    """

    def __init__(self, current_prompt: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._current_prompt = current_prompt

    def compose(self) -> ComposeResult:
        with Vertical(id="sp-dialog"):
            yield Label("[bold]System Prompt[/bold]")
            yield Label(
                "Sets the AI's behavior for this conversation. Leave blank to use no system prompt.",
                classes="hint",
            )
            yield TextArea(self._current_prompt, id="sp-textarea")
            with Horizontal(id="sp-btns"):
                yield Button("Save", variant="primary", id="sp-save-btn")
                yield Button("Clear", variant="warning", id="sp-clear-btn")
                yield Button("Cancel", id="sp-cancel-btn")

    @on(Button.Pressed, "#sp-save-btn")
    def _save(self) -> None:
        text = self.query_one("#sp-textarea", TextArea).text.strip()
        self.dismiss(text)

    @on(Button.Pressed, "#sp-clear-btn")
    def _clear(self) -> None:
        self.dismiss("")

    @on(Button.Pressed, "#sp-cancel-btn")
    def _cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------


class MessageInput(TextArea):
    """Multi-line message input. Ctrl+Enter submits."""

    BINDINGS = [Binding("ctrl+enter", "submit_message", "Send", show=False)]

    class Submit(Message):
        pass

    def action_submit_message(self) -> None:
        self.post_message(self.Submit())


class ChatMessage(Static):
    """A single chat message bubble."""

    DEFAULT_CSS = """
    ChatMessage {
        margin: 1 0;
        padding: 1 2;
        height: auto;
    }
    ChatMessage.user {
        background: $primary-darken-3;
        border-left: thick $primary;
        margin-left: 6;
    }
    ChatMessage.assistant {
        background: $panel;
        border-left: thick $success;
        margin-right: 6;
    }
    ChatMessage .role-label {
        text-style: bold;
        margin-bottom: 1;
    }
    ChatMessage.user .role-label {
        color: $primary-lighten-1;
    }
    ChatMessage.assistant .role-label {
        color: $success-lighten-1;
    }
    """

    def __init__(self, role: str, content: str = "", **kwargs) -> None:
        super().__init__(classes=role, **kwargs)
        self.role = role
        self._content = content

    def compose(self) -> ComposeResult:
        name = "You" if self.role == "user" else "ChatGPT"
        yield Label(name, classes="role-label")
        yield Markdown(self._content or "\u200b")

    def update_content(self, content: str) -> None:
        self._content = content
        self.query_one(Markdown).update(content or "\u200b")


class ConversationItem(ListItem):
    """Sidebar list item for a conversation."""

    def __init__(self, conv_id: str, title: str, updated_at: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.conv_id = conv_id
        self._title = title
        self._updated_at = updated_at

    def compose(self) -> ComposeResult:
        label = self._title if len(self._title) <= 22 else self._title[:19] + "..."
        yield Label(label)
        if self._updated_at:
            yield Label(_relative_time(self._updated_at), classes="conv-time")


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------


class ChatApp(App):
    """ChatGPT CLI — developer-friendly AI in your terminal."""

    TITLE = "ChatGPT CLI"
    SUB_TITLE = f"Model: {get_model()}"

    CSS = """
    /* Layout */
    #main { height: 1fr; }

    /* Sidebar */
    #sidebar {
        width: 28;
        background: $panel;
        border-right: solid $border;
        padding: 1 0;
    }
    #new-chat-btn { width: 1fr; margin: 0 1 1 1; }
    #sidebar-title {
        padding: 0 2;
        color: $text-muted;
        text-style: bold;
        margin-bottom: 1;
    }
    #conversations {
        height: 1fr;
        background: transparent;
        border: none;
    }
    #conversations > ListItem { background: transparent; padding: 0 1; }
    #conversations > ListItem:hover { background: $primary-darken-3; }
    #conversations > ListItem.--highlight { background: $primary-darken-2; }
    .conv-time { color: $text-muted; text-style: italic; }

    /* Chat area */
    #chat-area { width: 1fr; }
    #messages { height: 1fr; padding: 1 2; }

    /* Welcome */
    #welcome {
        width: 1fr;
        height: 1fr;
        content-align: center middle;
        color: $text-muted;
    }

    /* Input bar */
    #input-area {
        height: auto;
        min-height: 7;
        border-top: solid $border;
        padding: 1 1 0 1;
    }
    #message-input {
        height: 5;
        width: 1fr;
        margin-bottom: 1;
    }
    #input-buttons {
        height: auto;
        align: right middle;
    }
    #stop-btn { width: 8; margin-right: 1; display: none; }
    #send-btn { width: 8; }
    #input-hint {
        height: 1;
        padding: 0 1;
        color: $text-muted;
    }

    /* Status bar */
    #status-bar {
        height: 1;
        background: $panel;
        border-top: solid $border;
        padding: 0 2;
        align: left middle;
    }
    #status-label { color: $text-muted; }
    """

    BINDINGS = [
        Binding("ctrl+n", "new_chat", "New Chat"),
        Binding("ctrl+m", "change_model", "Model"),
        Binding("ctrl+k", "focus_input", "Focus"),
        Binding("ctrl+p", "system_prompt", "System Prompt"),
        Binding("ctrl+x", "stop_generation", "Stop"),
        Binding("ctrl+d", "delete_chat", "Delete"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    current_conv: reactive[Optional[dict]] = reactive(None)
    is_streaming: reactive[bool] = reactive(False)

    def __init__(self, initial_prompt: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.initial_prompt = initial_prompt
        self._current_worker: Optional[Worker] = None

    # ------------------------------------------------------------------
    # Compose & mount
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Button("+ New Chat", id="new-chat-btn", variant="primary")
                yield Label("RECENTS", id="sidebar-title")
                yield ListView(id="conversations")
            with Vertical(id="chat-area"):
                with VerticalScroll(id="messages"):
                    yield Static(
                        "Select a conversation or press [bold]Ctrl+N[/bold] to start.",
                        id="welcome",
                    )
                with Vertical(id="input-area"):
                    yield MessageInput("", id="message-input", language=None, show_line_numbers=False)
                    with Horizontal(id="input-buttons"):
                        yield Label("Ctrl+Enter to send  |  Ctrl+P system prompt", id="input-hint")
                        yield Button("Stop", id="stop-btn", variant="error")
                        yield Button("Send", id="send-btn", variant="primary")
        with Horizontal(id="status-bar"):
            yield Label("", id="status-label")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_sidebar()
        if not get_api_key():
            self.push_screen(ApiKeyScreen(), self._on_api_key)
        else:
            self.query_one(MessageInput).focus()
            if self.initial_prompt:
                self.set_timer(0.2, self._send_initial_prompt)

    def _on_api_key(self, key: Optional[str]) -> None:
        if key:
            self.notify("API key saved!", severity="information")
            self.query_one(MessageInput).focus()
            if self.initial_prompt:
                self.set_timer(0.2, self._send_initial_prompt)
        else:
            self.notify("No API key — set OPENAI_API_KEY env var.", severity="warning")

    def _send_initial_prompt(self) -> None:
        self._send(self.initial_prompt)

    # ------------------------------------------------------------------
    # Reactive watchers
    # ------------------------------------------------------------------

    def watch_is_streaming(self, streaming: bool) -> None:
        try:
            self.query_one("#send-btn", Button).disabled = streaming
            self.query_one("#stop-btn", Button).display = streaming
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Sidebar helpers
    # ------------------------------------------------------------------

    def _refresh_sidebar(self) -> None:
        lv = self.query_one("#conversations", ListView)
        lv.clear()
        for conv in storage.load_conversations():
            lv.append(ConversationItem(conv["id"], conv["title"], conv.get("updated_at", "")))

    # ------------------------------------------------------------------
    # Chat helpers
    # ------------------------------------------------------------------

    def _clear_messages(self) -> None:
        self.query_one("#messages", VerticalScroll).remove_children()

    def _render_conversation(self, conv: dict) -> None:
        self._clear_messages()
        scroll = self.query_one("#messages", VerticalScroll)
        for msg in conv.get("messages", []):
            if msg["role"] in ("user", "assistant"):
                scroll.mount(ChatMessage(msg["role"], msg["content"]))
        scroll.scroll_end(animate=False)

    def _set_status(self, text: str) -> None:
        self.query_one("#status-label", Label).update(text)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#new-chat-btn")
    def action_new_chat(self) -> None:
        self.current_conv = storage.new_conversation()
        self._clear_messages()
        self.query_one(MessageInput).focus()
        self._set_status("New conversation")

    @on(ListView.Selected, "#conversations")
    def _on_conv_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, ConversationItem):
            conv = storage.load_conversation(item.conv_id)
            if conv:
                self.current_conv = conv
                self._render_conversation(conv)
                self._set_status(f"Loaded: {conv['title']}")
                self.query_one(MessageInput).focus()

    @on(Button.Pressed, "#send-btn")
    @on(MessageInput.Submit)
    def _on_send(self) -> None:
        inp = self.query_one(MessageInput)
        text = inp.text.strip()
        if not text:
            return
        inp.clear()
        self._send(text)

    def _send(self, text: str) -> None:
        if self.is_streaming or not text:
            return

        if not self.current_conv:
            self.current_conv = storage.new_conversation()

        for w in self.query("#welcome"):
            w.remove()

        scroll = self.query_one("#messages", VerticalScroll)
        scroll.mount(ChatMessage("user", text))

        self.current_conv["messages"].append({"role": "user", "content": text})

        if len(self.current_conv["messages"]) == 1:
            self.current_conv["title"] = text[:40] + ("\u2026" if len(text) > 40 else "")

        assistant_widget = ChatMessage("assistant", "")
        scroll.mount(assistant_widget)
        scroll.scroll_end(animate=False)

        self._current_worker = self._stream_response(assistant_widget)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_focus_input(self) -> None:
        self.query_one(MessageInput).focus()

    def action_change_model(self) -> None:
        self.push_screen(ModelScreen(), self._on_model_selected)

    def _on_model_selected(self, model: Optional[str]) -> None:
        if model:
            save_model(model)
            self.sub_title = f"Model: {model}"
            self.notify(f"Model changed to {model}")

    def action_system_prompt(self) -> None:
        if not self.current_conv:
            self.notify("Start or select a conversation first.", severity="warning")
            return
        current = self.current_conv.get("system_prompt", "")
        self.push_screen(SystemPromptScreen(current_prompt=current), self._on_system_prompt)

    def _on_system_prompt(self, prompt: Optional[str]) -> None:
        if prompt is None:
            return
        if self.current_conv:
            self.current_conv["system_prompt"] = prompt
            storage.save_conversation(self.current_conv)
            label = f"System prompt {'set' if prompt else 'cleared'}"
            self.notify(label, severity="information")

    def action_stop_generation(self) -> None:
        if self._current_worker and self.is_streaming:
            self._current_worker.cancel()
            self._set_status("Stopped.")

    def action_delete_chat(self) -> None:
        if not self.current_conv:
            return
        storage.delete_conversation(self.current_conv["id"])
        self.current_conv = None
        self._clear_messages()
        scroll = self.query_one("#messages", VerticalScroll)
        scroll.mount(
            Static(
                "Select a conversation or press [bold]Ctrl+N[/bold] to start.",
                id="welcome",
            )
        )
        self._refresh_sidebar()
        self.notify("Conversation deleted", severity="warning")

    # ------------------------------------------------------------------
    # Streaming worker
    # ------------------------------------------------------------------

    @work(exclusive=True)
    async def _stream_response(self, widget: ChatMessage) -> None:
        self.is_streaming = True
        self._set_status("ChatGPT is thinking\u2026")

        full_text = ""
        usage_out: list = []
        scroll = self.query_one("#messages", VerticalScroll)

        try:
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in self.current_conv["messages"]
            ]
            system_prompt = self.current_conv.get("system_prompt", "")
            async for token in api.stream_chat(messages, system_prompt=system_prompt, usage_out=usage_out):
                full_text += token
                widget.update_content(full_text)
                scroll.scroll_end(animate=False)

        except Exception as exc:
            widget.update_content(f"**Error:** {exc}")
            self._set_status(f"Error: {exc}")

        finally:
            if full_text and self.current_conv:
                self.current_conv["messages"].append(
                    {"role": "assistant", "content": full_text}
                )
                storage.save_conversation(self.current_conv)
                self._refresh_sidebar()

            self.is_streaming = False
            if usage_out:
                usage = usage_out[-1]
                self._set_status(
                    f"Model: {get_model()} | Tokens: {usage.total_tokens} "
                    f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})"
                )
            else:
                self._set_status(f"Model: {get_model()}")
            self.query_one(MessageInput).focus()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="chatgpt",
        description="ChatGPT CLI — a developer-friendly AI in your terminal.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="",
        help="Optional initial prompt to send immediately on startup.",
    )
    args = parser.parse_args()
    ChatApp(initial_prompt=args.prompt).run()


if __name__ == "__main__":
    main()
