"""
Main module for Bitacora creation or updating

To do this:
    - Clockfy (app time tracker) is used

Required libraries:
    - Selenium for web management (pip install -U selenium)
"""

import time
import logging
from pathlib import Path
from typing import Any
import pandas as pd
from argparse import ArgumentParser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

import credentials as cdt

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
handler_formatter = logging.Formatter('[%(asctime)-26s] (%(name)s) - %(levelname)-8s :: %(message)s')
handler.setFormatter(handler_formatter)
logger.addHandler(handler)

parser = ArgumentParser()
parser.add_argument('--date_range', dest='date_range', action='store', default='Last week',
                    help="Date range for updating Bitacora. e.g: ['This week', 'Last week', '03/04/2023 - 07/04/2023]")
args = parser.parse_args()

PICKED_DATE_RANGE = args.date_range


class Bitacora:
    """ Create a Bitacora instance to manage all the actions"""

    def __init__(self):
        self.driver = None
        self.bitacora_file = None
        self.bitacora_df = None

    def _wait_visible_element(self, locator: Any) -> Any:
        # Function to wait until some event
        wait = WebDriverWait(self.driver, 20)
        element = wait.until(EC.visibility_of_element_located(locator))
        return element

    def download_clockify_time_report(self) -> None:
        """
        Download the weekly clockify time report from the webpage

        TODO: replace hardcoded variables content
        """
        # Options for the browser:
        # - headless= True to hide the browser window
        options = Options()
        options.add_argument("-headless")
        # Take de driver file from /usr/local/bin
        self.driver = webdriver.Firefox(options=options)

        logger.debug("Opening URL")

        # Open the url on the selected browser
        self.driver.get(cdt.CLOCKIFY_URL)

        logger.debug("Logging to the APP")

        # Fill email login field.
        email_login_element = self._wait_visible_element((By.NAME, "email"))
        # email_login_element = self.driver.find_element(By.NAME, "email")
        email_login_element.send_keys(cdt.CLOCKIFY_USER_MAIL)
        # Fill password login field.
        pass_login_element = self.driver.find_element(By.NAME, "password")
        pass_login_element.send_keys(cdt.CLOCKIFY_USER_PASSWORD)
        # Click log in button
        login_button_element = self.driver.find_element(By.CLASS_NAME, "cl-btn")
        login_button_element.click()

        logger.debug(f"Selecting '{PICKED_DATE_RANGE}' as date range option")

        # Click datepicker
        back_button_xpath = "/html/body/app-root/default-layout/div/main/div" \
                            "/app-detailed-reports/div/div/div[1]/div/div[2]" \
                            "/div/div/datepicker-range/div[1]/button[1]"
        span_datepickerrange_xpath = "/html/body/app-root/default-layout/div" \
                                     "/main/div/app-detailed-reports/div/div" \
                                     "/div[1]/div/div[2]/div/div/datepicker-range" \
                                     "/div[1]/div/div/span"
        datepicker_button_element = self._wait_visible_element((By.XPATH, back_button_xpath))
        span_datepickerrange_element = self.driver.find_element(By.XPATH, span_datepickerrange_xpath)

        while not span_datepickerrange_element.text == PICKED_DATE_RANGE:
            # datepicker_button_element.click() # does not work, no idea!!!
            # However, below command works for clicking the button
            self.driver.execute_script("arguments[0].click();", datepicker_button_element)
        time.sleep(15)

        logger.debug("Exporting data as CSV file")

        # Select an option from a dropdown menu
        dropdown_xpath = '/html/body/app-root/default-layout/div/main/div' \
                         '/app-detailed-reports/div/div/table-info/div/div[3]' \
                         '/div[1]/div[1]/div'
        # export_dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, dropdown_xpath)))
        export_dropdown = self.driver.find_element(By.XPATH, dropdown_xpath)
        self.driver.execute_script("arguments[0].click();", export_dropdown)
        dropdown_menu_xpath = "/html/body/app-root/default-layout/div/main/div" \
                              "/app-detailed-reports/div/div/table-info/div" \
                              "/div[3]/div[1]/div[1]/div[2]/div/a[2]"
        export_dropdown_menu = self._wait_visible_element((By.XPATH, dropdown_menu_xpath))
        self.driver.execute_script("arguments[0].click();", export_dropdown_menu)

        logger.debug("Bitacora CSV file downloaded succesfully!!!")

    def change_bitacora_file_location(self) -> None:
        """ Changes the location of the downloaded file

        By default, the file is stored in "downloads(Descargas) folder. For
        better management, the file is moved to the script location
        """
        found_file_flag = False
        downloads_folder = Path.home().joinpath(cdt.FOLDER_TO_DOWNLOAD)
        while not found_file_flag:
            logger.debug("Listing xlsx files")
            xlsx_files = list(downloads_folder.glob('**/*.csv'))
            logger.debug("Finding Clockify file")
            for xlsx_file in xlsx_files:
                if xlsx_file.name.startswith("Clockify"):
                    found_file_flag = True
                    logger.debug("Moving last week clockify file")
                    self.bitacora_file = Path.cwd().joinpath(xlsx_file.name)
                    xlsx_file.replace(self.bitacora_file)
            time.sleep(1)
        # After wait for file to download, close safely the webdriver.Firefox
        # (delete all the files located at /tmp folder)
        self.driver.quit()

    def extract_time_range_information(self) -> None:
        """ Extract the date range of the downloaded week report"""
        file_name_wo_suffix = self.bitacora_file.stem
        end_date = file_name_wo_suffix.split("-")[1]
        start_date = file_name_wo_suffix.split("-")[0].split("_Detailed_")[1]

        logger.info(f"Time range from {start_date} to {end_date}")

        start_day, start_month, start_year = start_date.split("_")
        end_day, end_month, end_year = end_date.split("_")

    def clean_downloaded_csv_data(self) -> None:
        """ Clean the csv file removing unused columns and organizing remaining
        ones
        """
        # self.bitacora_file = "Clockify_Time_Report_Detailed_13_03_2023-19_03_2023.csv"
        self.bitacora_df = pd.read_csv(self.bitacora_file)
        # print(self.bitacora_df.head(10))
        # Remove unnecessary columns
        self.bitacora_df = self.bitacora_df.drop(
            columns=['Client', 'Task', 'User', 'Group', 'Email', 'End Date']
            )
        # Create a column for the sum of day times
        self.bitacora_df['Total time'] = ''
        # print(bitacora_df.groupby(['Start Date'])['Duration (decimal)'].sum().reset_index())
        self.bitacora_df = self.bitacora_df.set_index(
            ['Start Date']).sort_index(axis=0, ascending=True).reset_index()
        # print(self.bitacora_df['Start Date'].unique())

    def _add_row_with_total_time_date(self, date: str) -> pd.DataFrame:
        """ Add a row at the end of every date block with the Total time column
        filled with time in a decimal format"""
        date_block_df = self.bitacora_df[self.bitacora_df['Start Date'] == date]
        date_total_time = date_block_df['Duration (decimal)'].sum()
        total_time_row = pd.DataFrame({'Start Date': date, 'Total time': date_total_time}, index=[0])
        date_block_df = pd.concat([date_block_df.loc[:], total_time_row]).reset_index(drop=True)
        return date_block_df

    def update_bitacora_file(self) -> None:
        """ Updates the xlsx bitacora file with new week entries"""
        bitacora_xlsx_path = Path.cwd().joinpath(cdt.BITACORA_FILE_NAME)
        if not bitacora_xlsx_path.exists():
            logger.info(f"Creating xlsx file: {bitacora_xlsx_path}")
            self.bitacora_df.to_excel(bitacora_xlsx_path, index=False, sheet_name="Sheet1")
            return

        for date in self.bitacora_df['Start Date'].unique():
            date_df = self._add_row_with_total_time_date(date)
            with pd.ExcelWriter(
                    bitacora_xlsx_path,
                    mode="a",
                    engine="openpyxl",
                    if_sheet_exists="overlay"
                    ) as writer:
                date_df.to_excel(
                    writer,
                    index=False,
                    header=False,
                    sheet_name="Sheet1",
                    startrow=writer.sheets['Sheet1'].max_row
                    )

        logger.info("¡Bitacora updated!")


def main():
    bitacora_manager = Bitacora()
    bitacora_manager.download_clockify_time_report()
    bitacora_manager.change_bitacora_file_location()
    bitacora_manager.extract_time_range_information()
    bitacora_manager.clean_downloaded_csv_data()
    bitacora_manager.update_bitacora_file()


if __name__ == '__main__':
    main()
