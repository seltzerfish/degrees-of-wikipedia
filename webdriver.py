from selenium import webdriver
from time import sleep
from numpy import linspace
import os


SCROLL_FRAMES = 200  # 100 frames is roughly 1 sec
EXP_DEGREE = 6 # positive even integer. Controls scroll smoothness

def show_results(results):
    results = [r[0] for r in results]
    driver = webdriver.Firefox()
    driver.get("https://en.wikipedia.org/wiki/" + results[0])
    cmd = """osascript -e 'tell app "Firefox" to activate'"""
    # os.system(cmd)  # uncomment if mac user
    del results[0]
    for r in results:
        element = driver.find_element_by_xpath('//a[@href="/wiki/'+r+'"]')
        final_pos = max(2, element.location['y'] - 100)
        if final_pos > 20:
            median = final_pos // 2
            cf = median / (median ** EXP_DEGREE)
            scroll_range = [round(cf * (i ** EXP_DEGREE))
                            for i in linspace(0, median, SCROLL_FRAMES // 2)]
            scroll_range += [round(cf * -1 * ((i - final_pos) ** EXP_DEGREE) + final_pos)
                             for i in linspace(median, final_pos, SCROLL_FRAMES // 2)][1:]

            for x in scroll_range:
                driver.execute_script("window.scrollTo(0, {})".format(x))
        highlight(element)
        element.click()


def highlight(element):
    """Highlights (blinks) a Selenium Webdriver element"""
    driver = element._parent

    def apply_style(s):
        driver.execute_script("arguments[0].setAttribute('style', arguments[1]);",
                              element, s)
    original_style = element.get_attribute('style')
    apply_style("background: yellow; border: 2px solid red;")
    sleep(1)
    apply_style(original_style)
