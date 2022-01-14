from time import sleep, time

from functools import wraps

from urllib.parse import urlparse

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException


from config import conf, tracer

def debug_url(o):
    print (f"URL: {o.scheme} {o.hostname} {o.path}")

def url_paths_equalish(lhs, rhs):
    u1 = urlparse(lhs)
    u2 = urlparse(rhs)
    #debug_url(u1)
    #debug_url(u2)
    return u1.path == u2.path

def urls_equalish(lhs, rhs):
    u1 = urlparse(lhs)
    u2 = urlparse(rhs)
    #debug_url(u1)
    #debug_url(u2)
    
    return u1.scheme == u2.scheme \
        and u1.hostname == u2.hostname \
        and u1.path == u2.path \
        or (u1.path.startswith(u2.path))


def log(msg, prefix, *, end="\n", no_pad=False, flush=False):
    # ignore at a certain depth
    if conf["lvl"] > conf["max_lvl"]:
        return 

    pad = conf["lvl"] * "  " if not no_pad else ""
    symbol = f"[{prefix:^3}] " if not no_pad else ""
    print(f"{pad}{symbol}{msg}", end=end, flush=flush)

def chat(msg):
    log(msg, "i")
    
def err(msg):
    log(msg, "ERR")


@tracer
def wait_for_path(path, max_iters=500, tick=0.33, refresh=False):
    return wait_for_url(gen_url(path), max_iters, tick, refresh)


@tracer
def wait_for_url(url, max_iters=500, tick=0.33, refresh=False):
    
    if urls_equalish(conf["dom"].current_url, url):
        return True
    
    log(f"waiting for url: {url}", "D --", end=" ", no_pad=False, flush=True)

    for idx in range(max_iters):
        log(".", "", end="", flush=True, no_pad=True)
        sleep(tick)

        # stay here on url-missmatch, but go instantly once we are there!
        if urls_equalish(conf["dom"].current_url, url):
            return True
            
        #### http://192.168.10.50/apps/calendar vs.
        #### http://192.168.10.50/apps/calendar/something/bla
        #### startswith() ?? mmmh :()

        modulo = int(3 / tick)
        if refresh and idx % modulo == modulo-1:
            conf["dom"].refresh()
    print()
    return False

@tracer
def gen_url(path, host=None, proto=None):
    path = ("/" + path) if not path.startswith("/") else path
    return f"{conf['active_proto']}://{conf['active_host']}{path}"


@tracer
def click_xpath(path):
    ret = get_xpath(path)
    if not ret:
        return False
    ret.click()
    return ret

# @tracer
# def fast_xpath(path, root=None, as_list=False):
#     root = conf["dom"].find_element(By.XPATH, '//*[@id="app-content-vue"]')
#     try:
#         return root.find_element(By.XPATH, path) if not as_list \
#             else root.find_elements(By.XPATH, path)
#     except NoSuchElementException:
#         return False
    
@tracer
def get_xpath(path, as_list=False):
    #if not wait_for_path(path, 1):
    #    return False

    # self-build "idle" wait, to avoid missed elements
    # start = time()
    # needle = conf["dom"].find_element(By.XPATH, path)
    # while time() - start <= 2.0 and not needle:
    #     needle = conf["dom"].find_element(By.XPATH, path)
    #     sleep(0.05)

    # multi-select doesn't throw exceptions
    if as_list:
        return conf["dom"].find_elements(By.XPATH, path) or False
            
    try:
        return conf["dom"].find_element(By.XPATH, path)
    except NoSuchElementException:
        return False

@tracer
def wait_for_xpath(path, timeout):
    try:
        WebDriverWait(conf["dom"], timeout).until(
            EC.visibility_of_element_located((By.XPATH, path)))
        return True
    except TimeoutException:
        return False


