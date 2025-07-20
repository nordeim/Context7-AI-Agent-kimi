"""
Production-ready AI agent with Pydantic AI and MCP integration.
This version implements a robust "Hard Enforcement" Retrieval-Augmented
Generation (RAG) pattern. The application logic now explicitly controls the
multi-step process of query formulation, tool execution, and answer synthesis.
*** THIS VERSION INCLUDES DIAGNOSTIC PRINT STATEMENTS FOR DEBUGGING ***
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import logging

# Import rich for styled, clear diagnostic printing
from rich import print as rprint

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import config
from .history import HistoryManager

logger = logging.getLogger(__name__)

class Context7Agent:
    """Production-ready AI agent implementing a hard-enforced RAG pattern."""
    
    def __init__(self):
        """Initialize with correct Pydantic AI v0.5+ patterns and a synthesis-focused system prompt."""
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
            system_prompt="""
            You are a helpful AI research assistant. Your task is to provide a clear and comprehensive answer to the user's question based *only* on the provided context documents. Synthesize the information from the various documents into a single, coherent response. If the context is insufficient to answer the question, state that clearly.
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
        Stream chat responses using a hard-enforced, two-step RAG pipeline with diagnostics.
        """
        try:
            rprint("[bold yellow]--- Starting RAG Pipeline ---[/bold yellow]")
            async with self.agent.run_mcp_servers():
                # =====================================================================
                # == STEP 1: FORMULATE SEARCH QUERY                                  ==
                # =====================================================================
                rprint("[bold yellow][DEBUG-STEP-1A][/bold yellow] Formulating search query from user message...")
                query_formulation_prompt = f"""
                Based on the user's request, what is the optimal, concise search query for the Context7 documentation database?
                The user's request is: "{message}"
                Return ONLY the search query string, and nothing else.
                """
                
                query_formulation_agent = Agent(model=self.model)
                query_result = await query_formulation_agent.run(query_formulation_prompt)
                search_query = str(query_result.data).strip().strip('"')

                rprint(f"[bold yellow][DEBUG-STEP-1B][/bold yellow] Formulated Search Query: [cyan]'{search_query}'[/cyan]")

                if not search_query:
                    raise ValueError("LLM failed to formulate a search query.")
                
                # =====================================================================
                # == STEP 2: EXPLICITLY EXECUTE THE TOOL                             ==
                # =====================================================================
                # The name of the tool 'search' is assumed. A common bug is that the tool
                # name is actually different (e.g., 'context7_search').
                tool_execution_prompt = f"search(query='{search_query}')"
                rprint(f"[bold yellow][DEBUG-STEP-2A][/bold yellow] Executing explicit tool call with prompt: [cyan]'{tool_execution_prompt}'[/cyan]")
                
                retrieval_result = await self.agent.run(tool_execution_prompt)
                
                # This is the most critical diagnostic print. It shows the RAW output from the tool.
                rprint(f"[bold yellow][DEBUG-STEP-2B][/bold yellow] Raw data received from tool call:")
                rprint(f"[dim white]{retrieval_result.data}[/dim white]")

                try:
                    retrieved_docs = json.loads(str(retrieval_result.data))
                    if not isinstance(retrieved_docs, list) or not retrieved_docs:
                        # This will trigger if the tool returns an empty list `[]`.
                        raise ValueError("Tool returned no documents or an empty list.")
                except (json.JSONDecodeError, ValueError) as e:
                    # This will trigger if the tool output is not valid JSON or if it's empty.
                    rprint(f"[bold red][DEBUG-FAIL][/bold red] Failed to parse tool output. Reason: {e}")
                    rprint("[bold red]--- RAG Pipeline Failed ---[/bold red]")
                    yield {
                        "type": "content",
                        "data": "I could not find any relevant information in the Context7 knowledge base to answer your question.",
                        "timestamp": datetime.now().isoformat()
                    }
                    return

                rprint(f"[bold green][DEBUG-STEP-2C][/bold green] Successfully parsed {len(retrieved_docs)} document(s) from tool output.")
                
                # =====================================================================
                # == STEP 3: SYNTHESIZE THE FINAL ANSWER                             ==
                # =====================================================================
                rprint("[bold yellow][DEBUG-STEP-3A][/bold yellow] Synthesizing final answer based on retrieved documents...")
                synthesis_prompt = f"""
                Here is the context retrieved from the Context7 documentation database:
                ---
                {json.dumps(retrieved_docs, indent=2)}
                ---
                Based ONLY on the context provided above, provide a comprehensive answer to the user's original question: "{message}"
                """
                
                final_result = await self.agent.run(synthesis_prompt)
                content = str(final_result.data)
                
                rprint("[bold green][DEBUG-STEP-3B][/bold green] Synthesis complete.")
                rprint("[bold green]--- RAG Pipeline Succeeded ---[/bold green]")

                yield {
                    "type": "content",
                    "data": content,
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.history.save_message(conversation_id or "default", message, content)
                
                yield {
                    "type": "complete",
                    "data": content,
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Agent RAG pipeline error: {e}")
            rprint(f"[bold red][DEBUG-FATAL-ERROR][/bold red] An unexpected exception occurred in the RAG pipeline: {e}")
            yield {
                "type": "error",
                "data": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using MCP tools with proper error handling."""
        try:
            async with self.agent.run_mcp_servers():
                search_prompt = f"""
                Search the Context7 knowledge base for documents about: {query}
                Return up to {limit} most relevant results with titles, sources, and brief summaries.
                """
                result = await self.agent.run(search_prompt)
                response_text = str(result.data)
                try:
                    if response_text.strip().startswith('[') or response_text.strip().startswith('{'):
                        parsed = json.loads(response_text)
                        if isinstance(parsed, list):
                            return parsed
                        else:
                            return [parsed]
                except json.JSONDecodeError:
                    pass
                return [{
                    "title": "Search Results",
                    "content": response_text,
                    "source": "Context7 MCP",
                    "score": 1.0
                }]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [{"title": "Search Error", "content": f"Unable to search documents: {str(e)}", "source": "Error", "score": 0.0}]
    
    def get_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversation histories."""
        return self.history.get_conversations()
    
    async def clear_history(self, conversation_id: Optional[str] = None):
        """Clear conversation history."""
        await self.history.clear(conversation_id)
