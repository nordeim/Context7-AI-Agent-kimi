"""
Production-ready AI agent with Pydantic AI and MCP integration.
Fixed import paths and message class names for v0.5+ compatibility.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import config
from .history import HistoryManager

logger = logging.getLogger(__name__)

class Context7Agent:
    """Production-ready AI agent with native Pydantic AI integration."""
    
    def __init__(self):
        """Initialize with correct Pydantic AI v0.5+ patterns."""
        self.provider = OpenAIProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        
        self.model = OpenAIModel(
            model_name=config.openai_model,
            provider=self.provider
        )
        
        self.mcp_server = MCPServerStdio(
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"]
        )
        
        self.agent = Agent(
            model=self.model,
            mcp_servers=[self.mcp_server],
            system_prompt="""You are Context7, an advanced AI assistant with access to a vast knowledge base.
            You can search, analyze, and present documents in real-time. Be helpful, concise, and engaging.
            When users ask about topics, use the search tools to find relevant documents and provide summaries."""
        )
        
        self.history = HistoryManager()
    
    async def initialize(self):
        """Initialize the agent and load history."""
        await self.history.load()
    
    async def chat_stream(
        self, 
        message: str, 
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat responses using correct Pydantic AI patterns."""
        
        try:
            async with self.agent.run_mcp_servers():
                # Build conversation history
                history = self.history.get_messages(conversation_id or "default")
                
                # Create proper message structure for Pydantic AI
                messages = []
                for msg in history[-6:]:  # Last 6 messages for context
                    if msg["role"] == "user":
                        messages.append({"role": "user", "content": msg["content"]})
                    elif msg["role"] == "assistant":
                        messages.append({"role": "assistant", "content": msg["content"]})
                
                # Use Pydantic AI's native run method
                result = await self.agent.run(
                    message,
                    message_history=messages
                )
                
                # Stream the response
                content = str(result.data)
                
                yield {
                    "type": "content",
                    "data": content,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Save to history
                await self.history.save_message(
                    conversation_id or "default",
                    message,
                    content
                )
                
                yield {
                    "type": "complete",
                    "data": content,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Agent error: {e}")
            yield {
                "type": "error",
                "data": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def search_documents(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents using MCP tools with proper error handling."""
        
        try:
            async with self.agent.run_mcp_servers():
                search_prompt = f"""
                Search the Context7 knowledge base for documents about: {query}
                Return up to {limit} most relevant results with titles, sources, and brief summaries.
                """
                
                result = await self.agent.run(search_prompt)
                
                # Parse and structure the results
                response_text = str(result.data)
                
                # Attempt to parse as JSON if possible
                try:
                    if response_text.strip().startswith('[') or response_text.strip().startswith('{'):
                        parsed = json.loads(response_text)
                        if isinstance(parsed, list):
                            return parsed
                        else:
                            return [parsed]
                except json.JSONDecodeError:
                    pass
                
                # Fallback to structured response
                return [{
                    "title": "Search Results",
                    "content": response_text,
                    "source": "Context7 MCP",
                    "score": 1.0
                }]
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [{
                "title": "Search Error",
                "content": f"Unable to search documents: {str(e)}",
                "source": "Error",
                "score": 0.0
            }]
    
    def get_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversation histories."""
        return self.history.get_conversations()
    
    async def clear_history(self, conversation_id: Optional[str] = None):
        """Clear conversation history."""
        await self.history.clear(conversation_id)
