'''
Now I need a data structure to support fast css selector switching
to add new selector, use 'IND' to indicate where index should be placed
'''
class SelectorManager:
    def __init__(self,selectorLst = None):
        self.rawData = selectorLst
        self.n = 0  # this is the consecutive selector index for consecutive elements
                    # we manually set this outside of the object, in the try-except block
                    # note that we always tally even when fail. This is a case-by-case design decision

        self.top = 0    #always stays at 0, top of the list
        self.bumper = 0 #repeatedly increased by one by each call of "roll"
                        #setTop relies one bumper
        self.switch = False

    def add(self,selector):
        if selector in self.rawData:
            print("This selector already exists")
        else:
            self.rawData.append(selector)
    def reset(self):
        self.rawData = []
        self.n = 0
        self.top = 0
        self.bumper = 0
        self.switch = False

    '''
    called whenever trying to look for a selector inside a try block
    '''
    def roll(self):

        ind = self.bumper%len(self.rawData)
        self.bumper += 1    # we bump regardless if we will succeed
                            # of course the first roll always returns the top selector
                            # but each subsequent roll gives a consecutive next element
        if self.top == ind and self.switch: #this condition means we tried every selector and we do not have a match
            self.switch = False
            return "FAIL"   # if we see "FAIL", do not bother to wait for the try-except, break loop
        self.switch = True
        # print("current chosen selector by roll: ",self.rawData[ind].replace("IND",str(self.n)))
        return self.rawData[ind].replace("IND",str(self.n))

    '''
    called only after a roll call
    also must be in the except block
    '''
    def setTop(self):
        ind = (self.bumper-1)%len(self.rawData)
        if self.top != ind: # meaning we just had a miss
            self.rawData[self.top], self.rawData[ind] = self.rawData[ind], self.rawData[self.top]

    '''
    called outside (before/after, in my case before) try-except block to refresh
    '''
    def update(self,code=0):
        self.bumper = 0
        self.n += code
        self.switch = False















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


# CSS selector for the scrollable container
scrollable_container_selector = "div.panel__body:nth-child(3)"
# step_height = 0  # Amount to scroll each time

# Function to scroll the container by a step
def scroll_by_step(driver, selector, step_height = 80):
    container = driver.find_element(By.CSS_SELECTOR, selector)
    driver.execute_script("arguments[0].scrollTop += arguments[1];", container, step_height)

def zoom_out(driver, zoom_level=0.5):
    driver.execute_script(f"document.body.style.zoom='{zoom_level}'")

'''
dynamic scroll adjustment function, the upperBound and lowerBounds
are heuristics obtained from manually inspecting the page
also auto obtained via scrollable container
in our case, roughly lowerbound 600 (bottom of viewport) and adjust scroll bigger
                     upperbound 300 (top of viewport) and adjust scroll smaller
             item hiehgt roughly 100. this is auto obtained 
'''
def dynamicScrollAdjust(upperBound=300, lowerBound=600, itemTop=450, itemSize=100):
    baseline = (lowerBound - upperBound)/2  # the middle of the viewport
    adjust = 0  #we increase/decrease scrolling based on adjust mount. Return val.
    if itemTop-2*itemSize < upperBound:    #item is too high, adjust down scroll
        adjust = itemSize - (baseline-upperBound)
    elif itemTop+2*itemSize > lowerBound: #item is too low, adjust up scroll
        adjust = itemSize + (lowerBound-baseline)
    else:
        adjust = itemSize
    return adjust


