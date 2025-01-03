from typing import List, Dict, Union
from PyPDF2 import PdfReader
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import yaml
import etl_utils as eu

def configure_page():
    st.set_page_config(
        page_title="Bank of America Financial Insights App",
        layout="wide",
        initial_sidebar_state="expanded"
        )
    hide_decoration_bar_style = '''
    <style>
    header {visibility: hidden;}
    </style>
    '''
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

def map_selected_page(selected_page:str):
    page_map = {
        "Configure Data Intake": "render_data_intake",
        "Customize Transaction Vendor and Expense Category":"render_customize_vendor_expense",
        "Monthly Spending Report":"render_mothly",
        "Quarterly Spending Report": "render_quarterly"
        }
    return page_map[selected_page]

def create_sidebar():
    page_options = [
        "Configure Data Intake",
        "Customize Transaction Vendor and Expense Category",
        "Monthly Spending Report",
        "Quarterly Spending Report",
    ]
    
    with st.sidebar:
        selected_page = option_menu(
            menu_title="Choose which insights you'd like to view.",
            options=page_options,
            menu_icon="currency-dollar",
            icons=["arrow-return-right"]*len(page_options),
            default_index=0,
        )
        selected_page = map_selected_page(selected_page)
        st.session_state["selected_page"] = selected_page

def assign_vec(statements_df:pd.DataFrame):
    try:
        yaml_uploadedfile_obj = st.session_state["vec_config"]
        yaml_file_dict = yaml.safe_load(yaml_uploadedfile_obj.read())
    except (KeyError, AttributeError) as ke_ae:
        st.warning("No yaml vendor name and expense category configuration file was uploaded. If this is correct, ignore this warning.")
        return statements_df
    
    # must store dictionary object into session_state. streamlit UploadedFile object cannot be kep in session state 
    vec_config_dict_key = [*yaml_file_dict.keys()][0]
    st.session_state["vec_config_dict_key"] = vec_config_dict_key
    st.session_state["vec_config_dict"] = yaml_file_dict
    yaml_file_list = yaml_file_dict[vec_config_dict_key]

    for i, rule_dict in enumerate(yaml_file_list):
        description = rule_dict["description"]
        vendor = rule_dict["vendor"]
        expense_category = rule_dict["expense_category"]
        exact_match = rule_dict["exact_match"]
        columns_to_change = ["Vendor_Name", "Expense_Category", "Rule_Applied_str", "Rule_Applied_bool"]
        if exact_match:
            condition = (statements_df["Description"]==description)
            statements_df.loc[condition, columns_to_change] = [vendor, expense_category, str(yaml_file_list[i]), True]
        else:
            condition = ((statements_df["Description"].str.strip().str.contains(description, case=rule_dict["case_sensitive"], regex=rule_dict["is_regex"])) & (statements_df["Rule_Applied_bool"]==False))
            statements_df.loc[condition, columns_to_change] = [vendor, expense_category, str(yaml_file_list[i]), True]
    return statements_df

def process_files():
    statements_list = []
    if "e_statements" in st.session_state:
        file_list = st.session_state.e_statements
        if file_list:
            for file in file_list:
                # Extract text from PDF
                reader = PdfReader(file)
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += page.extract_text()
                statement_df = eu.get_statement_df(pdf_text)
                statements_list.append(statement_df)
        else:
            # will be entered in file_list = []
            st.error("No files uploaded.")
    else:
        st.markdown("e_statements does not exist as accessible variable in session state")
    try:
        all_statements_df = pd.concat(objs=statements_list, ignore_index=True)
        all_statements_df = all_statements_df[["Transaction_Date", "Transaction_Type", "Description", "Amount"]].reset_index(drop=True)
        all_statements_df["Vendor_Name"] = ""
        all_statements_df["Expense_Category"] = ""
        all_statements_df["Rule_Applied_str"] = ""
        all_statements_df["Rule_Applied_bool"] = False
        all_statements_df = assign_vec(all_statements_df)
        st.session_state["statements_df"] = all_statements_df
        st.success("Processed files successfully. Navigate to the customization of vendor name and expense categories.")
    except ValueError as ve:
        pass

def render_data_intake():
    st.file_uploader(
        "Select the e-statements from your local computer storage that you would like to analyze.",
        type=["pdf"],
        accept_multiple_files=True,
        key="e_statements"
    )
    st.file_uploader(
        "Select the vendor name and expense category configuration file from local computer storage. This is optional. If you do not have one, after uploading e-statements, navigate to the 'Customize Transaction Vendor and Expense Category' page. Fill out vendor and expense category information based on the transaction description. Click 'Apply Changes', and a YAML file will be output. Use this YAML file to maintain rules for future uses. New rules persist for the session of the app, however, are cleared, once the page refreshes.",
        type=["yaml"],
        accept_multiple_files=False,
        key="vec_config"
    )
    st.button(label="Process Files", on_click=process_files)

