import unittest
from tap_adyen.cleaners import clean_row, clean_dispute_transaction_details,clean_payment_accounting

class TestCleaners(unittest.TestCase):
    def test_clean_row_with_missing_columns(self):
        row = {"existing_column": "1"}
        mappers = {
            "missing_column": {"type": int, "None": True},
            "existing_column": {"type": int, "None": True},
        }

        cleaned_row = clean_row(row, mappers)

        self.assertEqual(cleaned_row.get("existing_column"), 1)
        self.assertEqual(cleaned_row.get("missing_column"), None)
    
    def test_cleaners_leap_year_date_parse(self):
        dispute_row = {
            'Record Date' : "2024-01-01",
            'Payment Date' : "2024-01-01",
            'Dispute Date' : "2024-01-01",
            'Dispute End Date' : "2024-01-01",
            }
        payment_row = {
            'Booking Date' : "2024-01-01"
        }
        row_number = 1
        leap_year_dispute_csv_url = "https://dummy-url.adyen.com/reports/download/MerchantAccount/DummyMerchant/dispute_report_2024_02_29.csv"
        leap_year_payment_csv_url = "https://dummy-url.adyen.com/reports/download/MerchantAccount/DummyMerchant/payments_account_report_2024_02_29.csv"
        normal_dispute_csv_url = "https://dummy-url.adyen.com/reports/download/MerchantAccount/DummyMerchant/dispute_report_2024_06_15.csv"
        normal_payment_csv_url = "https://dummy-url.adyen.com/reports/download/MerchantAccount/DummyMerchant/payments_account_report_2024_06_15.csv"
        cleaned_leap_year_dispute_row = clean_dispute_transaction_details(dispute_row,row_number,leap_year_dispute_csv_url)
        cleaned_leap_year_payment_row = clean_payment_accounting(payment_row,row_number,leap_year_payment_csv_url)
        cleaned_normal_year_dispute_row = clean_dispute_transaction_details(dispute_row,row_number,normal_dispute_csv_url)
        cleaned_normal_year_payment_row = clean_payment_accounting(payment_row,row_number,normal_payment_csv_url)
        self.assertEqual(cleaned_leap_year_dispute_row.get("id"),202402290000000001)      
        self.assertEqual(cleaned_leap_year_payment_row.get("id"),202402290000000001)
        self.assertEqual(cleaned_normal_year_dispute_row.get("id"),202406150000000001)
        self.assertEqual(cleaned_normal_year_payment_row.get("id"),202406150000000001)
        
if __name__ == "__main__":
    unittest.main()
