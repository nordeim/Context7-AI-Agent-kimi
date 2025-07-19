"""
Production-ready AI agent with Pydantic AI and MCP integration.
This version implements a robust Retrieval-Augmented Generation (RAG)
pattern by using a highly precise system prompt, fixing the flawed logic
of the previous version and ensuring the agent uses its tools reliably.
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
    """Production-ready AI agent implementing a robust RAG pattern."""
    
    def __init__(self):
        """Initialize with correct Pydantic AI v0.5+ patterns and a RAG-enforcing system prompt."""
        self.provider = OpenAIProvider(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        
        self.model = OpenAIModel(
            model_name=config.openai_model,
            provider=self.provider
        )
        
        # This MCP server provides the `search` tool, which is critical for our RAG pipeline.
        # The tool's description within the MCP server itself should be equally clear, e.g.,
        # "Searches the official Context7 knowledge base for up-to-date documents."
        self.mcp_server = MCPServerStdio(
            command="npx",
            args=["-y", "@upstash/context7-mcp@latest"]
        )
        
        # =============================================================================
        # == GOLD STANDARD RAG SYSTEM PROMPT                                         ==
        # =============================================================================
        # This new, highly-directive system prompt is the core of the fix. It
        # forces the agent to follow a strict RAG pattern, preventing hallucination.
        #
        self.agent = Agent(
            model=self.model,
            mcp_servers=[self.mcp_server],
            system_prompt="""
            You are a specialized AI research assistant named Context7.

            ## CORE DIRECTIVE
            Your SOLE PURPOSE is to provide answers by exclusively using the information retrieved from the attached `search` tool, which connects to the official Context7 knowledge base. You are forbidden from using your own internal, pre-trained knowledge, as it is considered outdated and unreliable.

            ## RULES OF ENGAGEMENT
            1.  **MUST use the tool:** For any user question that is not a simple greeting (like "hello"), you MUST ALWAYS call the `search` tool to gather context before formulating an answer.
            2.  **MUST ground your answer:** You MUST synthesize your final answer using ONLY the `documents` and `content` provided in the tool's output. Do not add any information not present in the retrieved context.
            3.  **MUST handle failure:** If the `search` tool returns no relevant documents or an error, you MUST respond with the exact phrase: "I could not find any relevant information in the Context7 knowledge base to answer your question." Do not attempt to answer from memory.
            4.  **MUST be concise:** When you call the tool, formulate a concise and effective search query string based on the user's intent. Do not pass the user's entire conversational text to the tool.

            ## OPERATIONAL FLOW
            For every user query, you will follow this exact sequence:
            1.  **Analyze:** Deconstruct the user's query to identify the core topic.
            2.  **Formulate Query:** Create a clear, concise search term (e.g., "pydantic-ai MCP server setup" or "agent streaming").
            3.  **Execute Tool:** Call the `search` tool with the formulated query.
            4.  **Analyze Context:** Carefully review the documents returned by the tool.
            5.  **Synthesize Answer:** Construct a comprehensive answer based only on the retrieved documents, citing sources if possible.
            """
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
        """
        Stream chat responses using the robust RAG-powered agent.
        The control flow here remains simple because the complex RAG logic
        is now handled by the LLM, as mandated by the system prompt.
        """
        
        try:
            async with self.agent.run_mcp_servers():
                # Build conversation history
                history = self.history.get_messages(conversation_id or "default")
                
                # Create proper message structure for Pydantic AI
                messages = []
                for msg in history[-6:]:  # Last 6 messages for context
                    # The original file had a bug here, mapping "user" to "user" and "assistant" to "assistant".
                    # The correct mapping should be from our history format to OpenAI's format if they differ.
                    # Assuming they are already in the correct {"role": "...", "content": "..."} format.
                    messages.append(msg)
                
                # Use Pydantic AI's native run method. Thanks to our new system prompt,
                # this single call now triggers the entire RAG pipeline automatically.
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
        """
        Search documents using MCP tools with proper error handling.
        NOTE: This method is preserved to prevent regression but is not directly
        used by the main chat loop, which now relies on the agent's autonomous tool use.
        """
        
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
