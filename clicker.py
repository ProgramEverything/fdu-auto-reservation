from typing import List

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.webdriver import WebDriver


def action_chains_clicker(driver: WebDriver, click_position: List):
    """
    action chains似乎有bug，光标不能点在正确的位置，特别是offset的值为负数时
    :param driver:
    :param click_position:
    :return:
    """
    verifyPicOffsetHeight = driver.find_element(By.CLASS_NAME, 'valid_bg-img').get_property('offsetHeight')
    verifyPicOffsetWidth = driver.find_element(By.CLASS_NAME, 'valid_bg-img').get_property('offsetWidth')
    mouse_offsets = [[0, 0] for _ in range(len(click_position))]
    last_x = verifyPicOffsetWidth / 2
    last_y = verifyPicOffsetHeight / 2
    action_chains = ActionChains(driver)
    for i, click_position in enumerate(click_position):
        mouse_offsets[i][0] = click_position[i][0] - last_x
        mouse_offsets[i][1] = click_position[i][1] - last_y
        last_x = click_position[i][0]
        last_y = click_position[i][1]
    for id, mouse_offset in enumerate(mouse_offsets):
        if id == 0:
            action_chains.move_to_element_with_offset(
                driver.find_element(By.CLASS_NAME, 'valid_bg-img'),
                mouse_offset[0],
                mouse_offset[1]
            ).click()
        else:
            action_chains.move_by_offset(
                mouse_offset[0],
                mouse_offset[1]
            ).click()
    action_chains.perform()