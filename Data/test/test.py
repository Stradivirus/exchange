import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables and connect to DB
load_dotenv('.env')  # Specify the actual location of .env
PG_HOST = os.getenv("PG_HOST")
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}")

# Load data (last 1 year)
query = """
SELECT e.date, e.usd, e.jpy, e.eur, e.cny,
       c.gold, c.silver, c.copper
FROM exchange e
JOIN commodities c ON e.date = c.date
WHERE e.date >= (SELECT MAX(date) FROM exchange) - INTERVAL '365 days'
ORDER BY e.date
"""
df = pd.read_sql(query, engine)

# Interpolate missing values (linear) and sort
df = df.sort_values('date').reset_index(drop=True)
df = df.interpolate(method='linear')

# Correlation analysis
corr = df[['usd', 'jpy', 'eur', 'cny', 'gold', 'silver', 'copper']].corr()
print("=== Correlation Coefficients ===")
print(corr)

# Time series graphs (with English labels, and save as files)
plt.figure(figsize=(14, 7))
for col in ['usd', 'jpy', 'eur', 'cny']:
    plt.plot(df['date'], df[col], label=col)
plt.legend()
plt.title('Exchange Rates (KRW base) Time Series')
plt.xlabel('Date')
plt.ylabel('Exchange Rate')
plt.tight_layout()
plt.savefig('exchange_rates_timeseries.png')
plt.close()

plt.figure(figsize=(14, 7))
for col in ['gold', 'silver', 'copper']:
    plt.plot(df['date'], df[col], label=col)
plt.legend()
plt.title('Gold/Silver/Copper Price Time Series')
plt.xlabel('Date')
plt.ylabel('Price')
plt.tight_layout()
plt.savefig('metal_prices_timeseries.png')
plt.close()

# Scatter plot and correlation heatmap for exchange rates and metal prices (in English, and save as files)
sns.pairplot(df[['usd', 'jpy', 'eur', 'cny', 'gold', 'silver', 'copper']])
plt.suptitle('Exchange Rate & Metal Price Scatter', y=1.02)
plt.savefig('exchange_metal_pairplot.png')
plt.close()

plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap='coolwarm')
plt.title('Correlation Heatmap')
plt.tight_layout()
plt.savefig('correlation_heatmap.png')
plt.close()

# Summary statistics
print("\n=== Summary Statistics ===")
print(df[['usd', 'jpy', 'eur', 'cny', 'gold', 'silver', 'copper']].describe())