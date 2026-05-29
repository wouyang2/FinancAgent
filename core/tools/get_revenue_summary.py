import pandas as pd
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Any
from utils import apply_filters

from dotenv import load_dotenv
load_dotenv()


class RevenueSummaryInput(BaseModel):
    month: Optional[str] = Field(None, description="Month in YYYY-MM format")
    year: Optional[str] = Field(None, description="Year e.g. '2024'")
    vendors: Optional[list[str]] = Field(None, description="List of client/vendor names to filter")
    status: Optional[str] = Field(None, description="Payment status filter: 'paid' or 'paid_late'")


class RevenueSummaryTool(BaseTool):

    name: str = "get_revenue_summary"
    description: str = """
        Returns revenue summary for a given time period.
        Use when the user asks about total revenue, client billing,
        payment status, or income breakdown.
    """
    args_schema: type[BaseModel] = RevenueSummaryInput

    user_role: Optional[str] = None
    user_department: Optional[str] = None
    df: Any = None

    def _run(self, month=None, year=None, vendors=None, status=None):

        filtered = self.df.copy()

        if year and not month:
            filtered = filtered[filtered["year"] == int(year)]
        elif month:
            filtered = filtered[filtered["month"] == month]

        if vendors:
            filtered = filtered[filtered["vendor"].isin(vendors)]

        if status:
            filtered = filtered[filtered["status"] == status]

        if filtered.empty:
            return "No revenue data found for the given filters."

        total = filtered["amount"].sum()
        paid = filtered[filtered["status"] == "paid"]["amount"].sum()
        paid_late = filtered[filtered["status"] == "paid_late"]["amount"].sum()

        by_vendor = filtered.groupby("vendor")["amount"].sum().sort_values(ascending=False)
        by_month = filtered.groupby("month")["amount"].sum().sort_values()

        # Build period label
        if month:
            period = month
        elif year:
            period = f"Full Year {year}"
        else:
            period = "All Time"

        top_clients = "\n".join(
            f"  {vendor:<30} ${amount:>12,.2f}"
            for vendor, amount in by_vendor.head(10).items()
        )

        monthly_trend = "\n".join(
            f"  {m}   ${amount:>12,.2f}"
            for m, amount in by_month.items()
        )

        return f"""
REVENUE SUMMARY — {period}
{'─' * 50}
Viewing as: {self.user_role}

Total Revenue:    ${total:>12,.2f}
  Paid on time:  ${paid:>12,.2f}  ({paid / total * 100:.1f}%)
  Paid late:     ${paid_late:>12,.2f}  ({paid_late / total * 100:.1f}%)

TOP CLIENTS (by revenue):
{top_clients}

MONTHLY TREND:
{monthly_trend}

Invoices analyzed: {len(filtered)}
        """.strip()
