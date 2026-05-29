import pandas as pd
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Any
from utils import apply_filters
from dotenv import load_dotenv
load_dotenv()


class SpendingSummaryInput(BaseModel):
    """Input schema — Pydantic validates all inputs automatically."""
    month: Optional[str] = Field(None, description="Month in YYYY-MM format")
    year: Optional[str] = Field(None, description="Year e.g. '2024'")
    departments: Optional[list[str]] = Field(None, description="List of departments to filter")
    gl_categories: Optional[list[str]] = Field(None, description="List of GL categories to filter")

class SpendingSummaryTool(BaseTool):

    name: str = 'get_spending_summary'
    description: str = """
        Returns spending summary for a given time period.
        Use when the user asks about total spend, cost breakdown,
        or department expenses.
    """
    args_schema: type[BaseModel] = SpendingSummaryInput

    user_role : str = None
    user_department : str = None
    df: Any = None

    def _run(self, month = None, year = None, departments = None, gl_categories = None):

        filtered = apply_filters(self.df, departments, gl_categories, self.user_role, self.user_department)

        if year and not month:
            filtered = filtered[filtered['year'] == year]
        elif month:
            filtered = filtered[filtered['month'] == month]

        total = filtered['amount'].sum()
        by_dept = filtered.groupby('department')['amount'].sum()
        by_category = filtered.groupby('gl_category')['amount'].sum()

        # Build time period label
        if month:
            period = month
        elif year:
            period = f"Full Year {year}"
        else:
            period = "All Time"

        # Build department breakdown
        dept_breakdown = "\n".join(
            f"  {dept:<20} ${amount:>12,.2f}"
            for dept, amount in by_dept.sort_values(ascending=False).items()
        )

        # Build category breakdown
        category_breakdown = "\n".join(
            f"  {cat:<30} ${amount:>12,.2f}"
            for cat, amount in by_category.sort_values(ascending=False).items()
        )

        # Role context line
        role_context = f"Viewing as: {self.user_role}"
        if self.user_role == 'Department Head':
            role_context += f" ({self.user_department} department only)"

        return f"""
        SPENDING SUMMARY — {period}
        {'─' * 50}
        {role_context}

        Total Spend: ${total:,.2f}

        By Department:
        {dept_breakdown}

        By GL Category:
        {category_breakdown}

        Transactions analyzed: {len(filtered)}
        """.strip()

    