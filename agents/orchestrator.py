"""
Orchestrator Agent
Coordinates the multi-agent system workflow
"""

from typing import Dict, Any, List
from .spending_analyzer import SpendingAnalyzerAgent
from .benefit_evaluator import BenefitEvaluatorAgent
from .card_selector import CardSelectorAgent


class OrchestratorAgent:
    """
    Orchestrates the multi-agent workflow
    Coordinates between different specialized agents
    """
    
    def __init__(self, rag_system=None):
        """
        Initialize orchestrator with all agents
        
        Args:
            rag_system: Optional RAG system for document retrieval
        """
        print("Initializing Multi-Agent System...")
        
        # Initialize agents
        self.spending_analyzer = SpendingAnalyzerAgent()
        self.benefit_evaluator = BenefitEvaluatorAgent(rag_system=rag_system)
        self.card_selector = CardSelectorAgent()
        
        self.rag_system = rag_system
        
        print("✓ All agents initialized")
    
    def run(self, 
            spending_profile: Dict[str, float],
            cards: List[Dict[str, Any]],
            user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the complete multi-agent workflow
        
        Args:
            spending_profile: User's monthly spending by category
            cards: List of credit cards to evaluate
            user_preferences: Optional user preferences
        
        Returns:
            Complete analysis and recommendations
        """
        print("\n🤖 Starting Multi-Agent Analysis...")
        
        total_usage = {
            "input_tokens": 0,
            "output_tokens": 0
        }
        
        # Step 1: Spending Analysis
        print("\n1️⃣ SpendingAnalyzer: Analyzing spending patterns...")
        spending_result = self.spending_analyzer.process({
            'spending_profile': spending_profile
        })
        
        if spending_result['status'] != 'success':
            return {"error": "Spending analysis failed", "details": spending_result}
        
        total_usage['input_tokens'] += spending_result['usage']['input_tokens']
        total_usage['output_tokens'] += spending_result['usage']['output_tokens']
        
        print(f"   ✓ Analyzed ${spending_result['analysis'].get('total_monthly_spend', 0)}/month spending")
        
        # Step 2: Benefit Evaluation
        print("\n2️⃣ BenefitEvaluator: Calculating rewards for each card...")
        benefit_result = self.benefit_evaluator.process({
            'spending_analysis': spending_result['analysis'],
            'cards': cards
        })
        
        if benefit_result['status'] != 'success':
            return {"error": "Benefit evaluation failed", "details": benefit_result}
        
        total_usage['input_tokens'] += benefit_result['usage']['input_tokens']
        total_usage['output_tokens'] += benefit_result['usage']['output_tokens']
        
        print(f"   ✓ Evaluated {len(cards)} cards")
        
        # Step 3: Card Selection
        print("\n3️⃣ CardSelector: Ranking and recommending best cards...")
        selector_result = self.card_selector.process({
            'spending_analysis': spending_result['analysis'],
            'benefit_evaluation': benefit_result['evaluation'],
            'user_preferences': user_preferences or {}
        })
        
        if selector_result['status'] != 'success':
            return {"error": "Card selection failed", "details": selector_result}
        
        total_usage['input_tokens'] += selector_result['usage']['input_tokens']
        total_usage['output_tokens'] += selector_result['usage']['output_tokens']
        
        print(f"   ✓ Generated {len(selector_result['recommendations']['recommendations'])} recommendations")
        
        # Calculate cost
        cost = (total_usage['input_tokens'] * 0.0008 + 
                total_usage['output_tokens'] * 0.004) / 1000
        
        print(f"\n💰 Total API Usage:")
        print(f"   Input: {total_usage['input_tokens']:,} tokens")
        print(f"   Output: {total_usage['output_tokens']:,} tokens")
        print(f"   Cost: ${cost:.4f}")
        
        # Compile final result
        return {
            "status": "success",
            "spending_analysis": spending_result['analysis'],
            "benefit_evaluation": benefit_result['evaluation'],
            "recommendations": selector_result['recommendations'],
            "api_usage": total_usage,
            "cost": cost
        }


# Example usage
if __name__ == "__main__":
    import os
    
    # Make sure API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Please set ANTHROPIC_API_KEY environment variable")
        exit(1)
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    # Test spending profile
    test_spending = {
        "dining": 300,
        "groceries": 400,
        "gas": 150,
        "travel": 100,
        "other": 500
    }
    
    # Test cards
    test_cards = [
        {
            "name": "Chase Freedom Flex",
            "annual_fee": 0,
            "rewards": {
                "base": 0.01,
                "dining": 0.03,
                "drugstores": 0.03,
                "gas": 0.01,
                "travel": 0.05,
                "groceries": 0.01
            }
        }
    ]
    
    # Run analysis
    result = orchestrator.run(
        spending_profile=test_spending,
        cards=test_cards
    )
    
    if result.get("status") == "success":
        print("\n✅ Analysis Complete!")
        print(f"\nTop Recommendation: {result['recommendations']['recommendations'][0]['card_name']}")
    else:
        print(f"\n❌ Error: {result}")
