"""
Generic AI service supporting multiple LLM providers via LiteLLM.
"""

from litellm import completion
from app.config import settings
import json
import logging
from typing import Dict, Any, List, Optional


class LLMService:
    """Generic LLM service that works with multiple providers."""

    def __init__(self):
        """Initialize LLM service with configured provider."""
        self.logger = logging.getLogger(__name__)
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = self._get_model_name()
        self.api_key = self._get_api_key()
        self.api_base = settings.LLM_API_BASE
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.logger.info("LLM config: provider=%s model=%s api_base=%s", self.provider, self.model, self.api_base)

    def _get_model_name(self) -> str:
        """Get the full model name for the configured provider."""
        # LiteLLM uses provider prefixes for some models
        model = settings.LLM_MODEL

        # Normalize Gemini list-models output (they return names like "models/gemini-1.5-pro")
        if self.provider in {"google", "gemini"} and model.startswith("models/"):
            model = model.removeprefix("models/")

        # If model already includes a provider prefix, keep it as-is
        if "/" in model:
            return model

        # Map provider to model format
        provider_map = {
            "anthropic": model if model.startswith("claude") else f"claude-{model}",
            "openai": model if "/" not in model else model,
            "azure": f"azure/{model}",
            "bedrock": f"bedrock/{model}",
            "vertex_ai": f"vertex_ai/{model}",
            "gemini": f"gemini/{model}",
            "google": f"gemini/{model}",
            "ollama": f"ollama/{model}",
        }

        return provider_map.get(self.provider, f"gemini/{model}" if model.startswith("gemini-") else model)

    def _get_api_key(self) -> Optional[str]:
        """Get API key for the configured provider."""
        # Check provider-specific env vars first
        if self.provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            return settings.ANTHROPIC_API_KEY
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            return settings.OPENAI_API_KEY

        # Fall back to generic LLM_API_KEY
        return settings.LLM_API_KEY

    async def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
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
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        if self.provider in {"google", "gemini"}:
            kwargs["custom_llm_provider"] = "gemini"

        # Add API key if available
        if self.api_key:
            kwargs["api_key"] = self.api_key

        # Add API base if configured
        if self.api_base:
            kwargs["api_base"] = self.api_base

        # Add response format if specified (for structured outputs)
        if response_format:
            kwargs["response_format"] = response_format

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
- Total accounts: {context.get("account_count", 0)}
- Current month spending: ${context.get("current_month_spending", 0)}
- Active budgets: {json.dumps(context.get("budgets", []))}
- Top categories: {json.dumps(context.get("top_categories", []))}

Recent transactions (last 30 days):
{json.dumps(context.get("recent_transactions", [])[:50], indent=2, default=str)}

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
        return {"response": response, "query_type": "general", "data": None}


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
- Current month spending: ${context.get("current_month_spending", 0)}
- Previous month spending: ${context.get("previous_month_spending", 0)}
- Budgets: {json.dumps(context.get("budgets", []))}
- Top spending categories: {json.dumps(context.get("top_categories", []))}
- Recent transactions: {json.dumps(context.get("recent_transactions", [])[:30], default=str)}

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


async def analyze_statement_structure(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze bank statement structure and extract metadata.

    Args:
        content: Parsed content from CSV or PDF parser
                 For CSV: {'format_type': 'csv', 'transaction_count': int, 'date_range': {...}}
                 For PDF: {'format_type': 'pdf', 'content': {...}, 'account_info': {...}}

    Returns:
        Dictionary with extracted metadata:
        {
            "institution": "bank name",
            "account_number_last4": "last 4 digits or null",
            "account_type": "checking|savings|credit_card|unknown",
            "statement_period": {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"},
            "format_type": "csv|pdf_tabular|pdf_text",
            "confidence": 0.95
        }
    """
    # Build prompt based on content type
    if content.get("format_type") == "pdf":
        pdf_content = content.get("content", {})
        account_info = content.get("account_info", {})

        prompt = f"""Analyze this bank statement and extract metadata.

PDF Content:
- Full Text Sample: {pdf_content.get("full_text", "")[:2000]}
- Transaction Section: {pdf_content.get("transaction_section", "")[:1500]}
- Has Tables: {pdf_content.get("has_tables", False)}
- Detected Account Info: {json.dumps(account_info)}

Return JSON with this structure:
{{
  "institution": "bank name (e.g., Chase, Bank of America)",
  "account_number_last4": "last 4 digits or null",
  "account_type": "checking|savings|credit_card|unknown",
  "statement_period": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}},
  "format_type": "pdf_tabular|pdf_text",
  "confidence": 0.95
}}

