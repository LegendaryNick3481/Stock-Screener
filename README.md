# Stock Trading Bot

This project is a Python-based stock trading bot designed to automate a specific trading strategy. It integrates with the Fyers API for real-time market data and trade execution, and utilizes Selenium for scraping stock screening data from `screener.in`. The bot features a graphical user interface (GUI) built with `tkinter` to display live stock prices and profit/loss information.

## Features

*   **Automated Trading Strategy:** Implements a strategy to buy stocks that have increased by a certain percentage (e.g., 3%) and sell them at a target profit or stop-loss.
*   **Real-time Data:** Connects to the Fyers API via WebSockets for live stock price updates.
*   **Web Scraping:** Uses Selenium to scrape `screener.in` to generate a list of potential stocks to trade.
*   **GUI:** Provides a `tkinter` based interface to monitor live stock prices and trading performance.
*   **Market Hours Operation:** Designed to run during market hours and automatically squares off all positions at the end of the trading day.
*   **Flexible Start:** Includes scripts for starting the bot at market open or if the market has already been open for some time.

## Technologies Used

*   **Python:** The primary programming language.
*   **Fyers API (fyers_apiv3):** For real-time market data (WebSockets) and historical data.
*   **Selenium:** For web scraping `screener.in`.
*   **pandas:** For data manipulation and analysis.
*   **tkinter:** For building the graphical user interface.
*   **BeautifulSoup4:** (Likely used by screener.py for parsing HTML)

## Project Structure

*   `main.py`: Intended as the main entry point for the application (currently empty, a TODO for future development).
*   `login.py`: Handles authentication with the Fyers API to obtain and manage the access token.
*   `screener.py`: Script responsible for scraping stock data from `screener.in` to identify stocks for trading.
*   `fetch_open.py`: Fetches the opening prices for the selected stocks.
*   `web_socket.py`: The core trading logic. Establishes a WebSocket connection, updates the GUI with real-time data, and executes trades based on the defined strategy.
*   `web_socket_if_late.py`: A variant of `web_socket.py`, designed for scenarios where the bot starts after market open, attempting to buy stocks that have already met the initial price increase target.
*   `credentials.py`: Stores sensitive Fyers API credentials (client ID, secret key, redirect URL). **Ensure this file is properly secured and not committed to public repositories with actual credentials.**
*   `file_paths.py`: Likely defines paths for generated files and other resources.
*   `generatedFiles/`: Directory for storing generated data suchs as `access_token.txt`, `ticker_data.csv`, `screener_output.csv`, and log files.

## Getting Started

### Prerequisites

*   Python 3.x
*   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/LegendaryNick3481/Stock-Screener.git
    cd Stock-Screener
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install fyers_apiv3 pandas selenium beautifulsoup4
    ```

### Configuration

1.  **Fyers API Credentials:**
    *   Open `src/credentials.py`.
    *   Replace the placeholder values for `client_id`, `secret_key`, and `redirect_url` with your actual Fyers API credentials.

2.  **Screener Data:**
    *   The `screener.py` script requires manual intervention for logging into `screener.in`.
    *   Run the screener script:
        ```bash
        python src/screener.py
        ```
    *   Follow the prompts to log in to `screener.in`. This will generate `generatedFiles/ticker_data.csv`.

### Running the Application

1.  **Generate Access Token:**
    ```bash
    python src/login.py
    ```
    This will generate `generatedFiles/access_token.txt`.

2.  **Start the Trading Bot:**

    *   **If starting before market opens or at market open:**
        ```bash
        python src/web_socket.py
        ```

    *   **If starting after the market has been open for some time:**
        ```bash
        python src/web_socket_if_late.py
        ```

    This will launch the `tkinter` GUI and initiate the trading bot.

## Trading Strategy

The core trading strategy involves:
*   Identifying stocks that have shown a significant price increase (e.g., 3%) from their opening price.
*   Buying these stocks.
*   Setting a target profit and a stop-loss to manage trades.
*   Automatically squaring off all open positions at the end of the trading day.

## Future Enhancements (TODOs)

*   Implement logic in `main.py` to intelligently choose between `web_socket.py` and `web_socket_if_late.py` based on current market time.
*   Make the trading strategy parameters (e.g., percentage increase for buying, profit target, stop-loss) configurable.
*   Improve error handling and logging across all modules.
*   Add more robust testing.

## License

[Consider adding a license here, e.g., MIT, Apache 2.0, etc.]