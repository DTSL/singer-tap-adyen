"""PayPal API Client."""
# -*- coding: utf-8 -*-

import logging
from csv import DictReader
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Callable, Generator, Optional
from time import sleep

import requests
import requests.adapters
import singer

API_SCHEME: str = "https://"
API_BASE_URL_LIVE: str = "ca-live.adyen.com"
API_BASE_URL_TEST: str = "ca-test.adyen.com"
API_PATH_REPORTS: str = "/reports/download"
API_PATH_REPORTS_COMPANY: str = "/Company/:company:"
API_PATH_REPORTS_MERCHANT: str = "/MerchantAccount/:merchant:"
API_PATH_DISPUTE_REPORT: str = "/dispute_report_:date:.csv"
API_PATH_PAYMENT_REPORT: str = "/payments_accounting_report_:date:.csv"
API_PATH_SETTLEMENT_REPORT: str = "/settlement_detail_report_batch_:batch:.csv"

HEADERS: MappingProxyType = MappingProxyType(
    {
        "User-Agent": ("Singer Tap: GitHub.com/Yoast/singer-tap-adyen/ | By Yoast.com"),
    }
)


class Adyen(object):  # noqa: WPS230
    """Adyen API Client."""

    def __init__(  # noqa: WPS211
        self,
        report_user: str,
        company_account: str,
        user_password: str,
        merchant_account: str,
        test: bool,
    ) -> None:
        """Initialize Adyen client.

        Arguments:
            report_user {str} -- Reporting user username
            company_account {str} -- Adyen company account
            user_password {str} -- Reporing user API key
            merchant_account {str} -- Adyen merchant account
            test {bool} -- Whether to use the test or live environmennt
        """
        self.report_user: str = report_user
        self.company_account: str = company_account
        self.user_password: str = user_password
        self.merchant_account: str = merchant_account
        self.test: bool = test

        # Setup reusable web client
        self.client: requests.Session = requests.session()

        # Enable simple retry logic as per https://docs.python-requests.org/en/latest/api/#requests.adapters.HTTPAdapter
        self.client.mount("https://", requests.adapters.HTTPAdapter(max_retries=3))
        self.client.mount("http://", requests.adapters.HTTPAdapter(max_retries=3))

        # Setup logger
        self.logger: logging.RootLogger = singer.get_logger()

        # Check what URL to use (test/live)
        self.base_url = API_BASE_URL_TEST if test else API_BASE_URL_LIVE

    def dispute_transaction_details(  # noqa: WPS210
        self,
        start_date: str,
        initial_full_table_complete: bool,
    ) -> Generator[str, None, None]:
        """Get the dispute transaction report URLS.

        Arguments:
            start_date {str} -- Starting date to start generating urls from

        Yields:
            Generator[str, None, None]} -- Urls of dispute transaction reports
        """
        self.logger.info(
            "Looking for dispute transaction details reports. Starting with "
            f"date: {start_date}",
        )

        # Parse start_date string to date
        parsed_date: datetime = datetime.strptime(start_date, "%Y-%m-%d")

        # Replace placeholder in reports path
        company: str = API_PATH_REPORTS_COMPANY.replace(
            ":company:",
            self.company_account,
        )

        # Loop through increasing dates
        while True:
            # Fill in placeholder
            date: str = parsed_date.strftime("%Y_%m_%d")
            report: str = API_PATH_DISPUTE_REPORT.replace(
                ":date:",
                str(date),
            )

            # Create the URL
            url: str = (
                f"{API_SCHEME}{self.base_url}"
                f"{API_PATH_REPORTS}"
                f"{company}"
                f"{report}"
            )

            # Perform a HEAD request on the report url
            response: requests.Response = self._head_request(url)  # noqa: WPS437

            # The report with the batch number exists
            if response.status_code == 200:  # noqa: WPS432
                self.logger.info(
                    f"Found dispute transaction details report date: {date}",
                )

                # Yield the URL
                yield url

                # Increate the day by 1 day
                parsed_date = parsed_date + timedelta(days=1)

            # No report found, stop the loop
            elif response.status_code == 404:  # noqa: WPS432
                if (
                    not initial_full_table_complete
                    and parsed_date < datetime.utcnow() + timedelta(days=-1)
                ):
                    self.logger.info(
                        f"Dispute transaction details report date: {date} not "
                        "found, continue.",
                    )

                    # Increate the day by 1 day
                    parsed_date = parsed_date + timedelta(days=1)

                    pass
                else:
                    self.logger.debug(
                        f"Dispute transaction details report date: {date} not "
                        "found, stopping.",
                    )
                    break

            # Unexpected HTTP response
            else:
                self.logger.critical(
                    f"Unexpected HTTP status code while checking: {url}. ",
                    f"({response.status_code})",
                )
                response.raise_for_status()

        self.logger.info("Finished: Dispute Transaction Reports")

    def payment_accounting(  # noqa: WPS210
        self,
        start_date: str,
        initial_full_table_complete: bool,
    ) -> Generator[str, None, None]:
        """Get the Payment Accounting Report URLS.

        Arguments:
            start_date {str} -- starting date to start generating urls from

        Yields:
            Generator[str, None, None]}  -- Urls of payment accountinng reports
        """
        self.logger.info(
            "Looking for payment accounting reports. Starting with date: "
            f"{start_date}",
        )

        # Parse start_date string to date
        parsed_date: datetime = datetime.strptime(start_date, "%Y-%m-%d")

        # Replace placeholder in reports path
        merchant: str = API_PATH_REPORTS_MERCHANT.replace(
            ":merchant:",
            self.merchant_account,
        )

        # Loop through increasing dates
        while True:
            # Fill in placeholder
            date: str = parsed_date.strftime("%Y_%m_%d")
            report: str = API_PATH_PAYMENT_REPORT.replace(
                ":date:",
                str(date),
            )

            # Create the URL
            url: str = (
                f"{API_SCHEME}{self.base_url}"
                f"{API_PATH_REPORTS}"
                f"{merchant}"
                f"{report}"
            )

            # Perform a HEAD request on the report url
            response: requests.Response = self._head_request(url)  # noqa: WPS437

            # The report with the batch number exists
            if response.status_code == 200:  # noqa: WPS432
                self.logger.info(
                    f"Found payment accounting report date: {date}",
                )

                # Yield the URL
                yield url

                # Increate the day by 1 day
                parsed_date = parsed_date + timedelta(days=1)

            # No report found, stop the loop
            elif response.status_code == 404:  # noqa: WPS432
                if (
                    not initial_full_table_complete
                    and parsed_date < datetime.utcnow() + timedelta(days=-1)
                ):
                    self.logger.info(
                        f"Dispute transaction details report date: {date} not "
                        "found, continue.",
                    )

                    # Increate the day by 1 day
                    parsed_date = parsed_date + timedelta(days=1)

                    pass
                else:
                    self.logger.debug(
                        f"Dispute transaction details report date: {date} not "
                        "found, stopping.",
                    )
                    break

            # Unexpected HTTP response
            else:
                self.logger.critical(
                    f"Unexpected HTTP status code while checking: {url}. ",
                    f"({response.status_code})",
                )
                response.raise_for_status()

        self.logger.info("Finished: Payment Accounting Reports")

    def settlement_details(
        self,
        batch_number: int,
        initial_full_table_complete: bool,
    ) -> Generator[str, None, None]:
        """Get the settlement details report URLs.

        Arguments:
            batch_number {int} -- Batch number to start generating urls from

        Yields:
            Generator[str, None, None] -- Urls of settlement detail reports
        """
        self.logger.info(
            "Looking for settlement details reports. Starting with batch: "
            f"{batch_number}",
        )

        # Replace placeholder in reports path
        merchant: str = API_PATH_REPORTS_MERCHANT.replace(
            ":merchant:",
            self.merchant_account,
        )

        # Loop through increasing batch numbers
        while True:
            # Fill in placeholder
            report: str = API_PATH_SETTLEMENT_REPORT.replace(
                ":batch:",
                str(batch_number),
            )

            # Create the URL
            url: str = (
                f"{API_SCHEME}{self.base_url}"
                f"{API_PATH_REPORTS}"
                f"{merchant}"
                f"{report}"
            )

            # Perform a HEAD request on the report url
            response: requests.Response = self._head_request(url)  # noqa: WPS437

            # The report with the batch number exists
            if response.status_code == 200:  # noqa: WPS432
                self.logger.info(
                    f"Found settlement details report batch: {batch_number}",
                )

                # Yield the URL
                yield url

                # Increase batch number
                batch_number += 1

            # No report found, stop the loop
            elif response.status_code == 404:  # noqa: WPS432
                self.logger.debug(
                    f"Settlement details report batch: {batch_number} not "
                    "found, stopping.",
                )
                break

            # Unexpected HTTP response
            else:
                self.logger.critical(
                    f"Unexpected HTTP status code while checking: {url}. ",
                    f"({response.status_code})",
                )
                response.raise_for_status()

        self.logger.info("Finished retrieving Settlement Details Reports")

    def retrieve_csv(
        self,
        csv_url: str,
        cleaner: Optional[Callable],
    ) -> Generator[dict, None, None]:
        """Download the csv.

        Arguments:
            csv_url {str} -- The URL that points to the correct CSV file
            cleaner {Optional[Callable]} -- Optional cleaner function

        Yields:
            Generator[dict] -- Yields Adyen csvs
        """
        self.logger.info(f"Downloading report: {csv_url}")

        # Get Request to get the csv in binary format

        response: requests.Response = self.client.get(  # noqa: WPS437
            csv_url,
            auth=(self.report_user, self.user_password),
            headers=dict(HEADERS),
        )

        # If the status is not 200 raise the status
        if response.status_code != 200:  # noqa: WPS432
            self.logger.critical(
                f"Unexpected HTTP status code while downloading: {csv_url}. "
                f"({response.status_code})",
            )
            response.raise_for_status()

        # Read the csv
        csv: DictReader = DictReader(response.text.splitlines(), delimiter=",")

        # Clean every row in the csv
        if cleaner:
            yield from (
                cleaner(row, row_number, csv_url) for row_number, row in enumerate(csv)
            )

        # Return every row in the csv
        else:
            yield from (row for row in csv)

    def _head_request(
        self,
        url: str,
    ) -> requests.Response:  # noqa: WPS437
        """Perform a HEAD request.

        Arguments:
            url {str} -- Input url

        Returns:
            requests.Response -- Response of HEAD request
        """
        return self.client.head(
            url,
            auth=(self.report_user, self.user_password),
            headers=dict(HEADERS),
        )