Guidelines:
- Use detected account info if available
- Look for common bank names in headers
- Identify account type from keywords (checking, savings, credit card)
- Extract statement date range
- Set confidence based on how much information you can extract
"""
    else:
        # CSV format
        csv_metadata = content
        date_range = csv_metadata.get("date_range", {})

        prompt = f"""Analyze this CSV bank statement metadata and extract information.

CSV Metadata:
- Format: CSV
- Transaction count: {csv_metadata.get("transaction_count", 0)}
- Date range: {date_range.get("start")} to {date_range.get("end")}

Return JSON with this structure:
{{
  "institution": "bank name or null",
  "account_number_last4": "null for CSV",
  "account_type": "unknown",
  "statement_period": {{"start_date": "{date_range.get("start", "")}", "end_date": "{date_range.get("end", "")}"}},
  "format_type": "csv",
  "confidence": 0.7
}}

Note: CSV files typically don't contain institution or account info, so those will be null/unknown.
The user will need to specify the account during import.
"""

    messages = [{"role": "user", "content": prompt}]
    response = await llm_service.complete(messages, temperature=0.1)

    try:
        metadata = json.loads(response)
        return metadata
    except json.JSONDecodeError:
        # Return fallback metadata
        return {
            "institution": None,
            "account_number_last4": None,
            "account_type": "unknown",
            "statement_period": content.get("date_range", {}),
            "format_type": content.get("format_type", "unknown"),
            "confidence": 0.3,
        }


async def extract_transactions(
    content: Dict[str, Any], statement_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract transactions from parsed statement content.

    Args:
        content: Parsed content (CSV transactions or PDF content)
        statement_info: Metadata from analyze_statement_structure()

    Returns:
        List of transaction dictionaries:
        [{
            "date": "YYYY-MM-DD",
            "amount": -50.00,  # negative for expenses, positive for income
            "description": "original description",
            "merchant_name": "cleaned merchant name",
            "category": "suggested category",
            "confidence": 0.85
        }]
    """
    # If content is already parsed transactions (from CSV), enhance with AI categorization
    if isinstance(content, list) and len(content) > 0 and "date" in content[0]:
        # Already parsed CSV transactions - just add AI categorization
        return await categorize_transactions_batch(content)

    # PDF content - need to extract transactions from text/tables
    pdf_content = content.get("content", {})

    prompt = f"""Extract transactions from this bank statement.

Statement Info: {json.dumps(statement_info)}

Content:
- Transaction Section: {pdf_content.get("transaction_section", "")}
- Tables: {json.dumps(pdf_content.get("tables", [])[:2])}

Return JSON array of transactions:
[{{
  "date": "YYYY-MM-DD",
  "amount": -50.00,
  "description": "original description",
  "merchant_name": "cleaned merchant name",
  "category": "Food",
  "subcategory": "Restaurants",
  "confidence": 0.85
}}]

Guidelines:
- Skip headers, totals, and balance rows
- Normalize dates to YYYY-MM-DD
- Clean merchant names (remove IDs, locations, reference numbers)
- Negative amounts for debits/expenses, positive for credits/income
- Suggest category and subcategory
- Set confidence based on clarity of data

Categories: Income, Housing, Transportation, Food, Shopping, Entertainment, Healthcare, Financial, Personal, Travel, Other
"""

    messages = [{"role": "user", "content": prompt}]
    response = await llm_service.complete(messages, max_tokens=4096, temperature=0.1)

    try:
        transactions = json.loads(response)
        return transactions
    except json.JSONDecodeError:
        return []


