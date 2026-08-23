import logging

from agent.x_agent import run_agent


# ==========================================
# Logging
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
)


# ==========================================
# Run X agent
# ==========================================

df = run_agent()


# ==========================================
# Inspect result
# ==========================================

print()

print("Dataset shape:")
print(df.shape)

print()

print("Columns:")
print(df.columns.tolist())

print()

print(df.head())