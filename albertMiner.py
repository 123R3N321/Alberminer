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
        self.orignial = selectorLst.copy()

    def add(self,selector):
        if selector in self.rawData:
            print("This selector already exists")
        else:
            self.rawData.append(selector)

    '''
    edit:
    do not bother clearing the rawData
    simply declare another one
    now we keep the raw.
    and need to row again.
    '''
    def reset(self):
        self.rawData = self.orignial.copy()
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


timeout = 3 #not exactly needed at the moment
driver = None#global driver param. Do not touch
urlSet = set()#not exactly needed.

'''
encapsulation for shorter non repetitive code
however, there is no delay in this function
use with caution
'''
def interact(field, content = None):
    where = driver.find_element(By.CSS_SELECTOR, field)
    if isinstance(content, str):    #fill in a string
        where.send_keys(content)
    elif content is None:   #simply click
        where.click()


# CSS selector for the scrollable container
'''
shld prolly place this right above while loop inside run() function.
scrollabl container selector.
'''
scrollable_container_selector = "div.panel__body:nth-child(3)"
# step_height = 0  # Amount to scroll each time

'''
simple one-step scroll, 
step_height to be controlled externally
(preferrably dynamically if dynamic control is fast enough)
'''
def scroll_by_step(driver, selector, step_height = 80):
    container = driver.find_element(By.CSS_SELECTOR, selector)
    driver.execute_script("arguments[0].scrollTop += arguments[1];", container, step_height)

'''
somehow breaks the selenium functionality. 0.1 zoom out to tiny fonts, 2 zoom in to huge
might be useful in the future
'''
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



