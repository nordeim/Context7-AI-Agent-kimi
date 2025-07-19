"""
Conversation history management with JSON persistence.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import aiofiles

from .config import config

class HistoryManager:
    """Manages conversation history with JSON persistence."""
    
    def __init__(self):
        self.history_path = config.history_path
        self.max_history = config.max_history
        self._history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def load(self):
        """Load conversation history from disk."""
        try:
            if self.history_path.exists():
                async with aiofiles.open(self.history_path, 'r') as f:
                    content = await f.read()
                    self._history = json.loads(content)
        except Exception as e:
            print(f"Warning: Could not load history: {e}")
            self._history = {}
    
    async def save(self):
        """Save conversation history to disk."""
        try:
            async with aiofiles.open(self.history_path, 'w') as f:
                await f.write(json.dumps(self._history, indent=2))
        except Exception as e:
            print(f"Warning: Could not save history: {e}")
    
    async def save_message(
        self, 
        conversation_id: str, 
        user_message: str, 
        assistant_response: str
    ):
        """Save a message exchange to history."""
        if conversation_id not in self._history:
            self._history[conversation_id] = []
        
        self._history[conversation_id].append({
            "user": user_message,
            "assistant": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim history if too long
        if len(self._history[conversation_id]) > self.max_history:
            self._history[conversation_id] = self._history[conversation_id][-self.max_history:]
        
        await self.save()
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        return self._history.get(conversation_id, [])
    
    def get_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversation IDs with metadata."""
        conversations = []
        for conv_id, messages in self._history.items():
            if messages:
                conversations.append({
                    "id": conv_id,
                    "last_message": messages[-1]["timestamp"],
                    "message_count": len(messages)
                })
        
        return sorted(conversations, key=lambda x: x["last_message"], reverse=True)
    
    async def clear(self, conversation_id: Optional[str] = None):
        """Clear history for a conversation or all conversations."""
        if conversation_id:
            self._history.pop(conversation_id, None)
        else:
            self._history.clear()
        
        await self.save()
