"""
Base Agent Class
All specialized agents inherit from this
"""

from anthropic import Anthropic
import os
from typing import Dict, Any


class BaseAgent:
    """Base class for all agents in the multi-agent system"""
    
    def __init__(self, name: str, role: str, model: str = "claude-3-5-haiku-20241022"):
        """
        Initialize base agent
        
        Args:
            name: Agent name
            role: Agent's specific role/responsibility
            model: Claude model to use
        """
        self.name = name
        self.role = role
        self.model = model
        
        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = Anthropic(api_key=api_key)
    
    def call_claude(self, prompt: str, max_tokens: int = 1500) -> Dict[str, Any]:
        """
        Make API call to Claude
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
        
        Returns:
            Response dictionary with text and usage
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "text": message.content[0].text,
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            }
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return {
                "text": f"Error: {str(e)}",
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the agent's task
        To be overridden by specific agents
        
        Args:
            context: Dictionary containing all necessary context
        
        Returns:
            Dictionary with agent's output
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def __repr__(self):
        return f"{self.name} ({self.role})"
