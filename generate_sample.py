import pandas as pd
import numpy as np

# 1. Generate 1000 normal rows
np.random.seed(42)
data = {
    'Transaction_ID': range(1000, 2000),
    'Customer_Age': np.random.normal(35, 12, 1000).astype(int),
    'Purchase_Amount': np.random.normal(120, 40, 1000),
    'Loyalty_Score': np.random.uniform(1, 10, 1000),
    'Email_Subscriber': np.random.choice(['Yes', 'No', np.nan], 1000),
    'Shipping_State': np.random.choice(['NY', 'CA', 'TX', 'FL', 'IL', np.nan], 1000)
}
df = pd.DataFrame(data)

# 2. Inject Extreme Outliers (The "Anomalies")
df.loc[12, 'Customer_Age'] = 999         # Impossible age
df.loc[45, 'Customer_Age'] = -5          # Negative age
df.loc[105, 'Purchase_Amount'] = 50000.0 # Accidental massive charge
df.loc[500, 'Loyalty_Score'] = 999.0     # System glitch

# 3. Inject Missing Values (Nulls)
df.loc[20:60, 'Customer_Age'] = np.nan
df.loc[800:850, 'Purchase_Amount'] = np.nan

# 4. Inject Exact Duplicates
df = pd.concat([df, df.iloc[0:20]]) # Copies the first 20 rows and adds them to the bottom

# 5. Save the file
df.to_csv("sample_ecommerce_data.csv", index=False)
print(f"✅ Successfully created sample_ecommerce_data.csv with {len(df)} rows and {len(df.columns)} columns!")