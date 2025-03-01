import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Create sample employee data
departments = ['Data Science', 'Engineering', 'Marketing', 'Sales', 'HR']
locations = ['New York', 'San Francisco', 'Chicago', 'Austin', 'Seattle']
education = ['Bachelors', 'Masters', 'PhD', 'High School', 'Associates']

# Generate 100 employees
n = 100
data = {
    'employee_id': range(1001, 1001 + n),
    'name': [f'Employee {i}' for i in range(1, n + 1)],
    'department': np.random.choice(departments, n),
    'location': np.random.choice(locations, n),
    'salary': np.random.randint(50000, 150000, n),
    'years_of_experience': np.random.randint(0, 20, n),
    'education': np.random.choice(education, n),
    'hire_date': pd.date_range(start='2015-01-01', periods=n, freq='W'),
    'performance_score': np.random.uniform(1, 5, n).round(1),
    'projects_completed': np.random.randint(0, 50, n)
}

# Create some NaN values
indices = np.random.choice(range(n), 10, replace=False)
for idx in indices:
    data['performance_score'][idx] = np.nan

# Convert to DataFrame
employee_df = pd.DataFrame(data)
employee_df