def get_vec_changes(df:pd.DataFrame, edited_df:pd.DataFrame):
    has_vec_condition = (df["Vendor_Name"]!="") & (df["Expense_Category"]!="")
    df_w_vec = df[has_vec_condition]

    edited_has_vec_condition = (edited_df["Vendor_Name"]!="") & (edited_df["Expense_Category"]!="")
    edited_df_w_vec = edited_df[edited_has_vec_condition]

    rules_created_indices = st.session_state["rules_created_indices"]

    if len(df_w_vec)==len(edited_df_w_vec):
        change_indices = []
    else:
        change_indices = [index for index in edited_df_w_vec.index if not (index in df_w_vec.index) and not (index in rules_created_indices)]
        rules_created_indices.extend(change_indices)
        st.session_state["rules_created_indices"] = rules_created_indices
    return change_indices

def add_new_rules(yaml_file_dict:Dict[str, List[Dict[str, Union[str, bool]]]], edited_dvec_df:pd.DataFrame):
    if yaml_file_dict:
        vec_config_dict_key = st.session_state["vec_config_dict_key"]
    else:
        vec_config_dict_key = "vec_items"
        yaml_file_dict = {vec_config_dict_key:[]}

    for i, row in edited_dvec_df.iterrows():
        description = row["Description"]
        vn = row["Vendor_Name"]
        ec = row["Expense_Category"]
        rule_dict = {"description":description, "vendor":vn, "expense_category":ec, "exact_match":True}
        yaml_file_dict[vec_config_dict_key].append(rule_dict)
    yaml_file_str = yaml.dump(yaml_file_dict)
    return yaml_file_str

def render_customize_vendor_expense():
    df = st.session_state["statements_df"]
    st.markdown("""Assign vendors and expense categories to transaction descriptions. A transaction description must have both a Vendor and Expense_Category assigned. Once done, press the "Apply Changes" button below. An updated YAML file containing current and added rules will be available for download.""")
    description_list = []
    dvec_data_list = []
    for i in range(0, len(df)):
        description = df["Description"][i]
        if not (description in description_list):
            description_list.append(description)
            data = {"Description": description, "Vendor_Name": df["Vendor_Name"][i], "Expense_Category": df["Expense_Category"][i]}
            dvec_data_list.append(data)

    dvec_df = pd.DataFrame(dvec_data_list).sort_values(by=["Description", "Vendor_Name", "Expense_Category"], ascending=[True, True, True])
    
    edited_dvec_df = st.data_editor(data=dvec_df, use_container_width=True, hide_index=True)
    if st.button("Apply Changes"):
        changed_list = get_vec_changes(dvec_df, edited_dvec_df)
        if changed_list:
            statements_df_w_new_rules = pd.merge(left=st.session_state["statements_df"], right=edited_dvec_df, on=["Description"], how="inner", suffixes=["_original", "_edited"])
            statements_df = statements_df_w_new_rules[["Transaction_Date", "Transaction_Type", "Description", "Vendor_Name_edited", "Expense_Category_edited", "Amount"]]
            statements_df = statements_df.rename({"Vendor_Name_edited":"Vendor_Name", "Expense_Category_edited":"Expense_Category"}, axis=1)
            st.session_state["statements_df"] = statements_df
            try:
                try:
                    yaml_file_dict = st.session_state["vec_config_dict"]
                except KeyError as ke:
                    yaml_file_dict = {}
                yaml_file_str = add_new_rules(yaml_file_dict, edited_dvec_df.loc[changed_list, :])
                st.download_button(label="Download the available yaml file containing Vendor and Expense Category assignment configuration information. Use this new file in the future to maintain your iterative changes.", data=yaml_file_str, file_name="vendor_expense_category_config.yaml", icon=":material/download_for_offline:", use_container_width=True)
            except Exception as e:
                st.markdown(str(st.session_state))
                st.markdown(f"ERROR TYPE: {type(e)} ERROR {e}")
        else:
            st.warning("No changes were applied to the dataframe, so no new rules have been created.")
    
