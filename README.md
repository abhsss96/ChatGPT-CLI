# chatgpt-cli

A developer-friendly ChatGPT terminal UI built with [Textual](https://textual.textualize.io/). Chat with OpenAI models directly from your terminal — with conversation history, model switching, and a clean keyboard-driven interface.

## Features

- **Streaming responses** — see tokens as they arrive, just like the web UI
- **Persistent conversations** — all chats saved locally as JSON files
- **Model switching** — switch between GPT models without leaving the app
- **Sidebar** — browse and resume previous conversations
- **First-run onboarding** — prompts for your API key on first launch
- **Keyboard-first** — no mouse required

## Requirements

- Python 3.11+
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Installation

### From PyPI

```bash
pip install chatgpt-cli
```

### From source

```bash
git clone https://github.com/abhisheksharma/chatgpt-cli.git
cd chatgpt-cli
pip install .
```

## Usage

```bash
chatgpt
```

On first launch, you'll be prompted to enter your OpenAI API key. It's saved to your local config and never leaves your machine.

Alternatively, set the environment variable before running:

```bash
export OPENAI_API_KEY=sk-...
chatgpt
```

Or create a `.env` file in your working directory:

```
OPENAI_API_KEY=sk-...
```

## Keyboard Shortcuts

| Key      | Action              |
|----------|---------------------|
| `Ctrl+N` | New conversation    |
| `Ctrl+M` | Change model        |
| `Ctrl+K` | Focus message input |
| `Ctrl+D` | Delete conversation |
| `Ctrl+Q` | Quit                |
| `Enter`  | Send message        |

## Supported Models

- `gpt-4o` (default)
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

## Configuration

Config is stored at `~/.config/chatgpt-cli/config.json` (macOS/Linux) and contains:

```json
{
  "api_key": "sk-...",
  "model": "gpt-4o"
}
```

The `OPENAI_API_KEY` environment variable always takes precedence over the config file.

## Conversation Storage

Conversations are stored as individual JSON files at:

```
~/.local/share/chatgpt-cli/conversations/
```

Each file is human-readable and named by a UUID. You can back them up, move them, or delete them manually.

## Project Structure

```
chatgpt_cli/
├── app.py       # Main Textual app, UI layout, widgets, and modals
├── api.py       # OpenAI streaming API integration
├── config.py    # API key and model preference persistence
└── storage.py   # Conversation read/write/delete
```

## License

MIT
