## 🎯 Usage

### Quick Start
```bash
# 1. Clone and setup
git clone <your-repo>
cd context7-agent
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your OpenAI key

# 3. Run
python -m src.cli
```

### CLI Commands
- `/theme [name]` - Switch themes (cyberpunk, ocean, forest, sunset)
- `/history` - View conversation history
- `/clear` - Clear history
- `/exit` - Exit application

### Example Interactions
```
You: Tell me about quantum computing
Assistant: [Streams real-time search results about quantum computing]

You: /theme ocean
[Theme switches to ocean mode with blue gradients]

You: /history
[Shows previous conversations with timestamps]
```

## 🌟 Features Showcase

### Stunning Visuals
- **4 Beautiful Themes**: Each with unique color schemes and ASCII art
- **Smooth Animations**: Typing effects, progress spinners, transitions
- **Rich Layouts**: Split-screen interface with panels, tables, and gradients

### Advanced Functionality
- **Real-time MCP Integration**: Live document streaming from Context7
- **Conversation Persistence**: Auto-save/load with JSON storage
- **Smart Search**: AI-powered document discovery with relevance scoring
- **Command Interface**: Intuitive slash commands for all features

### Error Handling
- **Graceful Degradation**: Continues working even if MCP fails
- **Clear Error Messages**: Styled alerts with retry options
- **Logging**: Comprehensive logging for debugging

## 🚀 Future Enhancements

- **Voice Commands**: Speech-to-text integration
- **Web Interface**: Browser-based version
- **Plugin System**: Extensible tool architecture
- **Collaborative Sessions**: Multi-user chat support
- **Advanced Analytics**: Search pattern analysis and insights

This implementation delivers a production-ready, visually stunning Context7 AI agent that transforms terminal interactions into a futuristic experience!
