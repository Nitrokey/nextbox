import sys
from time import sleep

from selenium import webdriver as drv
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException

from config import conf

# init, talk about "eyes"
opts = ChromeOptions()
br = drv.Chrome(chrome_options=opts)
br.implicitly_wait(15)
conf["dom"] = br

###################################
###################################

from utils import get_xpath, wait_for_xpath, wait_for_path, \
    tracer, chat, err, gen_url, click_xpath, wait_for_xpath, \
    wait_for_url, log
from dom_tools import where_in_nextbox, goto_nextbox_nav, \
    goto_nextbox, nextbox_sub_ensure
from test_storages import storages_roundtrip, storages_backup_avail



import pysnooper


@tracer
def get_proto(host):
    br.get(f"http://{host}")

    if br.current_url.startswith("https"):
        return "https"
    else:
        return "http"

@tracer
def ensure_host(host, proto=None):
    url_toks = br.current_url.split("/")
    my_host = url_toks[2]
    my_proto = url_toks[0][:-1]

    if host != my_host or (proto is not None and my_proto != proto):
        proto = proto or my_proto
        url = f"{proto}://{host}"
        open_page(url)
        chatty_sleep(f"tried to ensure: {host}, but found {my_host} -> getting: {url}")
    else:
        chat(f"ensuring url points to: {proto or my_proto}://{host}")

@tracer
def open_page(url=None, max_tries=10):
    url = gen_url("/") if url is None else url
    for idx in range(max_tries):
        try:
            br.get(url)
            return True
        except WebDriverException:
            err(f"could not open: {url}, try: {idx+1}")
    return False        
            
@tracer
def test_and_click_button(el_or_xpath, click=True):
    sleep(1)

    button = el_or_xpath
    if isinstance(el_or_xpath, str):
        button = get_xpath(el_or_xpath)
    
    if not button.is_enabled():
        chat("something went wrong, we would expect that the button is not disabled!")
        chat(str(el_or_xpath))
        return False
    else:
        chat("all conditions are met, let's push the button!!!")
        button.click()

    sleep(1)
    return True

@tracer
def input_into_text_field(xpath: str, text: str, clear: bool=True):
    el = get_xpath(xpath)
    if not el:
        return False
    
    wait_for_xpath(xpath, 5)
    el.click()

    if clear:
        clen = len(el.get_attribute("value"))
        el.send_keys("\b" * clen)
        wait_for_xpath(xpath, 5)
        #el.clear()

    wait_for_xpath(xpath, 5)
    el.send_keys(text)
    
    return True

@tracer
def test_for_valid_login_page(domain, proto):
    open_page(f"{proto}://{domain}")

    url = f"{proto}://{domain}/login"
    
    chat("waiting for correct url...")
    if not wait_for_url(url, refresh=True):
        chat("baaad, new url not 'found'")
        sleep(1)
        return False

    if not wait_for_xpath('//*[@id="user"]', 2):
        chat("cannot find login-input field(s)")
        sleep(1)
        return False

    sleep(1)
    return True


@tracer
def choose_login():
    if wait_for_xpath('//*[@id="user"]', 1):
        return regular_login()
    return first_login()

@tracer
def first_login():
    # fill in new admin credentials
    input_into_text_field('//*[@id="adminlogin"]', conf["user_login"])
    input_into_text_field('//*[@id="adminpass"]', conf["user_pass"])

    # submit form
    conf["dom"].find_elements_by_tag_name("form")[0].submit()

    chat("we submitted the form, 'things' should happen!")
    wait_for_path("/index.php/core/apps/recommended", max_iters=100)

    chat("recommended apps are being installed, good!")
    wait_for_path("/apps/dashboard/", max_iters=6000)

    chat("found dashboard, trying to 'esc' the welcome dialog away")
    conf["dom"].find_element_by_tag_name("body").send_keys(Keys.ESCAPE)

    return True

@tracer
def regular_login():
    input_into_text_field('//*[@id="user"]', conf["user_login"])
    input_into_text_field('//*[@id="password"]', conf["user_pass"])

    # submit form
    br.find_elements_by_tag_name("form")[0].submit()
    wait_for_path("/apps/dashboard/", max_iters=20)
    return True

@tracer
def logout():
    chat("logging out now, just because I can!")
    
    click_xpath('//*[@id="expand"]')
    chat("expanding, just for the show...")
    
    get_xpath('//*[@id="expanddiv"]')

    res = get_xpath('//li[@data-id="logout"]').find_element(By.TAG_NAME, "a")
    if not res:
        chat("failed logging out...")
        return False

    return res.click()


@tracer
def random_nextcloud_walk():
    chat("visiting some random nextcloud stuff")

    res = True
    for _ in ["files", "photos", "calendar", "mail"]:
        br.get(gen_url("/apps/files"))    


    br.get(gen_url("/apps/files"))
    res &= wait_for_path("/apps/files")

    br.get(gen_url("/apps/photos"))
    res &= wait_for_path("/apps/photos")

    br.get(gen_url("/apps/calendar"))
    res &= wait_for_path("/apps/calendar")
    return res


    
