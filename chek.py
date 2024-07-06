import re
import requests
from bs4 import BeautifulSoup
import streamlit as st
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ECASStatusChecker:
    def __init__(self, lastname: str, iuc_identifier: int, birthday: str, birth_country_code: str):
        self.lastname = lastname
        self.iuc_identifier = iuc_identifier
        self.birthday = birthday
        self.birth_country_code = birth_country_code
        self.session = requests.Session()
        logger.info(f'Initialized ECASStatusChecker for {lastname} with IUC {iuc_identifier}')

    def generate_header(self, referer: str):
        headers = {
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-GPC": "1",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{referer}",
            "Accept-Language": "en-US,en;q=0.9",
        }
        logger.debug(f'Generated headers for referer: {referer}')
        return headers

    def check_status(self):
        try:
            logger.info('Starting status check')
            # 1 Pass intro page
            headers = self.generate_header("https://services3.cic.gc.ca/ecas/introduction.do?app=")
            self.session.get("https://services3.cic.gc.ca/ecas/security.do", headers=headers)
            logger.debug('Passed intro page')

            # 2 Validate security
            headers = self.generate_header("https://services3.cic.gc.ca/ecas/security.do")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            headers["Origin"] = "https://services3.cic.gc.ca"
            data = {"lang": "", "app": "", "securityInd": "agree", "_target1": "Continue"}
            self.session.post("https://services3.cic.gc.ca/ecas/security.do", headers=headers, data=data)
            logger.debug('Security validated')

            # 3 Send info to get to user page
            headers = self.generate_header("https://services3.cic.gc.ca/ecas/authenticate.do")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            headers["Origin"] = "https://services3.cic.gc.ca"

            data = {
                "lang": "",
                "_page": "_target0",
                "app": "",
                "identifierType": "1",
                "identifier": f"{self.iuc_identifier}",
                "surname": f"{self.lastname}",
                "dateOfBirth": self.birthday,
                "countryOfBirth": f"{self.birth_country_code}",
                "_submit": "Continue",
            }

            response3 = self.session.post(
                "https://services3.cic.gc.ca/ecas/authenticate.do",
                headers=headers,
                data=data,
            )
            logger.debug('User information submitted')

            status = "".join(
                BeautifulSoup(
                    response3.text, "html.parser"
                ).td.next_sibling.next_sibling.a.text.split()
            )
            logger.info(f'Status retrieved: {status}')

            # 4 Click on the link to see detail of PR
            headers = self.generate_header("https://services3.cic.gc.ca/ecas/viewcasestatus.do")

            rp_id = re.search(
                "(?:id=)(\d*)(?:&+?)",
                BeautifulSoup(response3.text, "html.parser").td.next_sibling.next_sibling.a[
                    "href"
                ],
            ).group(1)
            params = (
                ("id", f"{rp_id}"),
                ("type", "prCases"),
                ("source", "db"),
                ("app", ""),
                ("lang", "en"),
            )

            response4 = self.session.get(
                "https://services3.cic.gc.ca/ecas/viewcasehistory.do",
                headers=headers,
                params=params,
            )

            if response3.status_code != 200:
                raise Exception("An error occurred with IRCC. Form submission failed")
            logger.info('Detailed case information retrieved')

            detail = []
            for li in BeautifulSoup(response4.text, "html.parser").find_all(
                "li", class_="mrgn-bttm-md"
            ):
                detail.append(li.string)
            logger.info(f'Case details: {detail}')

            return status, detail

        except Exception as e:
            logger.error(f'Error occurred: {e}')
            return str(e), []

# Example of how to use in a Streamlit application
def main():
    st.title("ECAS Status Checker")

    lastname = st.text_input("Lastname (capitalized)")
    iuc_identifier = st.number_input("IUC Identifier", min_value=0, step=1)
    birthday = st.date_input("Birthday (YYYY-MM-DD)")

    birth_country_code = 622 # This should be replaced with the correct country code mapping

    if st.button("Check Status"):
        with st.spinner("Checking status..."):
            checker = ECASStatusChecker(
                lastname=lastname,
                iuc_identifier=iuc_identifier,
                birthday=birthday.strftime("%Y-%m-%d"),
                birth_country_code=birth_country_code
            )
            status, detail = checker.check_status()

            st.write(f"Your status is: {status}")
            st.write("The detail of your process is:")
            for item in detail:
                st.write(f"- {item}")

if __name__ == "__main__":
    main()
