# standard library
import os
import re
from typing import List, Union
# suplementary packages
import pandas as pd
import PyPDF2
from datetime import datetime
from streamlit import markdown
# custom module(s)
import constants as c

def validate_input(pdf_path:str):
    if type(pdf_path)!=str:
        raise ValueError("pdf_path must be of type str. Example '/Directory/file.pdf'")

def extract_pdf_text(pdf_path:str):
    validate_input(pdf_path) # raises TypeError for invalid args
    pdf_reader = PyPDF2.PdfReader(pdf_path) # Raises a FileNotFoundError if invalid file path
    pdf_length = len(pdf_reader.pages)
    pdf_text = ""
    for i in range(0, pdf_length):
        page_text = pdf_reader.pages[i].extract_text()
        pdf_text = pdf_text + page_text
    return pdf_text

def validate_transaction_str(transaction_str:str):
    invalid_str_list = ["Page", "page", "Continue", "continue", "Number", "Amount", "Total", "Purchases", "Adjustments"]
    for invalid_str in invalid_str_list:
        if invalid_str in transaction_str:
            return False
    return True

def unpack_interest(transaction_list:List[Union[str, float]]):
        transaction_date, posting_date = transaction_list[0:2]
        description = " ".join(transaction_list[2:-1])
        amount = transaction_list[-1]
        transaction_data = [transaction_date, posting_date, description, None, None, amount]
        return transaction_data

def unpack_credit_debit(transaction_list:List[Union[str, float]]):
        transaction_date, posting_date = transaction_list[0:2]
        description = " ".join(transaction_list[2:-3])
        reference_number, account_number, amount = transaction_list[-3:]
        transaction_data = [transaction_date, posting_date, description, reference_number, account_number, amount]
        return transaction_data

def unpack_transaction(transaction_str:str, transaction_type:str):
    try:
        is_valid_str = validate_transaction_str(transaction_str)
        transaction_list = transaction_str.split()
        if transaction_type=="Interest" and is_valid_str:
            transaction_data = unpack_interest(transaction_list)
        elif ((transaction_type=="Credit") or (transaction_type=="Debit")) and is_valid_str:
            # credit/debit transactions are mapped to a reference and account number
            transaction_data = unpack_credit_debit(transaction_list)
        else:
            transaction_data = [None]*6    
    except Exception as e:
        transaction_data = [None]*6
        error_str = f"ERROR TYPE: {type(e)}ERROR STR: {e}"
        print(error_str)
    return transaction_data

def find_match_index(transactions_list:List[str], pattern:str):
    for i in range(0, len(transactions_list)):
        transaction_value = transactions_list[i]
        try:
            match_value = re.match(pattern=pattern, string=transaction_value)[0]
            break
        except TypeError as te:
            continue
    return i

def get_statement_year(pdf_text_list:List[str]):
    i = find_match_index(pdf_text_list, c.MONTH_GROUP_STR)
    statement_date_range_str = pdf_text_list[i]
    if ("December" in statement_date_range_str) and ("January" in statement_date_range_str):
        needs_mapping, statement_year = True, statement_date_range_str.split()[-1]
    else:
        needs_mapping, statement_year = False, statement_date_range_str.split()[-1]
    return needs_mapping, statement_year

def get_transaction_data(transactions_list:List[str], start_str:str, end_str:str, transaction_type:str):
    start = find_match_index(transactions_list, start_str) + 1
    end = find_match_index(transactions_list, end_str)
    transactions_list = transactions_list[start:end]
    for i in range(0, len(transactions_list)):
        transactions_list[i] = unpack_transaction(transactions_list[i], transaction_type)
    df = pd.DataFrame(data=transactions_list, columns=c.column_tuple)
    df = df.dropna(how="all", axis=0)
    df["Transaction_Type"] = transaction_type
    return df

def clean_statement(df:pd.DataFrame):
    df["Amount"] = df["Amount"].str.replace(",", "").str.strip()
    for i in range(0, len(df)):
        try:
            # clean transaction date column
            try:
                transaction_date = df["Transaction_Date"][i]
                year, month, day = map(int, transaction_date.split("/"))
                td_object = datetime(year=year, month=month, day=day)
            except Exception as e:
                td_object = None
            # clean amount of transaction for transactions with multiline descriptions
            try:
                amount = df["Amount"][i]
                amount = float(amount)
            except Exception as e:
                amount = df["Amount"][i+1]
                amount = float(amount)
        except Exception as e:
            st.markdown(f"FUNCTION: clean_statement ERROR TYPE{type(e)} ERRRO STR: {e}")
        df["Transaction_Date"][i] = td_object.date() if td_object else None
        df["Amount"][i] = amount
    df = df.dropna(subset=["Transaction_Date", "Description"], how="any", ignore_index=True)
    return df

def get_statement_df(pdf_text:str)->pd.DataFrame:
    pdf_text_list = pdf_text.split("\n")
    needs_mapping, statement_year = get_statement_year(pdf_text_list)
    credit_df = get_transaction_data(pdf_text_list, c.CREDITS_STR_START_PATTERN, c.CREDITS_STR_END_PATTERN, "Credit")
    debit_df = get_transaction_data(pdf_text_list, c.DEBITS_STR_START_PATTERN, c.DEBITS_STR_END_PATTERN, "Debit")
    interest_df = get_transaction_data(pdf_text_list, c.INTEREST_STR_START_PATTERN, c.INTEREST_STR_END_PATTERN, "Interest")
    statement_df = pd.concat(objs=[credit_df, debit_df, interest_df], ignore_index=True)
    statement_df["Year"] = statement_year
    if needs_mapping:
        # map December entries to the previous year
        bool_array = statement_df["Transaction_Date"].str.contains("12/")
        statement_df.loc[bool_array, "Year"] = str(int(statement_year) - 1)
    statement_df["Transaction_Date"] = statement_df["Year"] + "/" + statement_df["Transaction_Date"]
    statement_df = statement_df.drop(labels=["Year"], axis=1)
    statement_df = clean_statement(statement_df)
    return statement_df