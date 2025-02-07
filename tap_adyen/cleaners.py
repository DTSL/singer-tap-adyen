"""Cleaner functions."""
# -*- coding: utf-8 -*-

from datetime import date
from types import MappingProxyType
from typing import Any, Optional

from dateutil.parser import parse as parse_date

from tap_adyen.streams import STREAMS


class ConvertionError(ValueError):
    """Failed to convert value."""


def to_type_or_null(
    input_value: Any,
    data_type: Optional[Any] = None,
    nullable: bool = True,
) -> Optional[Any]:
    """Convert the input_value to the data_type.

    The input_value can be anything. This function attempts to convert the
    input_value to the data_type. The data_type can be a data type such as str,
    int or Decimal or it can be a function. If nullable is True, the value is
    converted to None in cases where the input_value == None. For example:
    a '' == None, {} == None and [] == None.

    Arguments:
        input_value {Any} -- Input value

    Keyword Arguments:
        data_type {Optional[Any]} -- Data type to convert to (default: {None})
        nullable {bool} -- Whether to convert empty to None (default: {True})

    Returns:
        Optional[Any] -- The converted value
    """
    # If the input_value is not equal to None and a data_type input exists
    if input_value and data_type:
        # Convert the input value to the data_type
        try:
            return data_type(input_value)
        except ValueError as err:
            raise ConvertionError(
                f'Could not convert {input_value} to {data_type}: {err}',
            )

    # If the input_value is equal to None and Nullable is True
    elif not input_value and nullable:
        # Convert '', {}, [] to None
        return None

    # If the input_value is equal to None, but nullable is False
    # Return the original value
    return input_value


def clean_row(row: dict, mapping: dict) -> dict:
    """Clean the row according to the mapping.

    The mapping is a dictionary with optional keys:
    - map: The name of the new key/column
    - type: A data type or function to apply to the value of the key
    - nullable: Whether to convert empty values, such as '', {} or [] to None

    Arguments:
        row {dict} -- Input row
        mapping {dict} -- Input mapping

    Returns:
        dict -- Cleaned row
    """
    cleaned: dict = {}

    key: str
    key_mapping: dict

    # For every key and value in the mapping
    for key, key_mapping in mapping.items():

        # Retrieve the new mapping or use the original
        new_mapping: str = key_mapping.get('map') or key

        # Convert the value
        cleaned[new_mapping] = to_type_or_null(
            row.get(key),
            key_mapping.get('type'),
            key_mapping.get('null', True),
        )

    return cleaned


def clean_dispute_transaction_details(
    row: dict,
    row_number: int,
    csv_url: str,
) -> dict:
    """Clean dispute transaction details.

    Arguments:
        row {dict} -- Input row
        row_number {int} -- Row number, used to construct primary key
        file_date {str} -- File name, used to construct primary key

    Returns:
        dict -- Cleaned row
    """
    # Get the mapping from the STREAMS
    mapping: Optional[dict] = STREAMS['dispute_transaction_details'].get(
        'mapping',
    )

    # Get file date
    file_date: date = parse_date(
        csv_url.replace("_","-") # Can't parse leap year days (Feb 29th) with underscores, but can with dashes
        ,fuzzy=True
    ).date()

    # Create primary key
    date_string: str = '{date:%Y%m%d}'.format(date=file_date)  # noqa: WPS323
    number: str = str(row_number).rjust(10, '0')
    row['id'] = int(date_string + number)

    # Add timezone to the date, so that the datetime parser includes it
    row['Record Date'] = '{record_date} {record_date_timezone}'.format(
        record_date=row.get('Record Date', ''),
        record_date_timezone=row.get('Record Date TimeZone', ''),
    )
    row['Payment Date'] = '{payment_date} {payment_date_timezone}'.format(
        payment_date=row.get('Payment Date', ''),
        payment_date_timezone=row.get('Payment Date TimeZone', ''),
    )
    row['Dispute Date'] = '{dispute_date} {dispute_date_timezone}'.format(
        dispute_date=row.get('Dispute Date', ''),
        dispute_date_timezone=row.get('Dispute Date TimeZone', ''),
    )
    row['Dispute End Date'] = (
        '{dispute_end_date} {dispute_end_date_timezone}'.format(
            dispute_end_date=row.get('Dispute End Date', ''),
            dispute_end_date_timezone=row.get('Dispute End Date TimeZone', ''),
        )
    )

    # If a mapping has been defined in STREAMS, apply it
    if mapping:
        return clean_row(row, mapping)

    # Else return the original row
    return row


def clean_payment_accounting(
    row: dict,
    row_number: int,
    csv_url: str,
) -> dict:
    """Clean payment accounting.

    Arguments:
        row {dict} -- Input row
        row_number {int} -- Row number, used to construct primary key
        csv_url {str} -- File name, used to construct primary key

    Returns:
        dict -- Cleaned row
    """
    # Get the mapping from the STREAMS
    mapping: Optional[dict] = STREAMS['payment_accounting'].get('mapping')

    # Get file date
    file_date: date = parse_date(
        csv_url.replace("_","-"), # Can't parse leap year days (Feb 29th) with underscores, but can with dashes
        fuzzy=True
    ).date()

    # Create primary key
    date_string: str = '{date:%Y%m%d}'.format(date=file_date)  # noqa: WPS323
    number: str = str(row_number).rjust(10, '0')
    row['id'] = int(date_string + number)

    # Add timezone to the date, so that the datetime parser includes it
    row['Booking Date'] = '{booking_date} {timezone}'.format(
        booking_date=row.get('Booking Date', ''),
        timezone=row.get('TimeZone', ''),
    )

    # If a mapping has been defined in STREAMS, apply it
    if mapping:
        return clean_row(row, mapping)

    # Else return the original row
    return row


def clean_settlement_details(
    row: dict,
    row_number: int,
    _: str,
) -> dict:
    """Clean settlement details.

    Arguments:
        row {dict} -- Input row
        row_number {int} -- Row number, used to construct primary key

    Returns:
        dict -- Cleaned row
    """
    # Get the mapping from the STREAMS
    mapping: Optional[dict] = STREAMS['settlement_details'].get('mapping')

    # Create primary key
    number: str = str(row_number).rjust(10, '0')
    row['id'] = int(row['Batch Number'] + number)

    # Add timezone to the date, so that the datetime parser includes it
    row['Creation Date'] = '{creation_date} {timezone}'.format(
        creation_date=row.get('Creation Date', ''),
        timezone=row.get('TimeZone', ''),
    )

    # If a mapping has been defined in STREAMS, apply it
    if mapping:
        return clean_row(row, mapping)

    # Else return the original row
    return row


# Collect all cleaners
CLEANERS: MappingProxyType = MappingProxyType({
    'dispute_transaction_details': clean_dispute_transaction_details,
    'payment_accounting': clean_payment_accounting,
    'settlement_details': clean_settlement_details,
})
