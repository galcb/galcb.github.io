from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import os
import sys

def name_bill(bn):
    if bn=="SB780":
        return f"{bn} - Health insurance; coverage for contraceptive drugs and devices."
    if bn=="HB3271":
        return f"{bn} - Health insurance; coverage for contraceptive drugs and devices."
    if bn=="HB2611":
        return f"{bn} - Health insurance; coverage for cancer follow-up testing; report."
    if bn=="HB2034":
        return f"{bn} - Tidal and nontidal wetlands; wetland restoration and creation policy task force, report."
    if bn =="HB2528":
        return f"{bn} - Electric utilities; customer energy choice; customer return to service; subscription cap and queue."
    return f"{bn} - Bill Name Unknown"

def generate_markdown(results, date_header, houselink, senatelink):
    markdown = f"## {date_header}" + f" [House Sched.  ]({houselink})" + f"- [Senate Sched.]({senatelink})\n\n"  # Add the date header
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
    top_links_file = "toplinks.txt"
    
    # Read the current content of toplinks.txt if it exists
    existing_content = ""
    if os.path.exists(top_links_file):
        with open(top_links_file, 'r') as file:
            existing_content = file.read().strip()
    
    # Collect the text of the <a> tags
    combined_text = ""
    day_text = ""
    for xpath in xpaths:
        try:
            # Get the first <a> tag within the XPath
            element = driver.find_element(By.XPATH, xpath)
            text = element.text.strip()
            if text:
                combined_text += text  # Concatenate the text of the <a> tags
                day_text = text
        except Exception as e:
            print(f"Error finding element for XPath {xpath}: {e}")
    
    # Check if the concatenated text matches the existing content
    if combined_text == existing_content:
        print("The text of the <a> tags is the same as in toplinks.txt. No changes made.")
        sys.exit(0)
    
    # Write the new concatenated text to toplinks.txt
    with open(top_links_file, 'w') as file:
        file.write(combined_text)
    
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
    filter_words = ["SB780", "HB2371", "HB2611", "HB2034", "HB2528"]

    # Visit each top link and collect matching <a> tags
    results = []
    for link in top_links:
        try:
            driver.get(link)  # Visit the page
            time.sleep(8.0)

            # Now retrieve all <a> tags
            a_tags = driver.find_elements(By.TAG_NAME, 'a')

            # Check if the text matches any word in the filter array
            for a_tag in a_tags:
                text = a_tag.text.strip() if a_tag.text else ""  # Get the text of the <a> tag
                href = a_tag.get_attribute('href')  # Get the href attribute

                # Check if the text starts with any word in filter_words and href is not empty
                if any(text.startswith(word) for word in filter_words) and href:
                    # Build a scrollable link to the tag using the href and JS-based scrolling
                    # Ensure the href is relative to the page URL
                    element_id = a_tag.get_attribute('id') or a_tag.get_attribute('name')  # Get id or name if available
                    if element_id:
                        # Use a fragment identifier if id or name is present
                        link_to_tag = f"{link}#{element_id}"
                    else:
                        # Fallback: Link directly to the page since no fragment identifier exists
                        link_to_tag = f"{link}#unknown-{text[:30]}"  # Use the first 30 chars of text to identify

                    # Add the results to the list as a tuple of text, href, and link to the <a> tag
                    results.append((text, href, link_to_tag))

        except Exception as e:
            print(f"Error visiting link {link}: {e}")

    driver.quit()  # Close the browser
    return results, day_text, top_links[0], top_links[1]

def main():
    # Scrape the links
    scraped_results, day_text, linkhouse, linksen = scrape_from_xpaths_and_filter()

    # Generate Markdown content with today's date as the header
    markdown_content = generate_markdown(scraped_results, day_text, linkhouse, linksen)

    # Define the file path where the results will be saved
    file_path = "scraped_links.md"

    # Save the results to the file
    save_results_to_file(file_path, markdown_content)
    print(f"Results for {day_text} have been saved to {file_path}.")

if __name__ == "__main__":
    main()