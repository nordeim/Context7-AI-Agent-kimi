"""
Configuration management for Context7 Agent.
Handles environment variables and MCP server configuration.
*** UPDATED to use relative path for history. ***
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Config(BaseSettings):
    """Application configuration with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CONTEXT7_",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Required fields
    openai_api_key: str = Field(..., description="OpenAI API key")
    
    # Optional fields with defaults
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    mcp_config_path: Path = Field(
        default_factory=lambda: Path.home() / ".context7" / "mcp.json",
        description="Path to MCP configuration"
    )
    # UPDATED: Changed to a relative path as requested.
    history_path: Path = Field(
        default_factory=lambda: Path("data/history.json"),
        description="Path to conversation history"
    )
    max_history: int = Field(
        default=1000,
        description="Maximum conversation history entries"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure the new 'data' directory for history is created.
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCP server configuration."""
        config = {
            "mcpServers": {
                "context7": {
                    "command": "npx",
                    "args": ["-y", "@upstash/context7-mcp@latest"],
                    "env": {}
                }
            }
        }
        
        if not self.mcp_config_path.exists():
            with open(self.mcp_config_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        return config

# Global config instance
config = Config()
