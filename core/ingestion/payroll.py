import pandas as pd
from pathlib import Path
from normalizer import assign_role_visibility, validate_schema


def load_payroll(path):
    df = pd.read_csv(path)

    # Aggregate to department-month level
    dept_monthly = df.groupby(['department', 'month']).agg(
        amount=('total_cost', 'sum'),
        headcount=('employee_id', 'count'),
        avg_salary=('base_salary', 'mean')
    ).reset_index()

    # All new columns on dept_monthly from here
    dept_monthly['date'] = pd.to_datetime(dept_monthly['month'] + '-01').dt.strftime('%Y-%m-%d')

    dept_monthly['year'] = pd.to_datetime(dept_monthly['date']).dt.year.astype(str)
    dept_monthly['gl_code'] = '6000'
    dept_monthly['gl_category'] = 'Payroll & Benefits'
    dept_monthly['description'] = dept_monthly.apply(
        lambda row: f"{row['department']} department payroll for {row['month']} "
                    f"— {row['headcount']} employees, "
                    f"avg base salary ${round(row['avg_salary'] / 1000) * 1000:,.0f}",axis=1)
    dept_monthly['transaction_type'] = 'payroll'
    dept_monthly['vendor'] = None
    dept_monthly['source'] = 'payroll'
    dept_monthly['role_visibility'] = dept_monthly.apply(lambda row: assign_role_visibility(row['transaction_type'], row['department']),axis=1)

    # Drop avg_salary — not in unified schema
    dept_monthly = dept_monthly.drop(columns=['avg_salary', 'headcount'])

    dept_monthly = validate_schema(dept_monthly)

    print(f"✅ Payroll: {len(dept_monthly)} rows loaded")
    return dept_monthly



if __name__ == '__main__':
    curr_dir = Path(__file__).parent
    file_path = curr_dir.parent.parent / 'data/raw/payroll.csv'
    load_payroll(file_path)


