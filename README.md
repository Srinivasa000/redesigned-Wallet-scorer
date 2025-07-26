# Wallet Risk Scorer

A Python-based tool to analyze Ethereum wallet addresses from a CSV list and assign them a risk score from 0 to 1000 based on their on-chain transaction history.

---

## How It Works

This project provides a simple yet effective framework for on-chain risk analysis. The methodology involves three key steps:

1.  **Data Collection**: Fetches the complete transaction history for each wallet address using the **Etherscan API**.
2.  **Feature Engineering**: From the raw transaction data, it calculates several key risk indicators, including wallet age, transaction frequency, average transaction value, and the number of unique counterparties.
3.  **Scoring**: A weighted model is applied to the calculated features. The features are first normalized to prevent any single metric from dominating the result, and a final score is scaled to a 0-1000 range for easy interpretation.

---

## Getting Started

Follow these instructions to get the project running on your local machine.

### Prerequisites

* Python 3.8+
* An active **Etherscan API Key**. You can get a free key from the [Etherscan website](https://etherscan.io/myapikey).

### Setup & Installation

1.  **Clone the repository or download the source code.**

2.  **Create and activate a virtual environment:**
    ```bash
    # Create the virtual environment
    python -m venv venv

    # Activate on Windows
    .\venv\Scripts\activate

    # Activate on macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install pandas requests python-dotenv
    ```

4.  **Prepare your wallet list:**
    * Make sure you have a CSV file named `wallets.csv` in the root of the project directory.
    * This file should contain one wallet address per row in the first column.

5.  **Set up your API Key:**
    * Create a file named `.env` in the root of the project directory.
    * Add your Etherscan API key to this file in the following format:
        ```
        ETHERSCAN_API_KEY="YourApiKeyHere"
        ```

---

## Usage

Once the setup is complete, run the script from your terminal:

```bash
python scorer.py
