from config import conf
from utils import get_xpath, wait_for_xpath, wait_for_path, tracer, chat, err
from dom_tools import nextbox_sub_ensure

@tracer
def storages_info():
    if not nextbox_sub_ensure(2):
        return False

    items_mounted = '//*[@id="app-content-vue"]/div/div[1]/*/button'
    items_unmounted = '//*[@id="app-content-vue"]/div/div[2]/*/button'

    top = get_xpath(items_mounted, as_list=True)
    bottom = get_xpath(items_unmounted, as_list=True)
   
    chat(f"storages: top: #{top} - bottom: #{bottom}")
    return {"top": top or [], "bottom": bottom or []}
    
@tracer
def storages_roundtrip():
    if not nextbox_sub_ensure(2):
        return False

    # click on all mount/unmount you find
    info = storages_info()
    for el in info["top"] + info["bottom"]:
        el.click()
    return True

@tracer
def storages_backup_avail():
    if not nextbox_sub_ensure(2):
        return False

    info = storages_info()
    if len(info["bottom"]) > 0:
        for el in info["bottom"]:
            el.click()

    