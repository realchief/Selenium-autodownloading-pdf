from __future__ import division, absolute_import, unicode_literals
from scrapy import Spider
from selenium import webdriver
import os
from time import sleep
import re

class WashGasSpider(Spider):
    name = "washgas_add_accounts"
    start_urls = [
        'https://eservice.washgas.com/Pages/Login.aspx'
    ]

    PDF_LINK = 'https://eservice.washgas.com/Standard/BillPayments/Pages/_layouts/BillPayMgmt/ProcessPDFRequest.ashx?acctNum={account_number}&billDate={bill_date}&isInline=true'
    accounts = []

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; '
                      'Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
    }

    def __init__(self, username=None, password=None, file_name="WashGas Accounts.csv" ,*args, **kwargs):
        super(WashGasSpider, self).__init__(*args, **kwargs)
        self.user_name = username if username else 'ap@res1.net'
        self.password = password if password else 'Cy7tW4$RsQ'
        self.file_name = file_name

        cwd = os.getcwd()
        opt = webdriver.ChromeOptions()
        # opt.add_argument('--headless')
        self.driver = webdriver.Chrome(executable_path='{}/chromedriver.exe'.format(cwd), chrome_options=opt)

    def login(self):
        while True:
            try:
                user_email = self.driver.find_element_by_xpath(
                    '//form//input[@name="ctl00$SPWebPartManager1$g_778d3a08_260c_4a12_808d_a051c9581a61$ctl00$txtEmail"]'
                )
                user_email.send_keys(self.user_name)
                password = self.driver.find_element_by_xpath(
                    '//form//input[@name="ctl00$SPWebPartManager1$g_778d3a08_260c_4a12_808d_a051c9581a61$ctl00$txtPassword"]'
                )
                password.send_keys(self.password)
                btn_login = self.driver.find_element_by_xpath(
                    '//form//input[@name="ctl00$SPWebPartManager1$g_778d3a08_260c_4a12_808d_a051c9581a61$ctl00$btnSignIn"]'
                )
                btn_login.click()
                break
            except:
                sleep(10)
                continue

        while True:
            try:
                self.driver.find_element_by_xpath('//span[@class="menu-item-text" and contains(text(), "Account")]')
                break
            except:
                sleep(100)
                continue

    def parse(self, response):
        self.read_csv()
        idx = 0
        self.driver.get(response.url)

        self.login()

        while True:
            try:
                if idx == len(self.accounts):
                    break
                if self.driver.current_url != 'https://eservice.washgas.com/Pages/AddAccount.aspx':
                    self.driver.get('https://eservice.washgas.com/Pages/AddAccount.aspx')
                account_id = self.driver.find_element_by_xpath('//label[contains(text(), "Account")]').get_attribute('for')
                account_inp = self.driver.find_element_by_id(account_id)
                account_inp.send_keys(self.accounts[idx].get('id'))
                house_id = self.driver.find_element_by_xpath('//label[contains(text(), "Building")]').get_attribute('for')
                house_inp = self.driver.find_element_by_id(house_id)
                house_inp.send_keys(self.accounts[idx].get('house_number'))
                self.driver.find_element_by_xpath('//input[@value="Submit"]').click()
                idx += 1
            except:
                sleep(10)
                continue

    def read_csv(self):
        with open(self.file_name, 'r') as csvfile:
            spamreader = csvfile.readlines()
            for row in spamreader:
                account = re.findall('(\d+)', row)
                if len(account)== 2:
                    self.accounts.append({
                        'id': account[0],
                        'house_number': account[1]
                    })