@tracer
def backup_test():
    if not nextbox_sub_ensure(3):
        return False

    cont_button_xp = '//*[@id="app-content-vue"]/div/div/button'
    
    # if this button exists, then we've a not cleaned up backup
    wait_for_xpath(cont_button_xp, 5)
    continue_button = get_xpath(cont_button_xp)
    
    if continue_button.is_enabled():
        chat("someone left his stuff here, cleaning up...")
        click_xpath(cont_button_xp)
    
    xp_dropdown = '//*[@id="app-content-vue"]/div/div[1]/div[1]/div[2]/input'
    if not wait_for_xpath(xp_dropdown, 5):
        return False
    
    # storage dropdown input field 
    click_xpath(xp_dropdown)
    chat("chooosing target storage - 1st click the dropdown")

    # now select first storage
    click_xpath('//*[@id="app-content-vue"]/div/div[1]/div[1]/div[3]/ul/li[1]/span/div/span[1]')
    chat("now click to choose")

    # now click into input field
    input_into_text_field('//*[@id="app-content-vue"]/div/div[1]/input', "xxxtest_backup_name")

    chat("enter our designated backup name")
    if not test_and_click_button('//*[@id="app-content-vue"]/div/div[1]/button'):
        return False

    wait_for_xpath(cont_button_xp, 5)
    continue_button = get_xpath(cont_button_xp)

    log(f"waiting for backup...", " B ", end=" ", no_pad=False, flush=True)
    while not continue_button.is_enabled():
        log(".", "", end="", no_pad=True, flush=True)
        sleep(0.5)
    print()
    
    banner_msg = get_xpath('//*[@id="app-content-vue"]/div/div/span').text
    
    # don't leave the backup un-cleaned-up
    click_xpath(cont_button_xp)

    if banner_msg == "Completed Backup successfully":
        return True

    return False

@tracer
def setup_and_test_proxy():
    if not nextbox_sub_ensure(5):
        return False
    
    input_xp = '//*[@id="app-content-vue"]/div/div[2]/input'
    button_xp = '//*[@id="app-content-vue"]/div/div[2]/button'

    but = get_xpath(button_xp)
    inp = get_xpath(input_xp)

    # no input? means proxy is active!
    if not inp:
        chat("proxy is enabled, disabling first")
        but.click()
    
    ret = input_into_text_field(input_xp, conf["proxy_domain"])
    if not ret:
        chat("failed input of proxy_domain")
        return False

    if not test_and_click_button(button_xp):
        chat("failed button click")
        return False
    
    chat("checking 'new' login page now")
    return test_for_valid_login_page(conf["proxy_domain"], "https")

@tracer        
def setup_and_test_static_dns():
    if not nextbox_sub_ensure(6):
        return False

    button_xp = '//*[@id="app-content-vue"]/div/div[2]/button'
    input_xp = '//*[@id="app-content-vue"]/div/div[2]/input'

    ret = input_into_text_field(input_xp, conf["static_domain"])
    if not ret:
        click_xpath(button_xp)
        chat("looks like it's already active, ok let's disable it and retry!")
        if not input_into_text_field(input_xp, conf["static_domain"]):
            chat("failed again, failing overall...")
            return False
        chat("cool, worked out")
    
    if not test_and_click_button(button_xp):
        return False

    chat("looks good so far, let's see if we can connect")
    return test_for_valid_login_page(conf["static_domain"], "http")

@tracer
def setup_and_test_tls():
    if not nextbox_sub_ensure(7):
        return False

    button_xp = '//*[@id="app-content-vue"]/div/div/div/div/button'

    if not input_into_text_field('//*[@id="app-content-vue"]/div/div/div/div/input', conf["email"]):
        
        chat("mmmh, TLS already enabled, uha: this might be painful...")
        
        if not test_and_click_button(button_xp):
            return False
        
        chat("now waiting (~15secs) for apache restart => jump back to non-https (i.e., recurse!)")

        br.delete_all_cookies()

        sleep(5)
        return setup_and_test_tls()

    sleep(1)

    if not test_and_click_button(button_xp):
        chat("cannot click button to activate, giving up...")
        return False

    chat("ok, certificate is on the way, let's wait some secs then check, if it works")
    sleep(10)

    return test_for_valid_login_page(conf["static_domain"], "https")

    
# open nextcloud, init, get schema and decide on login (1st init or regualar)
active_proto = get_proto(conf["active_host"])
open_page()
choose_login()

# some "warming up" look around inside nextcloud, finally get to the nextbox-app
random_nextcloud_walk()
goto_nextbox()

# 'storage_roundtrip' means: mount & umount any possible storage device once
storages_roundtrip()

# logout and login again
logout()
choose_login()

# setup and test the proxy configuration
goto_nextbox()
setup_and_test_proxy()

# setup and start/monitor a backup operation
goto_nextbox()
storages_backup_avail()
backup_test()

sleep(5)

# test static dns
goto_nextbox()
setup_and_test_static_dns()

sleep(5)

# set up TLS (with static domain)
goto_nextbox()
setup_and_test_tls()

