from selenium.webdriver import Firefox, Chrome, FirefoxProfile, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functools import wraps

import time

from selenium.webdriver.remote.webelement import WebElement


class WebElementError(Exception):
    pass


class WebExplorer:
    def __init__(self, explorer_type='random', **config):
        self.type = explorer_type
        self.download_path = config.get("download_path", None)
        self.web_driver = None
        self.windows = dict()
        self.recent_type = self.type

    def init_driver(self):
        if self.type == "firefox":
            self._init_firefox()
        elif self.type == "chrome":
            self._init_chrome()
        elif self.type == "random":
            if int(time.time()) % 2 == 0:
                self._init_firefox()
                self.recent_type = "firefox"
            else:
                self._init_chrome()
                self.recent_type = "chrome"
        self.windows['main'] = self.web_driver.window_handles[-1]

    def _init_firefox(self):
        profile = FirefoxProfile()
        if self.download_path:
            profile.set_preference("browser.download.dir", self.download_path)
            profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "binary/octet-stream")
        self.web_driver = Firefox(profile)

    def _init_chrome(self):
        options = ChromeOptions()
        config = dict()
        config['profile.default_content_settings.popups'] = 0
        if self.download_path:
            config['download.default_directory'] = self.download_path
        options.add_experimental_option("prefs", config)
        self.web_driver = Chrome(options=options)

    def nav(self, url):
        if self.web_driver:
            self.web_driver.get(url)

    def maximum(self):
        if self.web_driver:
            self.web_driver.maximize_window()

    @property
    def title(self):
        if self.web_driver:
            return self.web_driver.title

    def close(self):
        if self.web_driver:
            self.web_driver.quit()
            self.web_driver = None
            self.windows.clear()

    def open_new_window(self, name):
        self.web_driver.execute_script(f"window.open('about:blank', '{name}')")
        self.windows[name] = self.web_driver.window_handles[-1]

    def switch_to_window(self, name):
        if name not in self.windows:
            return
        self.web_driver.switch_to.window(self.windows[name])

    def close_window(self, name):
        if name not in self.windows:
            return
        self.web_driver.switch_to.window(self.windows[name])
        self.web_driver.close()

    def open_download_window(self):
        if self.web_driver:
            self.open_new_window("download")
            self.switch_to_window("download")
            if self.recent_type == "firefox":
                self.nav("about:downloads")
            else:
                self.nav("chrome://downloads/")


def element(func):
    @wraps(func)
    def inner(*args, **kwargs):
        selector = dict()
        mapping = args[0].__class__.element_mapping
        selector['id'] = mapping[func.__name__].get("id", None)
        selector['xpath'] = mapping[func.__name__].get("xpath", None)
        selector['css_selector'] = mapping[func.__name__].get("css_selector", None)
        selector['class_name'] = mapping[func.__name__].get("class_name", None)
        selector['link_text'] = mapping[func.__name__].get("link_text", None)
        selector['timeout'] = mapping[func.__name__].get("timeout", 10)
        if hasattr(args[0], "element"):
            parent = args[0].element
        else:
            parent = args[0].explorer
        obj = mapping[func.__name__]['type'](parent, **selector)
        return func(*args, ret=obj)
    return inner


def webpage(page_data):
    def decorator(cls):
        setattr(cls, "element_mapping", page_data)
        return cls
    return decorator


class Element:
    """
    页面元素封装
    """
    element_mapping = dict()

    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.xpath = kwargs.get("xpath", None)
        self.id = kwargs.get("id", None)
        self.class_ = kwargs.get("class_name", None)
        self.css = kwargs.get("css_selector", None)
        self.link_text = kwargs.get("link_text", None)
        self.timeout = kwargs.get("timeout", 10)
        self.element = self._get_element()

    def _get_element(self):
        if self.xpath:
            by = By.XPATH
            locator = self.xpath
        elif self.id:
            by = By.ID
            locator = self.id
        elif self.css:
            by = By.CSS_SELECTOR
            locator = self.css
        elif self.class_:
            by = By.CLASS_NAME
            locator = self.class_
        elif self.link_text:
            by = By.LINK_TEXT
            locator = self.link_text
        else:
            raise WebElementError("no locator")
        return WebDriverWait(
            self.parent, self.timeout).until(EC.presence_of_element_located((by, locator))
            )

    def input_text(self, text):
        self.element.send_keys(text)

    def click(self):
        self.element.click()


header_data = {"search_text": {"type": Element, "id": "kw"}, "go_button": {"type": Element, "id": "su"}}


@webpage(header_data)
class Header(Element):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    @element
    def search_text(self, ret):
        return ret

    @element
    def go_button(self, ret):
        return ret


page_data = {"header":{"type": Header, "id": "head_wrapper"}}


@webpage(page_data)
class PageSearch:
    def __init__(self, explorer):
        self.explorer = explorer

    @element
    def header(self, ret):
        return ret



wb = WebExplorer("random")
wb.init_driver()
wb.nav("http://www.baidu.com")
page = PageSearch(wb.web_driver)
page.header().search_text().input_text("selenium")
page.header().go_button().click()


