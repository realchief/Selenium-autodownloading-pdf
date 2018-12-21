from __future__ import division, absolute_import, unicode_literals
from scrapy import Spider, FormRequest, Request
import re
from selenium import webdriver
import os
from time import sleep
import requests

import os


class WashGasSpider(Spider):
    name = "washgas"
    start_urls = [
        'https://eservice.washgas.com/Pages/Login.aspx'
    ]

    PDF_LINK = 'https://eservice.washgas.com/Standard/BillPayments/Pages/_layouts/BillPayMgmt/ProcessPDFRequest.ashx?acctNum={account_number}&billDate={bill_date}&isInline=true'
    passed_vals = []

    def __init__(self, username=None, password=None, download_directory=None, *args, **kwargs):
        super(WashGasSpider, self).__init__(*args, **kwargs)
        self.user_name = username if username else 'ap@res1.net'
        self.password = password if password else 'Cy7tW4$RsQ'
        self.download_directory = download_directory if download_directory else 'C:/Users/webguru/Downloads/washgas/'

        if not os.path.exists(self.download_directory):
            os.makedirs(self.download_directory)

        cwd = os.getcwd().replace("\\", "//").replace('spiders', '')
        opt = webdriver.ChromeOptions()
        # opt.add_argument('--headless')
        self.driver = webdriver.Chrome(executable_path='{}/chromedriver.exe'.format(cwd), chrome_options=opt)

        with open('{}/scrapy.log'.format(cwd), 'r') as f:
            self.logs = [i.strip() for i in f.readlines()]
            f.close()

    def login(self):
        while True:
            try:
                user_email = self.driver.find_element_by_xpath(
                    '//form//input[contains(@name, "txtEmail")]'
                )
                user_email.send_keys(self.user_name)
                password = self.driver.find_element_by_xpath(
                    '//form//input[contains(@name,"txtPassword")]'
                )
                password.send_keys(self.password)
                btn_login = self.driver.find_element_by_xpath(
                    '//form//input[contains(@id, "btnSignIn")]'
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
        
        self.driver.get(response.url)
        self.login()

        while True:
            try:
                if self.driver.current_url != 'https://eservice.washgas.com/Standard/BillPayments/Pages/CurrentBill.aspx':
                    self.driver.get('https://eservice.washgas.com/Standard/BillPayments/Pages/CurrentBill.aspx')
                # sel = self.driver.find_element_by_xpath('//select[@class="account-dropdown"]')
                val = self.driver.find_element_by_xpath('//select[@class="account-dropdown"]//option[@selected]').get_attribute('value')

                title = self.driver.find_element_by_xpath('//select[@class="account-dropdown"]//option[@selected]').text
                pdf_link = self.driver.find_element_by_xpath('//iframe').get_attribute('src')
                account_number = re.search(r'acctNum=(\d+)&', pdf_link)
                account_number = account_number.group(1) if account_number else None

                bill_date = re.search(r'billDate=(.*?)&', pdf_link)
                bill_date = self.date_to_string(bill_date.group(1)) if bill_date else None
                if pdf_link and val not in self.passed_vals:
                    self.passed_vals.append(val)
                if '{}-{}'.format(account_number, bill_date) not in self.logs:
                    print '--------- downloading ---'
                    yield self.download_page(pdf_link, account_number, bill_date, title)

                options = self.driver.find_elements_by_xpath('//select[@class="account-dropdown"]//option[not(@selected)]')
                print options
                for opt in options:
                    if opt.get_attribute('value') not in self.passed_vals:
                        opt.click()
                        break
                if len(self.passed_vals) == len(options):
                    break
            except:
                sleep(10)
                continue

    def download_page(self, pdf_link, account_number=None, bill_date=None, title=None):
        raw_pdf = requests.get(pdf_link).content
        file_name = '{}-{}-{}.pdf'.format(self.download_directory, title, bill_date)

        with open(file_name, 'wb') as f:
            f.write(raw_pdf)
            self.logger.info('{} is downloaded successfully'.format(title))
            f.close()
        self.write_logs('{}-{}'.format(account_number, bill_date))
        return {
            'file_name': file_name,
            'file_url': pdf_link,
            'title': title,
            'account_number': account_number,
            'bill_date': bill_date
        }

    def date_to_string(self, d):
        d = d.split('/')
        return ''.join([i.zfill(2) for i in d])

    def write_logs(self, bill_id):
        with open('scrapy.log', 'a') as f:
            f.write(bill_id + '\n')
            f.close()
        self.logs.append(bill_id)
