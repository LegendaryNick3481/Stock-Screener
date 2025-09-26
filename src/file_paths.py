
import os

# Base directory for generated files
generated_files_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generatedFiles'))

# Path to the access token file
access_token_file = os.path.join(generated_files_dir, 'access_token.txt')

# Path to the screener output file
screener_output_file = os.path.join(generated_files_dir, 'screener_output.csv')

# Path to the ticker data file
ticker_data_file = os.path.join(generated_files_dir, 'ticker_data.csv')

# Path to the trade log file
trade_log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'trade_log.csv'))

# Path to the fyers logs
fyers_log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generatedFiles'))

# Path to the Chrome user data directory
chrome_user_data_dir = r"C:\Users\eldoj\AppData\Local\Google\Chrome\User Data\AutomationProfile"

