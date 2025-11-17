"""
Spending Analyzer Agent
Analyzes user spending patterns and categorizes them
"""

from .base_agent import BaseAgent
from typing import Dict, Any
import json


class SpendingAnalyzerAgent(BaseAgent):
    """Analyzes user spending patterns"""
    
    def __init__(self):
        super().__init__(
            name="SpendingAnalyzer",
            role="Analyze and categorize user spending patterns"
        )
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze spending profile
        
        Args:
            context: Dictionary with 'spending_profile' key
        
        Returns:
            Analysis with categorized spending and insights
        """
        spending_profile = context.get('spending_profile', {})
        
        prompt = f"""You are a spending analysis expert. Analyze this user's monthly spending profile:

{json.dumps(spending_profile, indent=2)}

Provide analysis in the following JSON format:
{{
    "total_monthly_spend": <total>,
    "spending_breakdown": {{
        "category": amount
    }},
    "top_categories": [
        {{"category": "name", "amount": X, "percentage": Y}}
    ],
    "spending_pattern": "brief description of spending behavior",
    "recommendations": ["recommendation 1", "recommendation 2"]
}}

IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation."""

        response = self.call_claude(prompt)
        
        try:
            # Parse JSON response
            analysis = json.loads(response['text'])
            
            return {
                "status": "success",
                "agent": self.name,
                "analysis": analysis,
                "usage": response['usage']
            }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "status": "error",
                "agent": self.name,
                "error": "Failed to parse JSON response",
                "raw_response": response['text'],
                "usage": response['usage']
            }