def render_filter_df_section(df:pd.DataFrame, key_info:tuple):
    td_y, td_mq = map(int, key_info)
    col1, col2 = st.columns(2)

    with col1:
        min_td = df["Transaction_Date"].min().to_pydatetime().date()
        max_td = df["Transaction_Date"].max().to_pydatetime().date()
        min_td_bound, max_td_bound = st.slider(label="For what date range would you like to see data?", min_value=min_td, max_value=max_td, value=(min_td, max_td), key=f"slider_{td_y}_{td_mq}_0")
    
    with col2:
        min_amount = df["Amount"].min()
        max_amount = df["Amount"].max()
        min_amount_bound, max_amount_bound = st.slider(label="For what $ amount range would you like to see data?", min_value=min_amount, max_value=max_amount, value=(min_amount, max_amount), key=f"slider_{td_y}_{td_mq}_1")

    col1, col2 = st.columns(2)
    with col1:
        vendor_list = df["Vendor_Name"].unique()
        selected_vendors_list = st.multiselect(label="Which vendor's transaction would you like to see?", options=vendor_list, default=vendor_list, key=f"multiselect_{td_y}_{td_mq}_0")
    
    with col2:
        expense_category_list = df["Expense_Category"].unique()
        selected_expense_categories_list = st.multiselect(label="Which expense category transactions would you like to see?", options=expense_category_list, default=expense_category_list, key=f"multiselect_{td_y}_{td_mq}_1")

    filtered_df = df.copy(deep=True).drop(labels=["Transaction_Type"], axis=1)

    if min_td_bound and max_td_bound:
        filtered_df = filtered_df[(filtered_df["Transaction_Date"].dt.date>=min_td_bound) & (filtered_df["Transaction_Date"].dt.date<=max_td_bound)]
    if min_amount_bound and max_amount_bound:
        filtered_df = filtered_df[(filtered_df["Amount"]>=min_amount_bound) & (filtered_df["Amount"]<=max_amount_bound)]
    if selected_vendors_list:
        filtered_df = filtered_df[filtered_df["Vendor_Name"].isin(selected_vendors_list)]
    if selected_expense_categories_list:
        filtered_df = filtered_df[filtered_df["Expense_Category"].isin(selected_expense_categories_list)]
    
    # highlight outliers by amount
    sorted_df = filtered_df.sort_values(by=["Transaction_Date", "Description", "Vendor_Name", "Expense_Category", "Amount"], ascending=[True, True, True, True, False])
    sorted_df = sorted_df.rename({"Transaction_Date":"Transaction Date", "Vendor_Name":"Vendor Name", "Expense_Category": "Expense Category"}, axis=1)
    column_config = {
        "Transaction Date":st.column_config.DateColumn("Transaction Date", format="YYYY-MM-DD"),
        "Amount":st.column_config.NumberColumn("Amount", format="$ %.2f")
        }
    st.dataframe(sorted_df[["Transaction Date", "Description", "Amount", "Vendor Name", "Expense Category"]], use_container_width=True, hide_index=True, selection_mode=["multi-row", "multi-column"], column_config=column_config)

def render_top_N_t(df:pd.DataFrame, n:int):
    """Display the top N transaction descriptions by amount."""
    sorted_df = df.sort_values(by=["Amount"], ascending=False).reset_index(drop=True)
    top_n_df = sorted_df.iloc[0:n, :]
    num_columns = min(n, len(df))
    column_list = st.columns(num_columns)
    for i, column in enumerate(column_list):
        with column:
            description = top_n_df["Description"][i]
            amount = top_n_df["Amount"][i]
            st.markdown(f"### **Description {i+1}**")
            st.write(f"**Description Name:** {description}")
            st.write(f"**Total Amount:** ${amount:,.2f}")

def render_top_N_v(df:pd.DataFrame, n:int):
    """Display the top N vendors based on the total transaction amount."""
    grouped_df = df[["Vendor_Name", "Expense_Category", "Amount"]].groupby(by=["Vendor_Name", "Expense_Category"]).sum()
    sorted_df = grouped_df.sort_values(by=["Amount"], ascending=False).reset_index()
    top_n_df = sorted_df.iloc[0:n, :].reset_index()
    num_columns = min(n, len(grouped_df))
    column_list = st.columns(num_columns)
    for i, column in enumerate(column_list):
        with column:
            vendor_name = top_n_df["Vendor_Name"][i]
            expense_category = top_n_df["Expense_Category"][i]
            amount = top_n_df["Amount"][i]
            st.markdown(f"### **Vendor {i+1}**")
            st.write(f"**Vendor Name:** {vendor_name}")
            st.write(f"**Expense Category:** {expense_category}")
            st.write(f"**Total Amount:** ${amount:,.2f}")

def render_top_N_ec(df:pd.DataFrame, n:int):
    """Display the top N expense categories based on the total transaction amount."""
    grouped_df = df[["Expense_Category", "Amount"]].groupby(by=["Expense_Category"]).sum()
    sorted_df = grouped_df.sort_values(by=["Amount"], ascending=False).reset_index()
    top_n_df = sorted_df.iloc[0:n, :]
    num_columns = min(n, len(grouped_df))
    column_list = st.columns(num_columns)
    for i, column in enumerate(column_list):
        with column:
            expense_category = top_n_df["Expense_Category"][i]
            amount = top_n_df["Amount"][i]
            st.markdown(f"### **Category {i+1}**")
            st.write(f"**Expense Category:** {expense_category}")
            st.write(f"**Total Amount:** ${amount:,.2f}")

