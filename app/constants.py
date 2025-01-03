# regex explanations
# () grouping a pattern
# | signifies a logical OR condition between the strings
# \d digit character
# + one or more occurences
# ?! negation of pattern
# \s whitespace
# ? zero or one occurences
# must escape $, as it means to end a pattern at end of a character string or line

MONTH_GROUP_STR = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
STATEMENT_DATE_PATTERN = rf"{MONTH_GROUP_STR}\s+\d+\s+-\s{MONTH_GROUP_STR}\s+\d+,\s+\d{4}"

CREDITS_STR_START_PATTERN = r"(Page \d+ of \d+)?Payments and Other Credits(?!\s+-?\$\d+)"
CREDITS_STR_END_PATTERN = r"TOTAL PAYMENTS AND OTHER CREDITS FOR THIS PERIOD\s+-?\$\d+"

DEBITS_STR_START_PATTERN = r"(Page \d+ of \d+)?Purchases and Adjustments(?!\s+-?\$\d+)"
DEBITS_STR_END_PATTERN = r"TOTAL PURCHASES AND ADJUSTMENTS FOR THIS PERIOD\s+-?\$\d+"

INTEREST_STR_START_PATTERN = r"(Page \d+ of \d+)?Interest Charged(?!\s+-?\$\d+)"
INTEREST_STR_END_PATTERN = r"TOTAL INTEREST CHARGED FOR THIS PERIOD\s+-?\$\d+"

column_tuple = ("Transaction_Date", "Posting_Date", "Description", "Reference_Number", "Account_Number", "Amount")
