"""
Card Selector Agent  
Makes final card recommendations based on all analysis
"""

from .base_agent import BaseAgent
from typing import Dict, Any
import json


class CardSelectorAgent(BaseAgent):
    """Selects and recommends best cards"""
    
    def __init__(self):
        super().__init__(
            name="CardSelector",
            role="Select and rank best credit card recommendations",
            model="claude-3-5-sonnet-20241022"  # Use Sonnet for complex reasoning
        )
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select best cards based on all analysis
        
        Args:
            context: Dictionary with:
                - 'spending_analysis': From SpendingAnalyzer
                - 'benefit_evaluation': From BenefitEvaluator
                - 'user_preferences': Optional user preferences
        
        Returns:
            Ranked card recommendations with explanations
        """
        spending_analysis = context.get('spending_analysis', {})
        benefit_evaluation = context.get('benefit_evaluation', {})
        user_preferences = context.get('user_preferences', {})
        
        prompt = f"""You are an expert credit card advisor. Based on the analysis below, recommend the TOP 3 best credit cards for this user.

SPENDING ANALYSIS:
{json.dumps(spending_analysis, indent=2)}

BENEFIT EVALUATION:
{json.dumps(benefit_evaluation, indent=2)}

USER PREFERENCES:
{json.dumps(user_preferences, indent=2)}

Provide recommendations in JSON format:
{{
    "recommendations": [
        {{
            "rank": 1,
            "card_name": "name",
            "net_annual_value": X,
            "recommendation_strength": "rating out of 10",
            "pros": ["pro1", "pro2", "pro3"],
            "cons": ["con1", "con2"],
            "best_for": "brief description",
            "explanation": "detailed explanation why this card fits"
        }}
    ],
    "overall_analysis": "Summary of recommendations"
}}

Be honest and balanced in your assessment. If a card isn't great for their spending, say so.

IMPORTANT: Respond ONLY with valid JSON."""

        response = self.call_claude(prompt, max_tokens=2500)
        
        try:
            recommendations = json.loads(response['text'])
            
            return {
                "status": "success",
                "agent": self.name,
                "recommendations": recommendations,
                "usage": response['usage']
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "agent": self.name,
                "error": "Failed to parse JSON response",
                "raw_response": response['text'],
                "usage": response['usage']
            }
