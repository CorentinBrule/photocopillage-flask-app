from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import time
import random
import os

test= [1]

# driver = webdriver.Firefox()
option = webdriver.ChromeOptions()
option.add_experimental_option("excludeSwitches", ["enable-automation"])
option.add_argument('--disable-blink-features=AutomationControlled')
option.add_experimental_option('useAutomationExtension', False)
option.add_argument("window-size=1280,800")
option.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36")
option.add_argument("user-data-dir=/home/macrico/.config/chromium")

driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=option)
# driver = webdriver.Chrome(options=option)

url_log = "https://api.lulu.com/auth/realms/glasstree/protocol/openid-connect/auth?client_id=project-wizard&redirect_uri=https%3A%2F%2Fwww.lulu.com%2F%3Ferror%3Dinvalid_request%26error_description%3DMissing%2Bparameter%253A%2Bresponse_type&state=792ede07-b70b-4152-b72b-770044c0fb1b&response_mode=fragment&response_type=code&scope=openid&nonce=064a8e2f-1d92-4d9d-b8ac-70f4f7a8a094&kc_locale=en"
file_path_book = "/media/macrico/aa01328a-8641-420c-9077-a12c836f915d/home/macrico/Documents/DSRD/photocopillage/site/photocopillage-by100-chunk4.pdf"
file_path_cover = "/media/macrico/aa01328a-8641-420c-9077-a12c836f915d/home/macrico/Documents/DSRD/photocopillage/photocopillage-by100-executive-bydate/photocopillage-by100-chunk4-cover.pdf"

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

JS_DROP_FILES = """var args = arguments,
  element = args[0],
  offsetX = args[1],
  offsetY = args[2],
  doc = element.ownerDocument || document;

for (var i = 0; ;) {
  var box = element.getBoundingClientRect(),
    clientX = box.left + (offsetX || (box.width / 2)),
    clientY = box.top + (offsetY || (box.height / 2)),
    target = doc.elementFromPoint(clientX, clientY);
  
  if (target && element.contains(target))
      break;
  
  if (++i > 1) {
    var ex = new Error('Element not interactable');
    ex.code = 15;
    throw ex;
  }
  
  element.scrollIntoView({behavior: 'instant', block: 'center', inline: 'center'});
}

var input = doc.createElement('INPUT');
input.setAttribute('type', 'file');
input.setAttribute('multiple', '');
input.setAttribute('style', 'position:fixed;z-index:2147483647;left:0;top:0;');
input.onchange = function (ev) {
  input.parentElement.removeChild(input);
  ev.stopPropagation();

  var dataTransfer = {
    constructor   : DataTransfer,
    effectAllowed : 'all',
    dropEffect    : 'none',
    types         : [ 'Files' ],
    files         : input.files,
    setData       : function setData(){},
    getData       : function getData(){},
    clearData     : function clearData(){},
    setDragImage  : function setDragImage(){}
  };

  if (window.DataTransferItemList) {
    dataTransfer.items = Object.setPrototypeOf(Array.prototype.map.call(input.files, function(file) {
      return {
        constructor : DataTransferItem,
        kind        : 'file',
        type        : file.type,
        getAsFile   : function getAsFile () { return file },
        getAsString : function getAsString (callback) {
          var reader = new FileReader();
          reader.onload = function(ev) { callback(ev.target.result) };
          reader.readAsText(file);
        }
      }
    }), {
      constructor : DataTransferItemList,
      add    : function add(){},
      clear  : function clear(){},
      remove : function remove(){}
    });
  }
  
  ['dragenter', 'dragover', 'drop'].forEach(function (type) {
    var event = doc.createEvent('DragEvent');
    event.initMouseEvent(type, true, true, doc.defaultView, 0, 0, 0, clientX, clientY, false, false, false, false, 0, null);
    
    Object.setPrototypeOf(event, null);
    event.dataTransfer = dataTransfer;
    Object.setPrototypeOf(event, DragEvent.prototype);
    
    target.dispatchEvent(event);
  });
};

doc.documentElement.appendChild(input);
input.getBoundingClientRect(); /* force reflow for Firefox */
return input;
"""


def drop_files(element, files, offsetX=0, offsetY=0):
    driver = element.parent
    isLocal = not driver._is_remote or '127.0.0.1' in driver.command_executor._url
    paths = []

    # ensure files are present, and upload to the remote server if session is remote
    for file in (files if isinstance(files, list) else [files]):
        if not os.path.isfile(file):
            raise FileNotFoundError(file)
        paths.append(file if isLocal else element._upload(file))

    value = '\n'.join(paths)
    elm_input = driver.execute_script(JS_DROP_FILES, element, offsetX, offsetY)
    elm_input._execute('sendKeysToElement', {'value': [value], 'text': value})


WebElement.drop_files = drop_files

def sleep(t=1):
    time.sleep(1 + random.random() * t)



