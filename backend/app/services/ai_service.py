"""
Generic AI service supporting multiple LLM providers via LiteLLM.
"""
from litellm import completion
from app.config import settings
import json
from typing import Dict, Any, List, Optional


class LLMService:
    """Generic LLM service that works with multiple providers."""

    def __init__(self):
        """Initialize LLM service with configured provider."""
        self.provider = settings.LLM_PROVIDER
        self.model = self._get_model_name()
        self.api_key = self._get_api_key()
        self.api_base = settings.LLM_API_BASE
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    def _get_model_name(self) -> str:
        """Get the full model name for the configured provider."""
        # LiteLLM uses provider prefixes for some models
        model = settings.LLM_MODEL

        # Map provider to model format
        provider_map = {
            'anthropic': model if model.startswith('claude') else f'claude-{model}',
            'openai': model if '/' not in model else model,
            'azure': f'azure/{model}',
            'bedrock': f'bedrock/{model}',
            'vertex_ai': f'vertex_ai/{model}',
            'ollama': f'ollama/{model}',
        }

        return provider_map.get(self.provider, model)

    def _get_api_key(self) -> Optional[str]:
        """Get API key for the configured provider."""
        # Check provider-specific env vars first
        if self.provider == 'anthropic' and settings.ANTHROPIC_API_KEY:
            return settings.ANTHROPIC_API_KEY
        elif self.provider == 'openai' and settings.OPENAI_API_KEY:
            return settings.OPENAI_API_KEY

        # Fall back to generic LLM_API_KEY
        return settings.LLM_API_KEY

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get completion from LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            response_format: Optional response format (e.g., {"type": "json_object"})

        Returns:
            The text response from the LLM
        """
        kwargs = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature or self.temperature,
            'max_tokens': max_tokens or self.max_tokens,
        }

        # Add API key if available
        if self.api_key:
            kwargs['api_key'] = self.api_key

        # Add API base if configured
        if self.api_base:
            kwargs['api_base'] = self.api_base

        # Add response format if specified (for structured outputs)
        if response_format:
            kwargs['response_format'] = response_format

        response = completion(**kwargs)
        return response.choices[0].message.content


# Global LLM service instance
llm_service = LLMService()


async def process_nl_query(user_id: str, query: str) -> Dict[str, Any]:
    """
    Process natural language financial queries.

    Examples:
    - "How much did I spend on restaurants last month?"
    - "Show me my top 5 spending categories this year"
    - "Am I on track with my grocery budget?"
    """
    # Get user's financial context
    context = await get_user_financial_context(user_id)

    prompt = f"""You are a financial analysis assistant. Analyze this user's financial data and answer their question.

User's Financial Context:
- Total accounts: {context.get('account_count', 0)}
- Current month spending: ${context.get('current_month_spending', 0)}
- Active budgets: {json.dumps(context.get('budgets', []))}
- Top categories: {json.dumps(context.get('top_categories', []))}

Recent transactions (last 30 days):
{json.dumps(context.get('recent_transactions', [])[:50], indent=2, default=str)}

User's question: {query}

Provide a clear, concise answer with specific numbers. Format your response as JSON:
{{
  "response": "natural language answer",
  "query_type": "spending_by_category|budget_status|transaction_search|trends",
  "data": {{relevant data if applicable}}
}}
"""

    messages = [{"role": "user", "content": prompt}]
    response = await llm_service.complete(messages)

    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        # If response isn't JSON, wrap it
        return {
            "response": response,
            "query_type": "general",
            "data": None
        }


async def generate_insights(user_id: str) -> List[Dict[str, Any]]:
    """
    Generate AI-powered financial insights.

    Returns insights about:
    - Spending anomalies
    - Budget warnings
    - Savings opportunities
    - Trend analysis
    """
    # Get user's financial data
    context = await get_user_financial_context(user_id)

    prompt = f"""You are a financial advisor AI. Analyze this user's financial data and generate actionable insights.

Financial Data:
- Current month spending: ${context.get('current_month_spending', 0)}
- Previous month spending: ${context.get('previous_month_spending', 0)}
- Budgets: {json.dumps(context.get('budgets', []))}
- Top spending categories: {json.dumps(context.get('top_categories', []))}
- Recent transactions: {json.dumps(context.get('recent_transactions', [])[:30], default=str)}

Generate 3-5 insights as a JSON array:
[
  {{
    "category": "spending|budget|savings|trend",
    "title": "Brief title",
    "description": "Detailed explanation",
    "severity": "info|warning|success",
    "data": {{any relevant numbers}}
  }}
]

Focus on:
1. Unusual spending patterns
2. Budget overages
3. Savings opportunities
4. Positive trends to celebrate
"""

    messages = [{"role": "user", "content": prompt}]
    response = await llm_service.complete(messages)

    try:
        insights = json.loads(response)
        return insights
    except json.JSONDecodeError:
        return []


async def get_user_financial_context(user_id: str) -> Dict[str, Any]:
    """
    Get user's financial context for AI processing.
    """
    # TODO: Implement actual database queries
    # This is a placeholder that returns mock data

    return {
        'account_count': 0,
        'current_month_spending': 0,
        'previous_month_spending': 0,
        'budgets': [],
        'top_categories': [],
        'recent_transactions': []
    }
