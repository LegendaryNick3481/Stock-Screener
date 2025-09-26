from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import csv
import traceback
import file_paths as fp

# Setup Chrome options
options = Options()
options.add_argument(f"--user-data-dir={fp.chrome_user_data_dir}")
options.add_argument("--start-maximized")
options.add_argument("--disable-extensions")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

try:
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print('Chrome started successfully')
    time.sleep(2)

    # Go to Screener and wait for manual login
    login_url = "https://www.screener.in/"
    driver.get(login_url)
    input("Login manually and press Enter to continue...")

    # Navigate to your screener filter
    url = "https://www.screener.in/screen/raw/?order=&source_id=&query=Current+price+%3E%3D10+AND%0D%0ACurrent+price++%3C%3D+1000+AND%0D%0AVolume+%3E%3D+1000000&limit=50"
    driver.get(url)
    print(f"Navigated to: {url}")

    # Wait until the table is present
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.data-table")))
    print("Table loaded successfully")

    all_data = []

    while True:
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("table.data-table tbody tr")
        print(f"Found {len(rows)} rows on current page")

        for i, row in enumerate(rows):
            cols = row.find_all("td")
            if len(cols) >= 5:
                try:
                    sno = cols[0].text.strip()
                    name_element = cols[1].find("a")
                    name = name_element.text.strip() if name_element else cols[1].text.strip()

                    # ✅ Extract ticker from href="/company/TICKER/"
                    href = name_element['href'] if name_element else ""
                    ticker = href.split("/")[2].upper() if href else ""

                    cmp = cols[2].text.strip()
                    volume = cols[3].text.strip()
                    roce = cols[4].text.strip()
                    all_data.append([sno, name, ticker, cmp, volume, roce])

                except Exception as e:
                    print(f"Error processing row {i}: {e}")

        # Click "Next" if it's present and clickable
        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            if next_button.is_displayed() and next_button.is_enabled():
                print("Clicking next page...")
                driver.execute_script("arguments[0].click();", next_button)
            else:
                print("Next button not clickable. Ending pagination.")
                break
        except Exception as e:
            print("Next button not found. Ending pagination.")
            break

    # Create DataFrame with Ticker column
    if all_data:
        df = pd.DataFrame(all_data, columns=["S.No", "Name", "Ticker", "CMP Rs.", "Vol 1d", "ROCE %"])
        print("\n=== FINAL RESULTS ===")
        print(df)

        df.to_csv(fp.screener_output_file, index=False)
        print(f"Data saved to {fp.screener_output_file}")

        # Optional: Create NSE-style codes
        nse_tickers = ["NSE:" + t + "-EQ" for t in df["Ticker"]]
        print("\nNSE-style symbols:")
        print(nse_tickers)

        with open(fp.ticker_data_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Symbol'])  # header
            for ticker in nse_tickers:
                writer.writerow([ticker])



    else:
        print("No data extracted")

except Exception as e:
    print(f"An error occurred: {e}")
    traceback.print_exc()

finally:
    try:
        driver.quit()
        print("Browser closed successfully")
    except:
        print("Browser was already closed or couldn't be closed")