def go_to_log_page():
    sleep()
    logMenu = driver.find_element_by_css_selector('i[aria-label="navigation-signed-out"]')
    logMenu.click()
    hover = ActionChains(driver).move_to_element(logMenu)
    hover.perform()
    sleep()
    driver.find_element_by_css_selector('a[data-testid="main-nav-login"]').click()
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'button')))
    sleep()

    try:
        recapcha = driver.find_element_by_css_selector("iframe[title*='recaptcha']")
        if recapcha.is_displayed():
            driver.get("http://lulu.com/shop")
            sleep()
            button = driver.find_element_by_css_selector("section button")
            button.click()
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'product-item')))
            sleep()
            products = driver.find_elements_by_css_selector(".product-item")
            random.shuffle(products)
            products[0].find_element_by_css_selector("a").click()

            go_to_log_page()
    except:
        pass


def login():
    # driver.get(url_log)
    driver.get("http://lulu.com")
    go_to_log_page()
    # getElementsByTagName("a")[0].click()

    driver.find_element_by_id("username").click()
    sleep()
    driver.find_element_by_id("username").send_keys("corentin.brule@gmail.com")
    sleep()
    driver.find_element_by_id("password").click()
    sleep()
    driver.find_element_by_id("password").send_keys("ProjecT7242")
    sleep()
    driver.find_element_by_class_name("button").click()


book = {
    "projectName": "photocopillage",
    "goal": "lulu",
    "language": "French",
    "category": "Art & Photography",
    "contributors": [{
        "type": "Compiled by",
        "firstName": "Corentin",
        "lastName": "Brulé"
    }],
    "right": "PD_CC_0",
    "ISBN": False,
    "interiorInk": "BWPRE",
    "interiorPaper": "080CW",
    "bindingType": "PB",
    "coverFinish": "M"

}


def create_project(book, file_path_book, file_path_cover):
    driver.get("http://lulu.com/account/wizard/draft/start")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'productType')))

    # start
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="sellIntention"]')))
    ## goal
    goals = driver.find_element_by_css_selector('div[data-testid="wizard-goal-sellIntention"]')
    if book['goal'] == "print":
        goals[1].click()
    else:
        goals[0].click()
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="globalreach"]')))
    if book['goal'] == "lulu":
        driver.find_element_by_css_selector('div[data-testid="wizard-checkbox-globalreach"]').click()
    elif book['goal'] == "global":
        pass

    driver.find_element_by_id("projectTitle").send_keys(book["projectName"])

    if book.get("language", False):
        driver.find_element_by_xpath("//select[@id='language']/option[text()='{}']".format(book['language'])).click()
    # driver.find_element_by_id("language")

    if book.get("category", False):
        driver.find_element_by_xpath("//select[@id='category']/option[text()='{}']".format(book['category'])).click()
    project_id = driver.current_url.split("/")[5]

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".next-step a")))
    driver.find_element_by_css_selector(".next-step a").click()

    # copyright
    if book['goal'] != "print":
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'bookContributors[0].role')))
        # driver.find_element_by_id("bookTitle").send_keys("photocopillage")
        # driver.find_element_by_id("bookSubtitle").send_keys(project_name)
        ## contributors
        for i, contributor in enumerate(book['contributors']):
            if i > 0:
                driver.find_element_by_xpath("//*[ text() = ‘Add Another Contributor’ ]")
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//select[@id='bookContributors[{}].role']".format(i))))
            driver.find_element_by_xpath("//select[@id='bookContributors[{}].role']/option[text()='{}']".format(i, contributor["type"])).click()
            driver.find_element_by_id("bookContributors[0].firstName").send_keys(contributor["firstName"])
            driver.find_element_by_id("bookContributors[0].lastName").send_keys(contributor["lastName"])

        ## right
        driver.find_element_by_css_selector('div[data-testid="wizard-goal-copyrightLicenseType.PD_CC_0"]').click()

        ## ISBN
        if book['goal'] == "lulu":
            pass

        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".next-step a")))
        driver.find_element_by_css_selector(".next-step a").click()
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'file-upload__dropzone__description')))

    # design
    drop_zone_book = driver.find_element_by_class_name("file-upload__dropzone__description")
    ## drop book file
    drop_zone_book.drop_files(file_path_book)
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'file-upload__loading')))
    WebDriverWait(driver, 360).until(EC.presence_of_element_located((By.CLASS_NAME, 'message--success')))
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="card_radio_button-interiorInk-BWPRE"]')))

    ## color
    driver.find_element_by_css_selector('div[data-testid="card_radio_button-interiorInk-{}"]'.format(book["interiorInk"])).click()
    ## paper
    driver.find_element_by_css_selector('div[data-testid="card_radio_button-interiorPaper-{}"]'.format(book["interiorPaper"])).click()
    ## binding
    driver.find_element_by_css_selector('div[data-testid="card_radio_button-bindingType-{}"]'.format(book["bindingType"])).click()
    ## cover finish
    driver.find_element_by_css_selector('div[data-testid="card_radio_button-coverFinish-{}"]'.format(book["coverFinish"])).click()

    drop_zone_cover = driver.find_element_by_css_selector('div[data-testid="wizard-goal-uploadCover"] .file-upload__dropzone__description')
    drop_zone_cover.drop_files()
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="wizard-goal-uploadCover"] .file-upload__loading')))
    WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="wizard-goal-uploadCover"] .message--success')))


def main():
    if len(driver.find_elements_by_css_selector('a[data-testid="main-nav-my-account"]')) == 0:
        login()
    create_project("supertest", file_path_book, file_path_cover)

main()