data = []
'''
the function that does the mining
detailed Search gives much, much more insight, but slows down code
'''
def run(keyword = None, detailedSearch = False): #do not load image for better speed
    global driver
    extraDelay = 10 #for extra slow steps
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
    time.sleep(2)   #pretending I am a human
    select_element = WebDriverWait(driver, extraDelay).until(   #slow step, extra wait
        EC.presence_of_element_located((By.ID, "crit-camp"))  # Adjust the selector as needed
    )

    dropdown = Select(select_element)

    # Select the option for brookbrooklyn campus.
    dropdown.select_by_value("WS@BRKLN")   #this is changed for dff campuses. I selected brooklyn here

    # Verify the selected option (optional)
    selected_option = dropdown.first_selected_option
    print(f"Selected option: {selected_option.text}")

    #we can even search for keyword
    if(keyword):
        searchBar = WebDriverWait(driver, extraDelay).until(
            EC.presence_of_element_located((By.ID, 'crit-keyword'))  # Update the locator as necessary
        )
        searchBar.send_keys(keyword)

    startSearch = WebDriverWait(driver, extraDelay).until(  #slow step. Extra wait
        EC.presence_of_element_located((By.ID, "search-button"))  # Adjust the selector as needed
    )
    startSearch.click()

    # Initialize selector manager. Can add more selectors if needed.
    selectorManager = SelectorManager(["div.result:nth-child(IND) > a:nth-child(1)",
                                       "div.result:nth-child(IND)"])

    failCt = 0      #tally failed mining. Includes cases with no data (there's nothing to mine)
    successCt = 0   #tally successful data mining
    unknownCt = 0   #tally encounters with undocumented css selector
    breaker = 255   #infinite loop guard
    inPageDelay = 0.2   #heuristic param based on internet speed and Albert server speed. Range 0.1-3
    delayFactor = 5     #heuristic param as above. Range 1-10, dependent on inPageDelay linearly.
    step_height = 0     # Initial amount to scroll each time. Not exactly necessary
    correction = 50     #heuristic scrolling correction.

    scanRange = 200     #how many classes we are mining at

    # zoom_out(driver,0.2)
    '''
    somehow, zoom function breaks the scraping
    '''
    container = WebDriverWait(driver, extraDelay).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,scrollable_container_selector ))
    )
    upperBound = container.location['y']
    lowerBound = container.size['height'] + upperBound

    prevInfo = ""
    while selectorManager.n<scanRange and breaker>0:
        breaker -= 1
        # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        selectorManager.setTop()
        selectorManager.update(1)

        for i in range(len(selectorManager.rawData)):   #lazy code to function as a safe while loop
            curSelector = selectorManager.roll()
            if "FAIL"==curSelector: #we need to add more selector to selectorManager if this happens
                print("unknown selector at n= ",selectorManager.n)
                unknownCt +=1
                scroll_by_step(driver, scrollable_container_selector, correction)

                break

            try:    #attempt to locate course button
                checkOne = WebDriverWait(driver, inPageDelay).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, curSelector))
                )
                print(checkOne.text,": ")
                # print("testing eachButton top, ",checkOne.location["y"]," and total height: ",checkOne.size["height"])
                '''
                below is the dynamic scroll code, might fail. Careful.
                '''
                #todo: watch the below code carefully!!!!!!!
                step_height= max(0,dynamicScrollAdjust(upperBound,lowerBound,checkOne.location["y"],checkOne.size["height"])-correction)
                checkOne.click()
                # print("                                         obtained bounds:", upperBound, lowerBound, "item data: ",checkOne.location["y"],checkOne.size["height"])
                # print("                                     adjusted scroll size to be: ", step_height)
                # print("succeeded, with list: ",selectorManager.rawData, " more specifically, selector is: ",curSelector)

                try:    #when course button located successfully,
                        #further attempt to mine meeting loc and time info
                    locInfo = WebDriverWait(driver, inPageDelay * delayFactor).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR,".meet"))
                    )
                    print(locInfo.text, "at index n: ",selectorManager.n)
                    successCt+=1

                    global data
                    if locInfo.text != prevInfo:
                        data.append(locInfo.text+"at index n: "+str(selectorManager.n))
                    prevInfo = locInfo.text

                    scroll_by_step(driver, scrollable_container_selector, step_height)
                    break

                except Exception as e:  #no meeting info found
                    failCt+=1
                    print(f"Exception of getting meeting info at n={selectorManager.n}, the class prolly does not meet!")
                    # correction small step scroll, which is safer

                finally:

                    if (detailedSearch):
                        # first check type. Lab("REC") is likely not useful
                        sectionTypeScrollManager = SelectorManager(
                            (["a.course-section:nth-child(IND) > div:nth-child(2)"]))
                        sectionTypeScrollManager.n = 1  # because starts at ind 2
                        # next meeting time specific to section
                        sectionTimeScrollManager = SelectorManager(
                            ["a.course-section:nth-child(IND) > div:nth-child(3)"])
                        sectionTimeScrollManager.n = 1
                        # and prof's name. Vital!!!
                        profScrollManager = SelectorManager(["a.course-section:nth-child(IND) > div:nth-child(4)"])
                        profScrollManager.n = 1
                        localScanRange = 32  # assuming no more than 31 sections per class,
                        # this number is big as we might have multiple labs here too
                        while localScanRange > 0:
                            localScanRange -= 1
                            sectionTypeScrollManager.update(1)
                            sectionTypeSelector = sectionTypeScrollManager.roll()
                            sectionTimeScrollManager.update(1)
                            sectionTimeSelector = sectionTimeScrollManager.roll()
                            profScrollManager.update(1)
                            profSelector = profScrollManager.roll()
                            try:
                                # print(" generated selector: ", profSelector)

                                section = WebDriverWait(driver, inPageDelay * delayFactor).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, sectionTypeSelector))
                                )
                                print(" SectionType: ", section.text, end='\t')

                                section = WebDriverWait(driver, inPageDelay * delayFactor).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, sectionTimeSelector))
                                )
                                print(" DetailedMeeting time: ", section.text, end='\t')

                                section = WebDriverWait(driver, inPageDelay * delayFactor).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, profSelector))
                                )
                                print(" Instructor ", section.text, end='\n')


                            except:  # we reach the end
                                # print("No hit with new thing")
                                print()
                                break

                    scroll_by_step(driver, scrollable_container_selector, correction)
                    print()
                    break

            except Exception as e: #course button not found. Need selectorManager to switch selector now.
                pass
                # print("selector switch happened, now we have: ",selectorManager.rawData)

    print("script complete, failCt: ",failCt, " successCt: ",successCt, " unknownCt: ",unknownCt)
    time.sleep(3)



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



###################################below is data analysing##########################################

import re
import datetime


