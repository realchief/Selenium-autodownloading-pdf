from __future__ import division, absolute_import, unicode_literals
from scrapy import Spider, FormRequest, Request
import re
from selenium import webdriver
from time import sleep
import os
from dateutil.parser import parse


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
                if self.driver.current_url != 'https://eservice.washgas.com/Standard/BillPayments/Pages/BillingPaymentHistory.aspx':
                    self.driver.get('https://eservice.washgas.com/Standard/BillPayments/Pages/BillingPaymentHistory.aspx')

                val = self.driver.find_element_by_xpath('//select[@class="account-dropdown"]//option[@selected]').get_attribute('value')
                date_val = self.driver.find_elements_by_xpath(
                    '//select[@id="ctl00_SPWebPartManager1_g_bed3be53_cfc8_4589_ae53_958f96e4a203_ctl00_ddlBillDate"]//option')

                for v in date_val:
                    bill_date = v.get_attribute('value').split(';')[-1]

                    title = self.driver.find_element_by_xpath('//select[@class="account-dropdown"]//option[@selected]').text
                    title_list = title.split('  ')
                    account_infos = filter(None, title_list)
                    account_name = account_infos[0]
                    account_number = account_infos[1]
                    if '{}-{}'.format(account_number, bill_date) not in self.logs:
                        print '--------- downloading ---'
                        yield self.download_page(account_number, bill_date, account_name)

                if val not in self.passed_vals:
                    self.passed_vals.append(val)
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

    def download_page(self, account_number=None, bill_date=None, account_name=None):

        # raw_pdf = requests.get(pdf_link).content
        file_name = '{} {} {}.pdf'.format(account_number, account_name, bill_date)
        print file_name
        # with open(file_name, 'wb') as f:
        #     # f.write(raw_pdf)
        #     self.logger.info('{} is downloaded successfully'.format(account_name))
        #     f.close()
        self.write_logs('{}-{}'.format(account_number, bill_date))
        return {
            'file_name': file_name,
            'account_name': account_name,
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
