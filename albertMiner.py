from selenium.common import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
import json
import time
import requests


timeout = 3
driver = None
urlSet = set()

def interact(field, content = None):
    where = driver.find_element(By.CSS_SELECTOR, field)
    if isinstance(content, str):    #fill in a string
        where.send_keys(content)
    elif content is None:   #simply click
        where.click()
def run(): #do not load image for better speed
    global driver
    # I manually put it inside usr, otherwise need to specify driver file path
    options = Options()
    # options.add_argument('--blink-settings=imagesEnabled=false')  # disable loading image
    driver = webdriver.Chrome()

    # Go to the website
    driver.get("https://albert.nyu.edu/albert_index.html")
    # Wait for "sign in to albert" to pop up
    albertButton = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.textBox:nth-child(2) > div:nth-child(3) > a:nth-child(1)"))
    )
    albertButton.click()
    time.sleep(2)
    select_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "crit-camp"))  # Adjust the selector as needed
    )

    dropdown = Select(select_element)

    # Select the option with value "UY"
    dropdown.select_by_value("WS@BRKLN")   #this is changed for dff campuses. I selected brooklyn here

    # Verify the selected option (optional)
    selected_option = dropdown.first_selected_option
    print(f"Selected option: {selected_option.text}")

    startSearch = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search-button"))  # Adjust the selector as needed
    )
    startSearch.click()
    time.sleep(3)

    n=0
    breaker = 1024
    while n<50 and breaker>0:
        n+=1
        breaker -= 1

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            checkOne = WebDriverWait(driver, 0.2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"div.result:nth-child({str(n)}) > a:nth-child(1)"))
            )
            checkOne.click()
        except Exception as e:
            try:
                checkOne = WebDriverWait(driver, 0.2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, f"div.result:nth-child({str(n)})"))
                )
                checkOne.click()
            except Exception as e:
                print(f"Exception of clicking at n={n}")
            try:
                locInfo = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,".meet"))
                )
                print(locInfo.text, "at index n: ",n)
            except Exception as e:
                print(f"Exception of getting meeting info at n={n}")

    time.sleep(3)







    # Wait for the search button to be clickable
#     search_button = WebDriverWait(driver, timeout).until(
#         EC.element_to_be_clickable((By.CSS_SELECTOR, "#username"))
#     )
#     # Click the search button
#     search_button.click()
#     # Optionally, wait for the search results to load
#     WebDriverWait(driver, timeout).until(
#         lambda d: d.find_element(By.CSS_SELECTOR, ".collection__title") and targetProduct in d.find_element(By.CSS_SELECTOR,
#                                                                                            ".collection__title").text
#     )
#
# #step into each product card and mine them
# '''
# teargetProduct is just fixed to be "tea"
# filter True means we don want any product with vendor "HOUSE BRAND" (meaning loose tea)
# curPage simply tracks page number, not very important
# '''
# def mineSinglePage(targetProduct = "tea", filter = True,curPage = 1):
#     global driver
#     global urlSet
#     oldCt = len(urlSet)
#     n = 0  # paramatrize item navig
#     breaker = 255
#     delay = 0.2  # when internet slows down we use a higher delay factor
#     while breaker > 0:
#         breaker -= 1
#         n += 1
#         try:
#
#             vendor_info = WebDriverWait(driver, timeout).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR,
#                                                 "div.product-item:nth-child(" + str(
#                                                     n) + ") > div:nth-child(2) > div:nth-child(1) > a:nth-child(1)"))
#             )  # change the first index for diff products
#         except TimeoutException:
#             print("all products from page ",curPage," are extracted. Proceeding to next page...")
#             return
#
#
#
#         # only skip if we enabled filter and detect loose tea keyword: "HOUSE BRAND"
#         if (not ("HOUSE BRAND" in vendor_info.text and filter)):
#             # Find the link of the first product item
#             product_link = WebDriverWait(driver, timeout).until(
#                 EC.element_to_be_clickable((By.CSS_SELECTOR,
#                                                 "div.product-item:nth-child(" + str(
#                                                     n) + ") > div:nth-child(2) > div:nth-child(1) > a:nth-child(2)"))
#             )
#             # product_link.click()
#             #try javascript solution
#             driver.execute_script("arguments[0].click();", product_link)
#             # Wait for some time to let the network requests complete
#             time.sleep(delay)
#
#             # check for sold out button not disabled
#             soldOutButton = WebDriverWait(driver, timeout).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, ".product-form__add-button"))
#             )
#
#             # sold out, we skip
#             if(not soldOutButton.get_attribute("disabled")):
#
#                 ##########successfully located product. Now extraction starts#################
#                 website = "https://foodsofnations.com"
#
#                 successFlag = False
#                 for request in driver.requests:
#                     if request.response:
#                         if request.path.endswith('.json') and request.method == 'GET' and "products" in request.path:
#                             urlSet.add(website + request.path)
#                             successFlag = True
#                             # Stop iterating once the first JSON file is found
#                             # break
#                 if not successFlag:
#                     print("No JSON file found on initial page load. Refreshing the page...")
#                     driver.refresh()
#                     time.sleep(2 * delay)  # delay to make sure webpage loads
#
#                     for request in driver.requests:
#                         if request.response:
#                             if request.path.endswith('.json') and request.method == 'GET' and "products" in request.path:
#                                 print("Found JSON URL after refreshing:", "https://foodsofnations.com" + request.path)
#
#
#                 if not successFlag:
#                     print("No JSON file found on second attempt at url: ")
#                     print(driver.current_url)
#                 ############extraction of single item complete. Navigate back
#             driver.back()
#
#             WebDriverWait(driver, timeout).until(
#                 lambda d: d.find_element(By.CSS_SELECTOR, ".collection__title") and targetProduct in d.find_element(By.CSS_SELECTOR,
#                                                                                            ".collection__title").text
#             )
#             # above is the while loop for single page
#     print("total urls added from page ",curPage, ": ",len(urlSet)-oldCt)
#     for each in urlSet:
#         print(each)
#
# def mineAllPages(targetProduct = "tea", filter = True):
#     global driver
#     global urlSet
#     breaker = 255
#     pageCt = 0
#     while breaker > 0:
#         breaker -= 1
#         pageCt += 1
#         print("loop executed for page flip")
#         mineSinglePage(targetProduct = targetProduct, filter = filter,curPage = pageCt)
#         try:
#             nextPage = WebDriverWait(driver, timeout).until(
#                 EC.presence_of_element_located((By.CSS_SELECTOR,
#                                                 ".pagination__next"))
#             )
#             nextPage.click()
#             driver.get(driver.current_url)
#             print("one entire loop for page flip complete")
#
#
#
#         except TimeoutException:
#             print("All pages extracted. finishing at page ",pageCt)
#             print("Total urls added: ", len(urlSet))
#             break


# Function to fetch and parse JSON from URL
def fetch_json(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch JSON from {url}")
        return None

def dumpJson(urlLst, filename = "testData.json"):
    # Fetch JSON from each URL and combine into a single data structure
    combined_data = []
    for url in urlLst:
        json_data = fetch_json(url)
        if json_data:
            combined_data.append(json_data)
    # Write the combined data structure to a JSON file
    filename
    with open(filename, "w") as f:
        json.dump(combined_data, f)

    print(f"Combined JSON data written to {filename}")


if __name__ == "__main__":
    try:
        run()
    finally:
        # Close the WebDriver
        driver.quit()
        # dumpJson(urlSet, filename = "testData.json")
