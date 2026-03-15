# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-03-15

### Added
- **Multiline input**: Message input is now a `TextArea` — use `Ctrl+Enter` to send, or click Send
- **Stop generation**: Press `Ctrl+X` or click the Stop button to cancel a streaming response mid-way
- **System prompt per conversation**: Press `Ctrl+P` to set a custom system prompt; stored in the conversation JSON
- **Token usage in status bar**: After each response, shows total tokens used (prompt + completion breakdown)
- **Relative timestamps in sidebar**: Each conversation now shows how long ago it was last updated (e.g. "2h ago", "3d ago")
- **CLI argument support**: Pass a prompt directly — `chatgpt "explain async/await"` starts a new chat immediately

### Changed
- Status bar now shows token count after each AI response
- Sidebar conversation titles are slightly shorter (22 chars) to make room for timestamps
- Package classifier updated from Alpha to Beta

## [0.1.0] - 2026-01-01

### Added
- Initial release
- Real-time streaming chat responses
- Two-panel layout: sidebar (conversation list) + main chat area
- Conversation persistence (UUID-named JSON files in `~/.local/share/chatgpt-cli/conversations/`)
- Model selection modal (`Ctrl+M`) — gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
- Auto-title from first user message (truncated to 40 chars)
- Keyboard bindings: `Ctrl+N` (new chat), `Ctrl+M` (model), `Ctrl+K` (focus input), `Ctrl+D` (delete), `Ctrl+Q` (quit)
- First-run API key onboarding modal
- `OPENAI_API_KEY` env var support

[Unreleased]: https://github.com/abhisheksharma/chatgpt-cli/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/abhisheksharma/chatgpt-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/abhisheksharma/chatgpt-cli/releases/tag/v0.1.0
