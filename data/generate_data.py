from datetime import datetime as dt
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()


def generate_payroll():
    departments = {
        "Engineering": {
            "count": 18,
            "salary_range": (120_000, 180_000),
            "roles": ["Software Engineer", "Senior Software Engineer", "Staff Engineer", "DevOps Engineer"],
        },
        "Sales": {
            "count": 10,
            "salary_range": (80_000, 120_000),
            "roles": ["Account Executive", "Sales Development Rep", "Sales Manager"],
        },
        "Marketing": {
            "count": 6,
            "salary_range": (75_000, 110_000),
            "roles": ["Marketing Manager", "Demand Generation Specialist", "Content Strategist"],
        },
        "Product": {
            "count": 5,
            "salary_range": (110_000, 150_000),
            "roles": ["Product Manager", "Senior Product Manager", "Product Designer"],
        },
        "Operations": {
            "count": 7,
            "salary_range": (65_000, 95_000),
            "roles": ["Operations Manager", "People Operations Specialist", "IT Administrator"],
        },
        "Finance": {
            "count": 4,
            "salary_range": (85_000, 120_000),
            "roles": ["Financial Analyst", "Controller", "Accounting Manager"],
        },
    }

    employees = []
    next_employee_id = 1

    for department, details in departments.items():
        min_salary, max_salary = details["salary_range"]

        for index in range(details["count"]):
            salary_progress = 0.12 + (0.43 * index / max(details["count"] - 1, 1))
            annual_salary = min_salary + ((max_salary - min_salary) * salary_progress)

            employees.append(
                {
                    "employee_id": f"E{next_employee_id:03d}",
                    "department": department,
                    "role": details["roles"][index % len(details["roles"])],
                    "annual_salary": annual_salary,
                    "hire_date": dt(2023, 1, 1),
                }
            )
            next_employee_id += 1

    rows = []

    for month_start in pd.date_range("2023-01-01", "2025-12-01", freq="MS"):
        year = month_start.year

        for employee in employees:
            annual_salary = employee["annual_salary"] * (1.10 ** (year - 2023))
            monthly_base_salary = annual_salary / 12
            benefits = monthly_base_salary * 0.20
            sales_commission = monthly_base_salary * 0.10 if employee["department"] == "Sales" else 0
            q4_bonus = annual_salary * 0.15 if month_start.month == 12 else 0
            bonus = sales_commission + q4_bonus

            rows.append(
                {
                    "month": month_start.date().strftime("%Y-%m"),
                    "employee_id": employee["employee_id"],
                    "department": employee["department"],
                    "role": employee["role"],
                    "base_salary": round(monthly_base_salary, 2),
                    "bonus": round(bonus, 2),
                    "benefits": round(benefits, 2),
                    "total_cost": round(monthly_base_salary + benefits + bonus, 2),
                }
            )
    return pd.DataFrame(rows)


