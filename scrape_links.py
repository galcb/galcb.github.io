from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import os
from datetime import datetime, timedelta, timezone

def generate_markdown(results, date_header):
    markdown = f"## {date_header}\n\n"  # Add the date header
    for text, href, link_to_tag in results:
        markdown += f"- [{text}]({href})\n"  # Format each result as a list item
    markdown += "\n"  # Add an empty line at the end
    return markdown

def save_results_to_file(file_path, markdown_content):
    # Check if the file exists; if it does, prepend, otherwise create a new file
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            existing_content = file.read()
        with open(file_path, 'w') as file:
            file.write(markdown_content + existing_content)
    else:
        with open(file_path, 'w') as file:
            file.write(markdown_content)

def scrape_from_xpaths_and_filter():
    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Target page URL
    main_page_url = "https://lis.virginia.gov/session-details/20251/calendar"
    driver.get(main_page_url)

    # XPaths to search on the main page
    xpaths = [
        "/html/body/div/div[1]/div/main/section/div/div/div/div[2]/div[1]//a",
        "/html/body/div/div[1]/div/main/section/div/div/div/div[2]/div[2]//a"
    ]

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, xpaths[1]))
    )

    # Find the "closest to top" <a> tag for each XPath
    top_links = []
    for xpath in xpaths:
        try:
            # Get the first <a> tag within the XPath
            element = driver.find_element(By.XPATH, xpath)
            href = element.get_attribute('href')
            if href:
                top_links.append(href)
        except Exception as e:
            print(f"Error finding element for XPath {xpath}: {e}")

    # Array of words to match against <a> tag text
    filter_words = ["HB1601", "HB1616", "HB1603", "HJ434", "HB1764", "HB1768", "HB1779", "HB1791", "HB1821", "HB1834", "HB2025", "HB2030", "HB2034", "HB2037", "HB2528", "HB2509", "HB2506", "HB2497", "HB2464", "HB2408", "HB2459", "HB2335", "SB823", "SB806", "SB794", "SB777", "SB830", "SB839", "HB1597", "HB1607", "HB1608", "HB1622", "SB774",]

    # Visit each top link and collect matching <a> tags
    results = []
    for link in top_links:
        print("hey, trying " + str(link))
        try:
            driver.get(link)  # Visit the page
            time.sleep(5.0)

            # Now retrieve all <a> tags
            a_tags = driver.find_elements(By.TAG_NAME, 'a')

            # Check if the text matches any word in the filter array
            for a_tag in a_tags:
                text = a_tag.text.strip() if a_tag.text else ""  # Get the text of the <a> tag
                href = a_tag.get_attribute('href')  # Get the href attribute

                # Check if the text starts with any word in filter_words and href is not empty
                if any(text.startswith(word) for word in filter_words) and href:
                    # Get the link to the <a> tag (the outer HTML)
                    link_to_tag = a_tag.get_attribute('outerHTML')
                    # Add the results to the list as a tuple of text, href, and link to the <a> tag
                    results.append((text, href, link_to_tag))
        except Exception as e:
            print(f"Error visiting link {link}: {e}")

    driver.quit()  # Close the browser
    return results

def main():
    # Get today's date for the header
    eastern_offset = timedelta(hours=-5)  # Standard Time (UTC-5)
    eastern_time = datetime.now(timezone(eastern_offset))

    # Format the date
    today_date = eastern_time.strftime('%Y-%m-%d')

    # Scrape the links
    scraped_results = scrape_from_xpaths_and_filter()

    # Generate Markdown content with today's date as the header
    markdown_content = generate_markdown(scraped_results, today_date)

    # Define the file path where the results will be saved
    file_path = "scraped_links.md"

    # Save the results to the file
    save_results_to_file(file_path, markdown_content)
    print(f"Results for {today_date} have been saved to {file_path}.")

if __name__ == "__main__":
    main()