async def categorize_transactions_batch(
    transactions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Categorize a batch of transactions using AI.

    Args:
        transactions: List of transaction dicts with date, amount, description, merchant_name

    Returns:
        Same transactions with added category, subcategory, and confidence fields
    """
    if not transactions:
        return []

    # Define category structure
    categories = {
        "Income": ["Salary", "Freelance", "Investment Income", "Gifts", "Refunds"],
        "Housing": [
            "Rent/Mortgage",
            "Utilities",
            "Internet",
            "Home Maintenance",
            "Furniture",
        ],
        "Transportation": [
            "Gas",
            "Public Transit",
            "Ride Share",
            "Car Maintenance",
            "Parking",
        ],
        "Food": ["Groceries", "Restaurants", "Coffee Shops", "Fast Food", "Delivery"],
        "Shopping": ["Clothing", "Electronics", "Home Goods", "Personal Care", "Books"],
        "Entertainment": [
            "Streaming Services",
            "Movies",
            "Gaming",
            "Hobbies",
            "Events",
        ],
        "Healthcare": ["Medical", "Dental", "Pharmacy", "Health Insurance", "Fitness"],
        "Financial": ["Bank Fees", "Interest", "Investments", "Insurance", "Taxes"],
        "Personal": ["Haircut", "Spa", "Subscriptions", "Gifts", "Education"],
        "Travel": ["Flights", "Hotels", "Vacation", "Travel Insurance"],
        "Other": ["Uncategorized"],
    }

    # Limit batch size to avoid token limits
    batch_size = 30
    all_categorized = []

    for i in range(0, len(transactions), batch_size):
        batch = transactions[i : i + batch_size]

        prompt = f"""You are a financial transaction categorization expert. Analyze these transactions and categorize each one.

Available categories and subcategories:
{json.dumps(categories, indent=2)}

Transactions to categorize:
{json.dumps(batch, indent=2, default=str)}

For each transaction, determine:
1. The most appropriate category and subcategory
2. Your confidence level (0.0 to 1.0)

Return ONLY a JSON array with this structure:
[
  {{
    "date": "YYYY-MM-DD",
    "amount": -50.00,
    "description": "...",
    "merchant_name": "...",
    "category": "category_name",
    "subcategory": "subcategory_name",
    "confidence": 0.95
  }}
]

Guidelines:
- Use merchant name as primary signal
- Consider transaction amount patterns
- Be conservative with confidence scores
- If truly unclear, use confidence < 0.5 and suggest "Other"
"""

        messages = [{"role": "user", "content": prompt}]
        response = await llm_service.complete(
            messages, max_tokens=4096, temperature=0.1
        )

        try:
            categorized_batch = json.loads(response)
            all_categorized.extend(categorized_batch)
        except json.JSONDecodeError:
            # If parsing fails, return original batch with default category
            for txn in batch:
                txn["category"] = "Other"
                txn["subcategory"] = "Uncategorized"
                txn["confidence"] = 0.0
            all_categorized.extend(batch)

    return all_categorized


async def suggest_account_match(
    statement_metadata: Dict[str, Any], user_accounts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Suggest which account this statement belongs to.

    Args:
        statement_metadata: Extracted metadata from analyze_statement_structure()
        user_accounts: List of user's existing accounts

    Returns:
        {
            "suggested_account_id": "uuid or null",
            "confidence": 0.95,
            "reasoning": "explanation",
            "should_create_new": true/false,
            "suggested_account_name": "name for new account if creating"
        }
    """
    prompt = f"""You are a financial account matching expert. Determine which account this statement belongs to.

Statement Metadata:
{json.dumps(statement_metadata, indent=2)}

User's Existing Accounts:
{json.dumps(user_accounts, indent=2)}

Analyze and return JSON:
{{
  "suggested_account_id": "uuid of best match or null",
  "confidence": 0.95,
  "reasoning": "explanation of why this account matches",
  "should_create_new": true/false,
  "suggested_account_name": "name for new account if creating"
}}

Matching criteria (in order of importance):
1. Institution name + account_number_last4 = EXACT match (confidence 1.0)
2. Institution name + account_type = STRONG match (confidence 0.8)
3. Account_type only = WEAK match (confidence 0.5)
4. No matches = suggest creating new account

Guidelines:
- If multiple accounts match, choose the most recent or active one
- If no good match (confidence < 0.7), suggest creating new account
- For new accounts, suggest a descriptive name like "Chase Checking (...1234)"
"""

    messages = [{"role": "user", "content": prompt}]
    response = await llm_service.complete(messages, temperature=0.1)

    try:
        suggestion = json.loads(response)
        return suggestion
    except json.JSONDecodeError:
        # Return fallback - suggest creating new account
        institution = statement_metadata.get("institution", "Unknown")
        account_type = statement_metadata.get("account_type", "Unknown")
        last4 = statement_metadata.get("account_number_last4", "")

        account_name = f"{institution} {account_type.title()}"
        if last4:
            account_name += f" (...{last4})"

        return {
            "suggested_account_id": None,
            "confidence": 0.0,
            "reasoning": "Unable to parse AI response",
            "should_create_new": True,
            "suggested_account_name": account_name,
        }


async def get_user_financial_context(user_id: str) -> Dict[str, Any]:
    """
    Get user's financial context for AI processing.
    """
    # TODO: Implement actual database queries
    # This is a placeholder that returns mock data

    return {
        "account_count": 0,
        "current_month_spending": 0,
        "previous_month_spending": 0,
        "budgets": [],
        "top_categories": [],
        "recent_transactions": [],
    }
