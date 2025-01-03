**Bank of America - Credit Card Spending App**

- Brief app description  
  * This is a front-end ETL app for financial insights. This app intakes PDF e-statements and performs various functions. It offers the ability to gain insight into spending habits and teh ability to customize vendor names and expense categories based on user input/transaction details.  
- Core Features  
  * Upload PDF e-statements from customer Bank of America credit card statement portal  
  * Upload YAML configuration file for vendor names and expense categories  
  * Customize vendor names and expense categories assigned to each transaction  
    * Such changes persist for the life of the app session  
  * Download changes to vendor name and expense category for each edited transactions in a YAML configuration file  
  * View top insights for transaction name, vendor, and expense category (1, 3, 5, or 10 records)  
  * View and filter e-statements at the monthly/quarterly level to view transactions

---

**Project Justification**

- Why did I create this project?
  * I created this project primarily for myself. I wanted the ability to view my credit card e-statements immediately in a digestible format, without giving my personal financial information to a different third party entity.  
- Who is this project for?
  * This project was made for those of low or greater technical background who use Bank of America credit cards and would like to view their spending habits without providing information to a third party organization.

---

**Project Setup**

- Prerequisites
  * Python3.12
  * non standard libraries in requirements.txt
- Steps
  * git clone <repo_url>
  * cd <repo_folder>
  * pip install -r requirements.txt
  * streamlit run ./app/app_main.py
  * app opens locally on default browser

---

**Description of Each Page**
- Configure Data Intake  
  * Intake credit card e-statements  
  * Intake YAML configuration information for transactions  
- Customize Transaction Vendor and Expense Category  
  * Allow user to map a transaction string to a vendor and expense category  
  * Allow user to download a YAML with current rules and added rules, to be used on the next use of the app  
- Monthly Spending Report  
  * Show user top one to top ten transactions, vendors, and expense categories by amount spent  
  * Show user all transactions for that year-month  
- Quarterly Spending Report  
  * Show user top one to top ten transactions, vendors, and expense categories by amount spent  
  * Show user all transactions for that year-quarter

---
**Ideal Use**

1. Page: Configure Data Intake
- Upload PDF e-statements (required)
- Upload YAML configuration file for vendor name and expense categories (optional)
2. Page: Customize Transaction Vendor and Expense Category
- Assign a vendor name and an expense category to each unlabeled transaction (optional, reccomended if no YAML configuration file is uploaded on Page: Configure Data Intake)
  * use the downloaded YAML file in future app runs to keep transaction mapping information
- Click "Apply Changes" button
- Download the new YAML file by clicking the download widget
3. Page: Monthly Spending Report/Quarterly Spending Report
- Scroll through time tabs (optional)
- Change the number of transaction, vendor, or expense category insights (optional; min 1; max 10)
- Filter the transaction date range (optional)
- Filter the amount range (optional)
- Filter which vendors' transactions appear (optional)
- Filter which expense categories appear (optional)