# Helper function to convert time strings to time objects
def convert_to_time(time_str):
    try:
        # Attempt to parse the time with the format '%I:%M%p'
        return datetime.datetime.strptime(time_str, '%I:%M%p').time()
    except ValueError:
        # If parsing fails, attempt to parse without minutes and colon
        try:
            # Parse the time without minutes and colon
            return datetime.datetime.strptime(time_str, '%I%p').time()
        except ValueError:
            # If parsing still fails, raise an error
            raise ValueError("Time format not recognized: " + time_str)

    # Helper function to convert date strings to datetime objects
def convert_to_date(date_str):
    return datetime.datetime.strptime(date_str, '%m/%d').replace(year=datetime.datetime.now().year)

'''
helper function for sorting
'''
def roomOrder(roomMsg):
    numPattern = r'\b\d+\b' #non discriminant numeric match
    matches = re.findall(numPattern, roomMsg)   #which potentially also gives street num

    if matches:
        return int(matches[-1])  # Extract the last match as the room number
    else:
        return -1 # non numeric room num we treat as lowest possible val

'''
clumsy.
'''
def collectionUnfold(collection):
    return roomOrder(collection[4])


def analyse(buildingSel = "2"):
    global data

    # data = [
    #     "T 11am-12:20pm in Dibner , Pfizer Auditorium (9/3 to 12/12) at index n:  22",
    #     "T 11am-12:20pm in Dibner , Pfizer Auditorium (9/3 to 12/12) at index n:  22",
    #     "T 11am-12:20pm in Dibner , Pfizer Auditorium (9/3 to 12/12) at index 6"
    # ]

    # Regular expression pattern to match the relevant information
    pattern = re.compile(
        r"(?P<days>[MTWRFSU]{1,2})\s+"
        r"(?P<start_time>\d{1,2}(?::\d{2})?(?:am|pm))-(?P<end_time>\d{1,2}(?::\d{2})?(?:am|pm))\s+"
        r"in\s+(?P<building>[\w\s,]+),\s+(?P<room>[\w\s]+)\s+"
        r"\((?P<start_date>\d{1,2}/\d{1,2})\s+to\s+(?P<end_date>\d{1,2}/\d{1,2})\)"
    )

    # Set to store unique entries
    unique_entries = set()

    # Parse the data and extract relevant information
    for each in data:
        match = pattern.match(each)
        if match:
            # Extract match groups
            day = match.group('days')
            start_time = convert_to_time(match.group('start_time'))
            end_time = convert_to_time(match.group('end_time'))
            building = match.group('building').strip()
            room = match.group('room').strip()
            start_date = convert_to_date(match.group('start_date'))
            end_date = convert_to_date(match.group('end_date'))

            # Create a tuple of extracted information
            entry_tuple = (day, start_time, end_time, building, room, start_date, end_date)

            # Add the tuple to the set of unique entries
            unique_entries.add(entry_tuple)

    # Output the unique entries
    # sortedSet = sorted(unique_entries, key=collectionUnfold)
    sortedSet = sorted(unique_entries, key=lambda x: roomOrder(x[4]))
    # for entry in unique_entries:
    #     if buildingSel in entry[3]:
    #         unorderedLst.append(entry)

    for entry in sortedSet:
        if buildingSel in entry[3]:
            print(entry)



if __name__ == "__main__":
    # analyse()
    try:
        run(keyword = "CS", detailedSearch=True)
        analyse()
    finally:
        # Close the WebDriver
        driver.quit()
    #     # dumpJson(urlSet, filename = "testData.json")


#todo: next step, add LRU for clicking css selector candidates for speed optimization.
#add prof search
'''
a.course-section:nth-child(2) > div:nth-child(4)
a.course-section:nth-child(5) > div:nth-child(4)
a.course-section:nth-child(4) > div:nth-child(4)
a.course-section:nth-child(6) > div:nth-child(4)



a.course-section:nth-child(2) > div:nth-child(4)



we also need update on location time

a.course-section:nth-child(2) > div:nth-child(3)
a.course-section:nth-child(7) > div:nth-child(3)

so final ind 3 is time, 4 is teacher


and, section type; lab is most likely not useful

a.course-section:nth-child(2) > div:nth-child(2)
a.course-section:nth-child(9) > div:nth-child(2)
a.course-section:nth-child(3) > div:nth-child(2)

'''