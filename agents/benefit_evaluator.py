"""
Benefit Evaluator Agent
Evaluates credit card benefits and calculates projected rewards
Uses RAG to get detailed card information
"""

from .base_agent import BaseAgent
from typing import Dict, Any, List
import json


class BenefitEvaluatorAgent(BaseAgent):
    """Evaluates card benefits and calculates rewards"""
    
    def __init__(self, rag_system=None):
        super().__init__(
            name="BenefitEvaluator",
            role="Calculate projected rewards and evaluate card benefits"
        )
        self.rag_system = rag_system
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate benefits for cards
        
        Args:
            context: Dictionary with:
                - 'spending_analysis': Output from SpendingAnalyzer
                - 'cards': List of cards to evaluate
        
        Returns:
            Benefit evaluation for each card
        """
        spending_analysis = context.get('spending_analysis', {})
        cards = context.get('cards', [])
        
        if not cards:
            return {
                "status": "error",
                "agent": self.name,
                "error": "No cards provided for evaluation"
            }
        
        # Get additional context from RAG if available
        rag_context = ""
        if self.rag_system:
            for card in cards:
                query = f"What are the reward rates and benefits for {card.get('name', 'this card')}?"
                rag_context += self.rag_system.get_context_for_query(
                    query, 
                    k=2,
                    card_filter=card.get('name')
                ) + "\n\n"
        
        prompt = f"""You are a credit card rewards expert. Calculate projected annual rewards for these cards based on the spending profile.

SPENDING ANALYSIS:
{json.dumps(spending_analysis, indent=2)}

CARDS TO EVALUATE:
{json.dumps(cards, indent=2)}

{f"ADDITIONAL CARD DETAILS FROM DOCUMENTS:\\n{rag_context}" if rag_context else ""}

For each card, calculate:
1. Rewards by category
2. Total annual rewards
3. Annual fee impact
4. Net annual value (rewards - fees)

Respond in JSON format:
{{
    "evaluations": [
        {{
            "card_name": "name",
            "category_rewards": {{
                "category": {{"spend": X, "rate": Y, "rewards": Z}}
            }},
            "total_annual_rewards": X,
            "annual_fee": Y,
            "net_annual_value": Z,
            "effective_return_pct": X.XX
        }}
    ]
}}

IMPORTANT: Respond ONLY with valid JSON."""

        response = self.call_claude(prompt, max_tokens=2000)
        
        try:
            evaluation = json.loads(response['text'])
            
            return {
                "status": "success",
                "agent": self.name,
                "evaluation": evaluation,
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