def generate_general_ledger():
    gl_accounts = {
        "6000": "Payroll & Benefits",
        "6100": "Cloud Infrastructure",
        "6200": "SaaS Tools & Subscriptions",
        "6300": "Sales & Marketing",
        "6400": "Travel & Entertainment",
        "6500": "Professional Services",
        "6600": "Office & Facilities",
        "6700": "R&D Expenses",
        "8000": "Accounts Receivable",
    }

    rows = []
    transaction_number = 1
    opex_scale = 0.844
    payroll = generate_payroll()
    payroll["month"] = pd.to_datetime(payroll["month"])

    def add_transaction(
        date,
        department,
        gl_code,
        description,
        amount,
        vendor,
        transaction_type="expense",
    ):
        nonlocal transaction_number

        if transaction_type == "expense" and gl_code != "6000":
            amount *= opex_scale

        rows.append(
            {
                "date": pd.to_datetime(date).date(),
                "transaction_id": f"GL{transaction_number:06d}",
                "department": department,
                "gl_code": gl_code,
                "gl_category": gl_accounts[gl_code],
                "description": description,
                "amount": round(amount, 2),
                "vendor": vendor,
                "transaction_type": transaction_type,
            }
        )
        transaction_number += 1

    customer_mix = {
        "Acme Analytics": 0.26,
        "Northstar Health": 0.21,
        "Brightline Retail": 0.18,
        "Summit Logistics": 0.15,
        "Cobalt Financial": 0.11,
        "Helio Education": 0.09,
    }
    starting_mrr = 85_000
    ending_mrr = 271_423
    month_count = len(pd.date_range("2023-01-01", "2025-12-01", freq="MS"))
    monthly_growth_rate = (ending_mrr / starting_mrr) ** (1 / (month_count - 1)) - 1

    for month_index, month_start in enumerate(pd.date_range("2023-01-01", "2025-12-01", freq="MS")):
        year = month_start.year
        month = month_start.month
        quarter = ((month - 1) // 3) + 1
        quarter_index = ((year - 2023) * 4) + quarter - 1
        month_end = month_start + pd.offsets.MonthEnd(0)
        month_payroll = payroll[payroll["month"] == month_start]
        headcount = month_payroll["employee_id"].nunique()

        for row in month_payroll.itertuples(index=False):
            add_transaction(
                month_end,
                row.department,
                "6000",
                f"{month_start:%B %Y} payroll for {row.employee_id}",
                row.total_cost,
                "Gusto",
            )

        cloud_growth = 1.15 ** quarter_index
        q3_engineering_push = 1.12 if quarter == 3 else 1.0
        for service_index in range(25):
            add_transaction(
                month_start.replace(day=(service_index % 20) + 3),
                "Engineering",
                "6100",
                f"AWS usage line {service_index + 1}: compute, storage, and observability",
                (760 + (service_index * 19)) * cloud_growth * q3_engineering_push,
                "AWS",
            )
        for service_index in range(5):
            add_transaction(
                month_start.replace(day=6 + service_index),
                "Product",
                "6100",
                f"GCP analytics workload {service_index + 1}",
                (620 + (service_index * 85)) * cloud_growth,
                "GCP",
            )

        saas_lines = [
            ("Operations", "Slack", "Company Slack workspace subscription", 16 * headcount),
            ("Operations", "Notion", "Notion knowledge base seats", 12 * headcount),
            ("Operations", "Zoom", "Zoom business conferencing licenses", 18 * headcount),
            ("Sales", "Salesforce", "Salesforce CRM seats and automation", 82 * headcount),
            ("Finance", "Stripe", "Stripe billing and revenue tooling", 1_100 * (1.10 ** (year - 2023))),
            ("Engineering", "GitHub", "GitHub source control and CI seats", 24 * headcount),
            ("Product", "Figma", "Figma product design seats", 650 * (1.08 ** (year - 2023))),
        ]
        for line_index, (department, vendor, description, amount) in enumerate(saas_lines):
            add_transaction(
                month_start.replace(day=7 + line_index),
                department,
                "6200",
                description,
                amount,
                vendor,
            )

        add_transaction(
            month_start.replace(day=10),
            "Operations",
            "6600",
            "WeWork office rent and facilities",
            8_400 + (headcount * 85),
            "WeWork",
        )
        add_transaction(
            month_start.replace(day=11),
            "Operations",
            "6600",
            "Office supplies, snacks, and workplace services",
            2_100 * (1.08 ** (year - 2023)),
            "Staples",
        )
        add_transaction(
            month_start.replace(day=12),
            "Operations",
            "6600",
            "Distributed team equipment and shipping",
            1_650 * (1.10 ** (year - 2023)),
            "Apple",
        )

        if month == 1:
            add_transaction(
                month_start.replace(day=15),
                "Sales",
                "6200",
                "Annual Salesforce CRM contract renewal",
                42_000 * (1.18 ** (year - 2023)),
                "Salesforce",
            )

        if quarter == 1:
            marketing_campaign = 6_500
            sales_travel = 3_500
        elif quarter == 2:
            marketing_campaign = 18_000
            sales_travel = 6_500
        elif quarter == 3:
            marketing_campaign = 12_500
            sales_travel = 8_000
        else:
            marketing_campaign = 22_000
            sales_travel = 9_500

        if year >= 2024:
            marketing_campaign *= 1.18
            sales_travel *= 1.25
        if year >= 2025:
            marketing_campaign *= 1.15
            sales_travel *= 1.10

        marketing_vendors = ["Google Ads", "LinkedIn", "HubSpot", "Clearbit", "Webflow", "Customer.io", "Sendoso"]
        for campaign_index, vendor in enumerate(marketing_vendors):
            add_transaction(
                month_start.replace(day=12 + campaign_index),
                "Marketing",
                "6300",
                f"Q{quarter} campaign spend: {vendor}",
                marketing_campaign / len(marketing_vendors),
                vendor,
            )

        travel_vendors = ["Ramp", "Delta", "Marriott", "Uber"]
        for travel_index, vendor in enumerate(travel_vendors):
            add_transaction(
                month_start.replace(day=18 + travel_index),
                "Sales",
                "6400",
                f"Q{quarter} customer travel and field expense: {vendor}",
                sales_travel / len(travel_vendors),
                vendor,
            )

        if quarter == 3:
            rd_monthly = 13_500 * (1.12 ** (year - 2023))
        else:
            rd_monthly = 8_500 * (1.08 ** (year - 2023))
        for rd_index, vendor in enumerate(["Toptal", "UserTesting", "Linear", "Datadog", "Sentry", "OpenAI", "BrowserStack"]):
            add_transaction(
                month_start.replace(day=20 + (rd_index % 7)),
                "Engineering" if rd_index != 1 else "Product",
                "6700",
                f"Product research and development expense: {vendor}",
                rd_monthly / 7,
                vendor,
            )

        if (year, month) in [(2023, 8), (2024, 8), (2025, 8)]:
            add_transaction(
                month_start.replace(day=22),
                "Operations",
                "6400",
                f"{year} annual company retreat",
                38_000 * (1.12 ** (year - 2023)),
                "Airbnb",
            )

        if (year, month) == (2024, 2):
            add_transaction(
                month_start.replace(day=14),
                "Operations",
                "6600",
                "Office expansion buildout, deposits, and furniture",
                95_000,
                "WeWork",
            )

        if (year, month) == (2023, 5):
            add_transaction(
                month_start.replace(day=16),
                "Finance",
                "6500",
                "Series A fundraising legal diligence and closing costs",
                72_000,
                "Cooley",
            )

        if month in [3, 6, 9, 12]:
            add_transaction(
                month_start.replace(day=25),
                "Finance",
                "6500",
                "Quarterly accounting review and tax advisory",
                8_500 * (1.08 ** (year - 2023)),
                "Deloitte",
            )
        add_transaction(
            month_start.replace(day=24),
            "Finance",
            "6500",
            "Monthly bookkeeping and controller advisory",
            4_500 * (1.06 ** (year - 2023)),
            "Pilot",
        )
        add_transaction(
            month_start.replace(day=26),
            "Finance",
            "6500",
            "Employment counsel and contract review",
            3_800 * (1.06 ** (year - 2023)),
            "Cooley",
        )

        mrr = starting_mrr * ((1 + monthly_growth_rate) ** month_index)
        for customer, share in customer_mix.items():
            add_transaction(
                month_end,
                "Sales",
                "8000",
                f"MRR invoice: {customer}",
                mrr * share,
                "Stripe",
                transaction_type="revenue",
            )
        add_transaction(
            month_end,
            "Sales",
            "8000",
            "Implementation and onboarding fees",
            8_350,
            "Stripe",
            transaction_type="revenue",
        )

    return pd.DataFrame(rows)


def generate_budget():
    department_allocations = {
        "Engineering": 0.35,
        "Sales": 0.20,
        "Marketing": 0.15,
        "Product": 0.10,
        "Operations": 0.12,
        "Finance": 0.08,
    }
    payroll_allocation = 0.65
    operating_mix = {
        "Engineering": {"Cloud Infrastructure": 0.60, "R&D Expenses": 0.40},
        "Sales": {
            "SaaS Tools & Subscriptions": 0.55,
            "Travel & Entertainment": 0.45,
        },
        "Marketing": {
            "Sales & Marketing": 0.80,
            "SaaS Tools & Subscriptions": 0.20,
        },
        "Product": {"Cloud Infrastructure": 0.75, "R&D Expenses": 0.25},
        "Operations": {
            "SaaS Tools & Subscriptions": 0.45,
            "Office & Facilities": 0.55,
        },
        "Finance": {
            "Professional Services": 0.85,
            "SaaS Tools & Subscriptions": 0.15,
        },
    }

    ledger = generate_general_ledger()
    ledger["date"] = pd.to_datetime(ledger["date"])
    expenses = ledger[ledger["transaction_type"] == "expense"].copy()
    expenses["year"] = expenses["date"].dt.year
    expenses["month"] = expenses["date"].dt.strftime("%Y-%m")
    expenses["expected_spend"] = expenses["amount"].abs()

    monthly_expected = (
        expenses.groupby(["year", "month"])["expected_spend"]
        .sum()
        .rename("expected_spend")
        .reset_index()
    )
    rows = []

    for month_start in pd.date_range("2023-01-01", "2025-12-01", freq="MS"):
        year = month_start.year
        month = month_start.strftime("%Y-%m")

        expected_match = monthly_expected[
            (monthly_expected["year"] == year) & (monthly_expected["month"] == month)
        ]
        expected_spend = expected_match["expected_spend"].iloc[0]
        total_budget = expected_spend * 1.10

        for department, department_share in department_allocations.items():
            department_budget = total_budget * department_share
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "department": department,
                    "gl_category": "Payroll & Benefits",
                    "budgeted_amount": round(department_budget * payroll_allocation, 2),
                }
            )

            department_operating_budget = department_budget * (1 - payroll_allocation)
            for gl_category, category_share in operating_mix[department].items():
                rows.append(
                    {
                        "year": year,
                        "month": month,
                        "department": department,
                        "gl_category": gl_category,
                        "budgeted_amount": round(department_operating_budget * category_share, 2),
                    }
                )

    return pd.DataFrame(rows)