def run(): #do not load image for better speed
    global driver
    # I manually put it inside usr, otherwise need to specify driver file path
    options = Options()
    options.add_argument('--blink-settings=imagesEnabled=false')  # disable loading image
    driver = webdriver.Chrome(options=options)

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




    selectorManager = SelectorManager(["div.result:nth-child(IND) > a:nth-child(1)",
                                       "div.result:nth-child(IND)"])

    failCt = 0
    successCt = 0
    unknownCt = 0
    breaker = 255
    inPageDelay = 0.2
    delayFactor = 5
    step_height = 0  # Amount to scroll each time
    correction = 50

    scanRange = 200

    # zoom_out(driver,0.2)
    '''
    somehow, zoom function breaks the scraping
    '''
    container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,scrollable_container_selector ))
    )
    upperBound = container.location['y']
    lowerBound = container.size['height'] + upperBound

    while selectorManager.n<scanRange and breaker>0:
        breaker -= 1
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        selectorManager.setTop()
        selectorManager.update(1)

        for i in range(len(selectorManager.rawData)):
            curSelector = selectorManager.roll()
            if "FAIL"==curSelector:
                print("unknown selector at n= ",selectorManager.n)
                unknownCt +=1
                scroll_by_step(driver, scrollable_container_selector, correction)

                break

            try:
                checkOne = WebDriverWait(driver, inPageDelay).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, curSelector))
                )
                print("testing eachButton top, ",checkOne.location["y"]," and total height: ",checkOne.size["height"])
                '''
                below is the dynamic scroll code, might fail. Careful.
                '''
                #todo: watch the below code carefully!!!!!!!
                step_height= max(0,dynamicScrollAdjust(upperBound,lowerBound,checkOne.location["y"],checkOne.size["height"])-correction)
                checkOne.click()
                print("                                         obtained bounds:", upperBound, lowerBound, "item data: ",checkOne.location["y"],checkOne.size["height"])
                print("                                     adjusted scroll size to be: ", step_height)
                # print("succeeded, with list: ",selectorManager.rawData, " more specifically, selector is: ",curSelector)

                try:
                    locInfo = WebDriverWait(driver, inPageDelay * delayFactor).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,".meet"))
                    )
                    print(locInfo.text, "at index n: ",selectorManager.n)
                    successCt+=1

                    scroll_by_step(driver, scrollable_container_selector, step_height)
                    break

                except Exception as e:
                    failCt+=1
                    print(f"Exception of getting meeting info at n={selectorManager.n}, the class prolly does not meet!")

                    scroll_by_step(driver, scrollable_container_selector, correction)

                break

            except Exception as e:
                pass
                # print("selector switch happened, now we have: ",selectorManager.rawData)




    # n=0
    # breaker = 1024
    # while n<50 and breaker>0:
    #     n+=1
    #     breaker -= 1
    #
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     try:
    #         checkOne = WebDriverWait(driver, 0.2).until(
    #             EC.presence_of_element_located((By.CSS_SELECTOR, f"div.result:nth-child({str(n)}) > a:nth-child(1)"))
    #         )
    #         checkOne.click()
    #     except Exception as e:
    #         try:
    #             checkOne = WebDriverWait(driver, 0.2).until(
    #                 EC.presence_of_element_located(
    #                     (By.CSS_SELECTOR, f"div.result:nth-child({str(n)})"))
    #             )
    #             checkOne.click()
    #         except Exception as e:
    #             print(f"Exception of clicking at n={n}")
    #         try:
    #             locInfo = WebDriverWait(driver, 5).until(
    #                 EC.presence_of_element_located((By.CSS_SELECTOR,".meet"))
    #             )
    #             print(locInfo.text, "at index n: ",n)
    #         except Exception as e:
    #             print(f"Exception of getting meeting info at n={n}")
    print("script complete, failCt: ",failCt, " successCt: ",successCt, " unknownCt: ",unknownCt)
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

    # selectorManager = SelectorManager(["fakeAtIndINDpos","anotherwithINDpos"])
    # print("we just initializd is: ",selectorManager.rawData)
    # print("first, try to roll: ", selectorManager.roll())
    # print("check if bumper goes to 1 corrct: ", selectorManager.bumper)
    # print("roll again, we check another: ",selectorManager.roll())
    # print("check if bumper goes to 2 corrct: ", selectorManager.bumper)
    # # print("roll a third time, we should fail now: ",selectorManager.roll())
    # # print("check if bumper goes to 3 corrct: ", selectorManager.bumper)
    # selectorManager.setTop()
    # selectorManager.update(0)
    #
    # print("check entire list after setTop: ", selectorManager.rawData)
    # print("look all good, we try more: ")
    # print("first, try to roll, we shld see another: ", selectorManager.roll())
    # print("check if bumper goes to 1 corrct: ", selectorManager.bumper)
    # print("roll again, we check fake at: ",selectorManager.roll())
    # print("check if bumper goes to 2 corrct: ", selectorManager.bumper)
    # print("roll a third time, we should fail now: ",selectorManager.roll())
    # print("check if bumper goes to 3 corrct: ", selectorManager.bumper)


    try:
        run()
    finally:
        # Close the WebDriver
        driver.quit()
    # #     # dumpJson(urlSet, filename = "testData.json")


#todo: next step, add LRU for clicking css selector candidates for speed optimization.