import argparse
import base64
import io
import time
from PIL import Image
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ExpectedCond
from time import sleep

import clicker
import image_edition
import nn_service_request


class AutoReservation:
    def __init__(
            self,
            username,
            password,
            reservation_date: str,
            reservation_time: str,
            reservation_arena: str,
            **kwargs
    ):
        self.driver: WebDriver = WebDriver(
            options=kwargs.get("webdriver_options"),
            service=kwargs.get("webdriver_service")
        )
        self.wait: WebDriverWait = WebDriverWait(
            self.driver,
            timeout=10
        )
        self.action_chains = ActionChains(self.driver)
        self.username = username
        self.password = password
        self.reservation_date = reservation_date
        self.reservation_time = reservation_time
        self.reservation_arena = reservation_arena

    def login(self):
        # 访问登录页面，点击”校内登录“按钮，等待页面跳转
        self.driver.get(r'https://elife.fudan.edu.cn/login.jsp')
        self.wait.until(
            ExpectedCond.element_to_be_clickable(
                (
                    By.CLASS_NAME,
                    "xndl"
                )
            )
        ).click()
        # 等待统一登录页面的用户名、密码和登录按钮显示出来
        self.wait.until(
            ExpectedCond.presence_of_element_located(
                (
                    By.ID,
                    'username'
                )
            )
        ).send_keys(self.username)
        self.wait.until(
            ExpectedCond.presence_of_element_located(
                (
                    By.ID,
                    'password'
                )
            )
        ).send_keys(self.password)
        self.wait.until(
            ExpectedCond.element_to_be_clickable(
                (
                    By.ID,
                    'idcheckloginbtn'
                )
            )
        ).click()
        # TODO:检查校园生活服务平台的登录状态

    def jump_to_confirm_page(self):
        # 点击场馆预约，这里有一个页面跳转的动作
        self.wait.until(
            ExpectedCond.presence_of_element_located(
                (
                    By.XPATH,
                    '//ul[@class="ydfw_r_content"]//li[1]//a[1]'
                )
            )
        ).click()
        time.sleep(1)
        self.driver.switch_to.window(self.driver.window_handles[-1])

        # 选择场馆，场馆列表使用iframe标签内嵌了一个网页，要切换frame
        gymListFrame = self.wait.until(
            ExpectedCond.presence_of_element_located(
                (By.ID, 'contentIframe')
            )
        )
        self.driver.switch_to.frame(gymListFrame)
        self.driver.find_element(by=By.XPATH, value="//a[contains(text(), '{}')]".format(self.reservation_arena)).click()
        # 点击预约，页面跳转
        time.sleep(1)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.wait.until(
            ExpectedCond.element_to_be_clickable(
                (
                    By.CLASS_NAME,
                    'button_order'
                )
            )
        ).click()
        # 选择日期和时间，时间选择列表是用iframe嵌入的页面，要切换frame到contentIframe
        timeListFrame = self.wait.until(
            ExpectedCond.presence_of_element_located(
                (By.ID, 'contentIframe')
            )
        )
        self.driver.switch_to.frame(timeListFrame)
        # 用js代码跳转到指定日期，函数名为goToDate
        self.driver.execute_script("""
            goToDate('{}')
        """.format(self.reservation_date))
        # 判断跳转到指定日期是否成功
        hoveredDate = self.driver.find_element(by=By.XPATH, value='//li[contains(@class, "hover")]').find_element(by=By.TAG_NAME, value='input').get_dom_attribute("value")
        assert self.reservation_date == hoveredDate
        # 查找预约时间，判断是否可以预约
        reservationBtn = self.driver.find_element(
            by=By.XPATH,
            value='//font[contains(text(), "{}")]'.format(self.reservation_time)
        ).find_element(
            By.XPATH,
            value='../../td[contains(@align, "right")]//img')
        # 判断reservationBtn是否有onClick属性
        if reservationBtn.get_dom_attribute('onClick'):
            # 可以预约
            reservationBtn.click()
            # 进入预约验证页面点击verify_button1
            verifyBtn = self.wait.until(
                ExpectedCond.element_to_be_clickable((By.ID, 'verify_button1'))
            )
            sleep(1)
            verifyBtn.click()
            # 等待直到valid_bg-img加载完成，从图片的src属性获取图片的base64编码
            self.wait.until(
                ExpectedCond.visibility_of_element_located((By.CLASS_NAME, 'valid_bg-img'))
            )

        else:
            # 不能预约
            raise Exception("场地：{}，日期：{}，时间：{}，无法预约".format(self.reservation_arena, self.reservation_date, self.reservation_time))

    def pass_verification(self):
        # 弹出验证码的模态窗口后进入该函数
        # 如果识别结果长度不足，则直接点击切换验证码，
        # 如果点击完成后，提示验证失败，则重新识别并点击
        # 直到识别成功
        while True:
            verifyPic_base64 = self.driver.find_element(
                By.CLASS_NAME, 'valid_bg-img'
            ).get_dom_attribute('src')
            verifyPic_base64 = verifyPic_base64.replace('data:image/jpg;base64,', '')  # 去掉base64头
            # base64 -> image data -> image stream -> Image对象
            verifyPic = Image.open(io.BytesIO(base64.decodebytes(verifyPic_base64.encode())))
            verifyCharTarget = self.wait.until(
                ExpectedCond.presence_of_element_located(
                    (By.XPATH, '//span[@class="valid_tips__text"]//b')
                )
            ).text
            verifyPicWithCharTarget = image_edition.image_edition(
                verifyPic,
                verifyCharTarget,
                r'C:\Windows\Fonts\simsun.ttc',
                35,
                (0, 0, 0),
                (255, 255, 255)
            )
            verifyPicWithCharTarget_base64 = image_edition.image2base64(verifyPicWithCharTarget)
            recogResults: list = nn_service_request.nn_service_request(verifyPicWithCharTarget_base64)
            if not len(recogResults) == len(verifyCharTarget):
                # 换验证码
                sleep(1)    # 防止点得太快了触发什么机制
                self.driver.find_element(By.CLASS_NAME, 'valid_refresh').click()
            else:
                # 点击对应位置
                verifyPicOffsetHeight = self.driver.find_element(By.CLASS_NAME, 'valid_bg-img').get_property('offsetHeight')
                verifyPicOffsetWidth = self.driver.find_element(By.CLASS_NAME, 'valid_bg-img').get_property('offsetWidth')
                x_stretch_rate = verifyPicOffsetWidth / verifyPic.width
                y_stretch_rate = verifyPicOffsetHeight / verifyPic.height
                click_position = [[None, None] for _ in range(len(verifyCharTarget))]
                for i, recogResult in enumerate(recogResults):
                    click_position[i][0] = (recogResult[0] + recogResult[2]) / 2 * x_stretch_rate
                    click_position[i][1] = (recogResult[1] + recogResult[3]) / 2 * y_stretch_rate

                clicker.action_chains_clicker(self.driver, click_position)

                # 检查是否通过验证，验证码模式窗口class = valid_popup是否关闭，以及验证成功id = verify_result是否成功
                isValidPopupClosed = self.driver.execute_script(
                    """
                        return window.getComputedStyle(arguments[0]).getPropertyValue("display");
                    """,
                    self.driver.find_element(By.CLASS_NAME, 'valid_popup')
                ) == 'none'
                isVerifyResultShowed = self.driver.execute_script(
                    """
                        return window.getComputedStyle(arguments[0]).getPropertyValue("display");
                    """,
                    self.driver.find_element(By.ID, 'verify_result')
                ) == 'block'
                if isValidPopupClosed and isVerifyResultShowed:
                    break

    def clean_up(self):
        self.driver.close()
        self.driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", type=str)
    parser.add_argument("--password", type=str)
    parser.add_argument("--reservation-date", type=str, help="预约日期，形式为yyyy-mm-dd")
    parser.add_argument("--reservation-time", type=str, help="预约时间段，形式为hh:mm")
    parser.add_argument("--reservation-arena", type=str, help="预约场地")
    args = parser.parse_args()
    ar = AutoReservation(
        args.username,
        args.password,
        args.reservation_date,
        args.reservation_time,
        args.reservation_arena
    )
    try:
        ar.login()
        ar.jump_to_confirm_page()
        ar.pass_verification()
    finally:
        ar.clean_up()