def generate_invoices():
    rows = []
    invoice_number = 1

    def payment_delay(index, invoice_type):
        if invoice_type == "AR":
            delay_pattern = [-4, 0, 3, 7, 15, 0]
        else:
            delay_pattern = [-2, 0, 4, 10, 0, 18]

        return delay_pattern[index % len(delay_pattern)]

    def add_invoice(
        date,
        invoice_type,
        vendor_or_customer,
        department,
        amount,
        due_date,
    ):
        nonlocal invoice_number

        delay_days = payment_delay(invoice_number, invoice_type)
        paid_date = pd.to_datetime(due_date) + pd.Timedelta(days=delay_days)
        status = "paid_late" if paid_date.date() > pd.to_datetime(due_date).date() else "paid"

        rows.append(
            {
                "invoice_id": f"INV{invoice_number:06d}",
                "date": pd.to_datetime(date).date(),
                "type": invoice_type,
                "vendor_or_customer": vendor_or_customer,
                "department": department,
                "amount": round(amount, 2),
                "status": status,
                "due_date": pd.to_datetime(due_date).date(),
                "paid_date": paid_date.date(),
            }
        )
        invoice_number += 1

    customers = {
        "Acme Analytics": 0.26,
        "Northstar Health": 0.21,
        "Brightline Retail": 0.18,
        "Summit Logistics": 0.15,
        "Cobalt Financial": 0.11,
        "Helio Education": 0.09,
    }
    starting_mrr = 85_000
    ending_mrr = 271_423
    month_count = len(pd.date_range("2023-01-01", "2025-12-01", freq="MS"))
    monthly_growth_rate = (ending_mrr / starting_mrr) ** (1 / (month_count - 1)) - 1

    for month_index, month_start in enumerate(pd.date_range("2023-01-01", "2025-12-01", freq="MS")):
        mrr = starting_mrr * ((1 + monthly_growth_rate) ** month_index)
        invoice_date = month_start.replace(day=1)
        due_date = invoice_date + pd.Timedelta(days=30)

        for customer, share in customers.items():
            add_invoice(
                invoice_date,
                "AR",
                customer,
                "Sales",
                mrr * share,
                due_date,
            )
        add_invoice(
            invoice_date,
            "AR",
            "Implementation Services",
            "Sales",
            8_350,
            due_date,
        )

    ledger = generate_general_ledger()
    ledger["date"] = pd.to_datetime(ledger["date"])
    ap_entries = ledger[
        (ledger["transaction_type"] == "expense") & (ledger["gl_code"].astype(str) != "6000")
    ].copy()
    ap_entries["year"] = ap_entries["date"].dt.year
    ap_entries["month"] = ap_entries["date"].dt.month
    ap_entries["amount"] = ap_entries["amount"].abs()
    vendor_rollups = {
        "Google Ads": "Marketing Vendor Bundle",
        "LinkedIn": "Marketing Vendor Bundle",
        "HubSpot": "Marketing Vendor Bundle",
        "Clearbit": "Marketing Vendor Bundle",
        "Webflow": "Marketing Vendor Bundle",
        "Customer.io": "Marketing Vendor Bundle",
        "Sendoso": "Marketing Vendor Bundle",
        "Ramp": "Travel Card",
        "Delta": "Travel Card",
        "Marriott": "Travel Card",
        "Uber": "Travel Card",
        "Toptal": "R&D Vendor Bundle",
        "UserTesting": "R&D Vendor Bundle",
        "Linear": "R&D Vendor Bundle",
        "Datadog": "R&D Vendor Bundle",
        "Sentry": "R&D Vendor Bundle",
        "OpenAI": "R&D Vendor Bundle",
        "BrowserStack": "R&D Vendor Bundle",
    }
    ap_entries["invoice_vendor"] = ap_entries["vendor"].replace(vendor_rollups)
    ap_invoices = (
        ap_entries.groupby(["year", "month", "invoice_vendor"], as_index=False)
        .agg({"date": "min", "department": "first", "amount": "sum"})
    )

    for entry in ap_invoices.itertuples(index=False):
        invoice_date = entry.date
        due_date = invoice_date + pd.Timedelta(days=30)
        add_invoice(
            invoice_date,
            "AP",
            entry.invoice_vendor,
            entry.department,
            entry.amount,
            due_date,
        )

    return pd.DataFrame(rows)


