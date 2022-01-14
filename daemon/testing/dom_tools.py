from time import sleep

from config import conf
from utils import get_xpath, wait_for_xpath, wait_for_path, tracer, \
    chat, err, click_xpath, gen_url, url_paths_equalish

from selenium.webdriver.common.by import By


@tracer
def goto_nextbox_by_icon():
    click_xpath('//a[@aria-label="NextBox App"]')
    return wait_for_path("/apps/nextbox/")

@tracer
def goto_nextbox():
    # already there?
    if wait_for_path("/apps/nextbox/", 1):
        return True
        
    # go to nextbox app
    conf["dom"].get(gen_url("/apps/nextbox/"))
    sleep(1)
    return wait_for_path("/apps/nextbox/")
    
@tracer
def goto_nextbox_nav(idx):
    if not url_paths_equalish(conf["dom"].current_url, "/apps/nextbox/"):
        if not goto_nextbox():
            return False
        sleep(1)

    navs = get_xpath('//*[@id="app-navigation-vue"]').find_elements(By.TAG_NAME, "li")
    navs = [nav.find_element(By.TAG_NAME, "a") for nav in navs]

    try:
        navs[idx-1].click()
    except Exception:
        return False
    return True


@tracer
def nextbox_sub_ensure(idx):
    where = where_in_nextbox()
    if where is None:
        return False

    if not where == idx:
        err(f"not in {idx}, switching")
        if not goto_nextbox_nav(idx):
            return False

    # @TODO: e.g., here wait until magic element is visible,
    # which signalizes that the page has done loading...
    sleep(1)
    return True  


@tracer
def where_in_nextbox():
    title_xpath = '//*[@id="app-content-vue"]/div/div[1]/h2'
    el = get_xpath(title_xpath)
    if not el:
        err("not even inside nextbox app?")
        return False

    dct = {
        "Remote Access for Your NextBox": 1,
        "Mounted Storages": 2,
        "Full System Backup": 3,
        "Remote Access - Status": 4,
        "Backwards Proxy Remote Access for Your NextBox": 5,
        "Static Domain Configuration": 6,
        "HTTPS / TLS Configuration": 7,
        "System Logs": 8
    }
    out = dct.get(el.text)
    if out is None:
        err("could not determine where we are inside the nextbox app")
    return out