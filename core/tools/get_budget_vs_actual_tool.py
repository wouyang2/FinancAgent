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

class BudgetVsActualsInput(BaseModel):
    month: Optional[str] = Field(None, description="Month in YYYY-MM format")
    year: Optional[str] = Field(None)
    departments: Optional[list[str]] = Field(None, description="List if departments to filter")
    variance_threshold: Optional[float] = Field(None, description="Variance threshold")
    user_role: str = None       
    user_department: str = None

class BudgetVsActualsTool(BaseTool):
    name: str = "get_budget_vs_actual"
    description: str = """
                        Returns comparison of budget and actual spending. 
                        Use when the user ask about Budget vs Actual Spending. 
                    """
    args_schema : type[BaseModel] = BudgetVsActualsInput

    expense_df: Any = None
    budget_df: Any = None

    def _run(self, month = None, year = None, departments: list[str] = None, variance_threshold = None):
        
        actual = apply_filters(self.expense_df, departments or [], [], self.user_role, self.user_department)
        budgeted = apply_filters(self.budget_df, departments or [], [], self.user_role, self.user_department)
        variance_threshold = variance_threshold or 0.10 

        if year and not month:
            actual   = actual[actual['year'] == year]
            budgeted = budgeted[budgeted['year'] == year]
        elif month:
            actual   = actual[actual['month'] == month]
            budgeted = budgeted[budgeted['month'] == month]


        actual_agg = actual.groupby(['department', 'gl_category'])['amount'].sum().reset_index()
        actual_agg.rename(columns={'amount': 'actual'}, inplace=True)

        budget_agg = budgeted.groupby(['department', 'gl_category'])['amount'].sum().reset_index()
        budget_agg.rename(columns={'amount': 'budgeted'}, inplace=True)

        merged = pd.merge(budget_agg, actual_agg, on=['department', 'gl_category'], how='outer').fillna(0)

        merged['variance'] = merged['actual'] - merged['budgeted']
        merged['variance_pct'] = (merged['variance'] / merged['budgeted'].replace(0, 1))
        merged['status'] = merged['variance_pct'].apply(
            lambda x: f"⚠️ {x*100:.1f}% over" if x > variance_threshold
                    else f"✅ {abs(x)*100:.1f}% under" if x < -variance_threshold
                    else f"🟢 on track ({x*100:.1f}%)")
        
        flagged    = merged[merged['variance_pct'].abs() > variance_threshold]
        on_track   = merged[merged['variance_pct'].abs() <= variance_threshold]

        # Build time period label
        if month:
            period = month
        elif year:
            period = f"Full Year {year}"
        else:
            period = "All Time"

        # Build flagged rows
        if len(flagged) > 0:
            flagged_lines = "\n".join(
                f"  {row['department']:<20} {row['gl_category']:<30} "
                f"Budgeted: ${row['budgeted']:>10,.0f}  "
                f"Actual: ${row['actual']:>10,.0f}  "
                f"Variance: ${row['variance']:>+10,.0f}  {row['status']}"
                for _, row in flagged.sort_values('variance_pct', ascending=False).iterrows()
            )
        else:
            flagged_lines = "  None — all departments within threshold"

        # Summary totals
        total_budgeted = merged['budgeted'].sum()
        total_actual   = merged['actual'].sum()
        total_variance = total_actual - total_budgeted
        total_variance_pct = (total_variance / total_budgeted * 100) if total_budgeted > 0 else 0

        return f"""
        BUDGET VS ACTUALS — {period}
        {'─' * 60}
        Viewing as: {self.user_role}
        Variance threshold: {variance_threshold*100:.0f}%

        OVERALL:
        Total Budgeted:  ${total_budgeted:>12,.0f}
        Total Actual:    ${total_actual:>12,.0f}
        Net Variance:    ${total_variance:>+12,.0f} ({total_variance_pct:+.1f}%)

        FLAGGED ITEMS ({len(flagged)} items exceeding {variance_threshold*100:.0f}% threshold):
        {flagged_lines}

        ON TRACK: {len(on_track)} line items within threshold
        """.strip()