def generate_chart_of_accounts():
    accounts = [
        {
            "gl_code": "6000",
            "gl_category": "Payroll & Benefits",
            "account_type": "Expense",
            "description": "Employee salaries, commissions, bonuses, payroll taxes, and benefits.",
        },
        {
            "gl_code": "6100",
            "gl_category": "Cloud Infrastructure",
            "account_type": "Expense",
            "description": "Usage-based cloud hosting, storage, data processing, and platform infrastructure.",
        },
        {
            "gl_code": "6200",
            "gl_category": "SaaS Tools & Subscriptions",
            "account_type": "Expense",
            "description": "Software subscriptions and seat-based tools used to operate the business.",
        },
        {
            "gl_code": "6300",
            "gl_category": "Sales & Marketing",
            "account_type": "Expense",
            "description": "Demand generation, advertising, campaigns, events, and go-to-market programs.",
        },
        {
            "gl_code": "6400",
            "gl_category": "Travel & Entertainment",
            "account_type": "Expense",
            "description": "Customer travel, meals, conferences, team events, and company retreats.",
        },
        {
            "gl_code": "6500",
            "gl_category": "Professional Services",
            "account_type": "Expense",
            "description": "Legal, accounting, tax, fundraising, advisory, and consulting services.",
        },
        {
            "gl_code": "6600",
            "gl_category": "Office & Facilities",
            "account_type": "Expense",
            "description": "Office rent, coworking space, facilities, furniture, deposits, and buildout costs.",
        },
        {
            "gl_code": "6700",
            "gl_category": "R&D Expenses",
            "account_type": "Expense",
            "description": "Product research, prototyping, contractor engineering, testing, and experimentation.",
        },
        {
            "gl_code": "8000",
            "gl_category": "Accounts Receivable",
            "account_type": "Asset",
            "description": "Customer invoices and receivables for recurring SaaS subscription revenue.",
        },
    ]

    return pd.DataFrame(accounts)

def main():

    curr_dir = Path(__file__).parent
    raw_data_path = curr_dir / "raw"

    payroll_data = generate_payroll()
    print("payroll_data", payroll_data.shape)
    payroll_data.to_csv(raw_data_path / "payroll.csv", index=False)

    general_ledger_data = generate_general_ledger()
    print("general_ledger_data", general_ledger_data.shape)
    general_ledger_data.to_csv(raw_data_path / "general_ledger.csv", index=False)

    budget_data = generate_budget()
    print("budget_data", budget_data.shape)
    budget_data.to_csv(raw_data_path / "budget.csv", index=False)

    invoice_data = generate_invoices()
    print("invoice_data", invoice_data.shape)
    invoice_data.to_csv(raw_data_path / "invoice.csv", index=False)

    chart_of_accounts = generate_chart_of_accounts()
    print("chart_of_accounts", chart_of_accounts.shape)
    chart_of_accounts.to_csv(raw_data_path / "chart_of_accounts.csv", index=False)

if __name__ == "__main__":
    main()