def render_insights(df:pd.DataFrame):
    try:
        year = [*df["Transaction_Date"].dt.year][0]
        month = [*df["Transaction_Date"].dt.month][0]
        # total spent
        col1, col2, col3, col4 = st.columns(4)
        num_records_options = [1, 3, 5, 10]

        with col1:
            total_spent = sum(df["Amount"])
            st.markdown("Total amount of money spent")
            st.markdown(total_spent)
        with col2:
            key_str = str(year) + "/" + str(month) + "/1"
            t_n = st.selectbox(label="How many top transaction insights would you like to see?", options=num_records_options, key=(key_str), index=1)
        with col3:
            key_str = str(year) + "/" + str(month) + "/2"
            v_n = st.selectbox(label="How many top vendor insights would you like to see?", options=num_records_options, key=(key_str), index=1)
        with col4:
            key_str = str(year) + "/" + str(month) + "/3"
            ec_n =st.selectbox(label="How many top expense category insights would you like to see?", options=num_records_options, key=(key_str), index=1)
        
        # top three individual transactions
        render_top_N_t(df, t_n)
        # top three vendors
        render_top_N_v(df, v_n)
        # top three expense categories
        render_top_N_ec(df, ec_n)
        # filterable dataframe
        render_filter_df_section(df, (year, month))
    except Exception as e:
        exception_str = f"ERROR TYPE: {type(e)} ERROR STR: {e}"
        st.markdown(exception_str)
        st.dataframe(df)

def get_year_month_combos(df:pd.DataFrame):
    ym_list = []
    for i in range(0, len(df)):
        try:
            ymd_value = df["Transaction_Date"][i]
            mv = str(ymd_value.month)
            yv = str(ymd_value.year)
            ym_value = yv + "/" + (mv if len(mv)==2 else "0" + mv)
            if not (ym_value in ym_list):
                ym_list.append(ym_value)
        except Exception as e:
            st.markdown(f"FUNCTION: get_year_month_combos ERROR TYPE{type(e)} ERRRO STR: {e} VALUE: {ymd_value}")
    return sorted(ym_list)

def render_monthly():
    df = st.session_state["statements_df"]
    df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'], errors='coerce')
    tabs_list = get_year_month_combos(df) 
    tab_objects = st.tabs(tabs_list)
    for tab, year_month in zip(tab_objects, tabs_list):
        with tab:
            # Extract year and month from the tab's label
            yv, mv = map(int, year_month.split("/"))
            debit_condition = (df["Transaction_Type"]=="Debit")
            year_condition = (df['Transaction_Date'].dt.year==yv)
            month_condition = (df['Transaction_Date'].dt.month==mv)
            all_conditions = debit_condition & year_condition & month_condition
            # Filter df based on year and month
            job_df = df[all_conditions]
            render_insights(job_df)

def get_year_quarter_combos(df:pd.DataFrame):
    yq_list = []
    for i in range(0, len(df)):
        ymd_value = df["Transaction_Date"][i]
        qv = str(ymd_value.quarter)
        yv = str(ymd_value.year)
        yq_value = yv + "/" + (qv if len(qv)==2 else "0" + qv)
        if not (yq_value in yq_list):
            yq_list.append(yq_value)
    return sorted(yq_list)

def render_quarterly():
    df = st.session_state["statements_df"]
    tabs_list = get_year_quarter_combos(df) 
    tab_objects = st.tabs(tabs_list)
    for tab, year_quarter in zip(tab_objects, tabs_list):
        with tab:
            # Extract year and month from the tab's label
            yv, qr = map(int, year_quarter.split("/"))
            debit_condition = (df["Transaction_Type"]=="Debit")
            year_condition = (df['Transaction_Date'].dt.year == yv)
            month_condition = (df['Transaction_Date'].dt.quarter == qr)
            all_conditions = debit_condition & year_condition & month_condition
            # Filter df based on year and month
            job_df = df[all_conditions]
            render_insights(job_df)

def page_handler():
    selected_page = st.session_state["selected_page"]

    if not ("rules_created_indices" in st.session_state):
        st.session_state["rules_created_indices"] = []
    try:
        if selected_page=="render_data_intake":
            render_data_intake()
        elif selected_page=="render_customize_vendor_expense":
            render_customize_vendor_expense()
        elif selected_page=="render_mothly":
            render_monthly()
        elif selected_page=="render_quarterly":
            render_quarterly()
    except KeyError as ke:
        st.error("Did you upload financial statements? If not, navigate to page 'Configure Date Intake' to upload your e-statements and your vendor/expense category mappings.")