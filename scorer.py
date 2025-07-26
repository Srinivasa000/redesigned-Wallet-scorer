import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv
from datetime import datetime

# --- 1. SETUP ---
# Load environment variables (your API key)
load_dotenv()
API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_API_URL = "https://api.etherscan.io/api"

# --- 2. DATA COLLECTION ---
def get_transactions(wallet_address):
    """Fetches the normal transaction history for a given wallet address."""
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": API_KEY
    }
    try:
        response = requests.get(ETHERSCAN_API_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if data["status"] == "1":
            return data["result"]
        else:
            # Handles cases where the API returns an error message (e.g., invalid address)
            print(f"API Error for {wallet_address}: {data['message']}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"HTTP Request failed for {wallet_address}: {e}")
        return []

# --- 3. FEATURE ENGINEERING ---
def calculate_features(transactions, wallet_address):
    """Calculates risk features from a list of transactions."""
    if not transactions:
        # Return default zero-values if no transactions are found
        return {
            "wallet_address": wallet_address, "wallet_age_days": 0, "tx_count": 0,
            "avg_eth_sent": 0, "unique_recipients": 0,
            # Mocked data for demonstration, as this is complex to get from basic tx lists
            "mock_liquidations": 0, "mock_high_ltv_borrows": 0
        }

    df = pd.DataFrame(transactions)
    # Convert data types for calculations
    # FIX APPLIED HERE: Use .astype(float) to handle very large numbers (Wei)
    df['value'] = df['value'].astype(float) / 1e18 # Convert Wei to Ether
    df['timeStamp'] = pd.to_datetime(df['timeStamp'], unit='s')

    # Feature 1: Wallet Age
    first_tx_date = df['timeStamp'].min()
    wallet_age_days = (datetime.now() - first_tx_date).days

    # Feature 2: Transaction Count
    tx_count = len(df)

    # Feature 3: Average ETH Sent (a proxy for financial activity)
    sent_tx = df[df['from'].str.lower() == wallet_address.lower()]
    avg_eth_sent = sent_tx['value'].mean() if not sent_tx.empty else 0

    # Feature 4: Unique Recipients (a proxy for network interaction complexity)
    unique_recipients = sent_tx['to'].nunique()

    # NOTE: Getting accurate LTV and liquidation data requires decoding transaction inputs
    # with specific DeFi protocol ABIs, which is very complex.
    # We will MOCK these features to demonstrate the scoring logic.
    # In a real-world scenario, you would use a service like The Graph or Dune Analytics for this.
    mock_liquidations = wallet_address[-1] in '012' # Example: 30% chance of having a liquidation
    mock_high_ltv_borrows = wallet_address[-2] in 'abc' # Example: 20% chance of high LTV borrows

    return {
        "wallet_address": wallet_address,
        "wallet_age_days": wallet_age_days,
        "tx_count": tx_count,
        "avg_eth_sent": avg_eth_sent,
        "unique_recipients": unique_recipients,
        "mock_liquidations": int(mock_liquidations), # Convert boolean to 0 or 1
        "mock_high_ltv_borrows": int(mock_high_ltv_borrows)
    }

# --- 4. RISK SCORING ---
def calculate_risk_scores(features_df):
    """Applies a weighted model to calculate a risk score from 0 to 1000."""
    # Define weights for each feature. Higher weight = more impact on score.
    # Negative weights mean "good" behavior (e.g., older wallet is less risky).
    weights = {
        "wallet_age_days": -0.1,      # Older wallet is less risky
        "tx_count": 0.15,             # More transactions can be neutral or slightly risky
        "avg_eth_sent": 0.2,          # Higher average value sent might indicate higher capacity/risk
        "unique_recipients": 0.25,    # High number of recipients could be a mixer/distributor
        "mock_liquidations": 0.5,     # Liquidations are a strong indicator of risk
        "mock_high_ltv_borrows": 0.4  # High LTV is a strong indicator of risk
    }

    # Normalize features to be on a scale of 0 to 1
    # This ensures that one feature doesn't dominate the score just because its raw values are large
    normalized_df = features_df.copy()
    for feature in weights.keys():
        min_val = features_df[feature].min()
        max_val = features_df[feature].max()
        if (max_val - min_val) > 0:
            normalized_df[feature] = (features_df[feature] - min_val) / (max_val - min_val)
        else:
            normalized_df[feature] = 0 # Handle case where all values for a feature are the same

    # Calculate raw score
    raw_score = (normalized_df[list(weights.keys())] * pd.Series(weights)).sum(axis=1)

    # Scale score to 0-1000
    min_score = raw_score.min()
    max_score = raw_score.max()
    final_score = 1000 * (raw_score - min_score) / (max_score - min_score)

    return final_score.astype(int)


# --- 5. MAIN EXECUTION ---
if __name__ == "__main__":
    print("🚀 Starting Wallet Risk Scorer...")

    # Load wallet addresses from CSV
    try:
        wallets_df = pd.read_csv("wallets.csv")
        wallet_addresses = wallets_df.iloc[:, 0].tolist() # Assumes wallets are in the first column
    except FileNotFoundError:
        print("Error: `wallets.csv` not found. Please download it and place it in the project folder.")
        exit()

    all_features = []
    # Process each wallet (with a rate limit delay)
    for i, address in enumerate(wallet_addresses):
        print(f"Processing wallet {i+1}/{len(wallet_addresses)}: {address}")
        transactions = get_transactions(address)
        features = calculate_features(transactions, address)
        all_features.append(features)
        time.sleep(0.2) # IMPORTANT: Respect Etherscan's API rate limit (5 calls/sec for free tier)

    # Create a DataFrame from the collected features
    features_df = pd.DataFrame(all_features).set_index("wallet_address")
    features_df.fillna(0, inplace=True) # Replace any NaN values with 0

    print("\n✅ Feature calculation complete. Calculating risk scores...")

    # Calculate scores
    scores = calculate_risk_scores(features_df)

    # Create the final CSV output
    output_df = pd.DataFrame({"wallet_id": features_df.index, "score": scores})
    output_df.to_csv("risk_scores.csv", index=False)

    print("\n🎉 Success! Results saved to `risk_scores.csv`.")
    print(output_df.head())