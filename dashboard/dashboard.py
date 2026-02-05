import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import os

# Load database URL from environment variable directly
DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    st.error("Database URL is not set. Please check your Docker environment settings.")

@st.cache_data
def load_data():
    """
    Connects to the PostgreSQL database and reads each table into a DataFrame.
    """
    engine = create_engine(DB_URL)
    
    # Load data from PostgreSQL
    clubs = pd.read_sql("SELECT * FROM club", con=engine)
    staff = pd.read_sql("SELECT * FROM staff", con=engine)
    leads = pd.read_sql("SELECT * FROM lead", con=engine)
    members = pd.read_sql("SELECT * FROM member", con=engine)
    subscriptions = pd.read_sql("SELECT * FROM subscription", con=engine)
    
    # Convert date columns to datetime (if they exist)
    date_columns = {
        "leads": ["creation_date", "conversion_date"],
        "staff": ["hired_date"],
        "members": ["join_date"],
        "subscriptions": ["start_date", "end_date"]
    }

    for table_name, cols in date_columns.items():
        df = locals()[table_name]
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
    
    return leads, staff, clubs, members, subscriptions

def main():
    st.set_page_config(page_title="Gym Manager Dashboard", layout="wide")
    st.title("Gym Lead Conversion & Staff Performance Dashboard")
    
    # Load data from PostgreSQL
    leads, staff, clubs, members, subscriptions = load_data()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    if not leads.empty:
        date_min = leads['creation_date'].min().date()
        date_max = leads['creation_date'].max().date()
        created_range = st.sidebar.date_input("Lead Creation Date Range", [date_min, date_max])
    else:
        created_range = [None, None]
    
    club_options = clubs['name'].unique().tolist() if not clubs.empty else []
    selected_clubs = st.sidebar.multiselect("Select Club(s)", club_options, default=club_options)
    
    staff_options = staff['name'].unique().tolist() if not staff.empty else []
    selected_staff = st.sidebar.multiselect("Select Staff Member(s)", staff_options, default=staff_options)
    
    # Apply filters (only if data exists)
    if not leads.empty:
        club_ids = clubs[clubs['name'].isin(selected_clubs)]['club_id'] if not clubs.empty else []
        staff_ids = staff[staff['name'].isin(selected_staff)]['staff_id'] if not staff.empty else []
        mask = (
            (leads['creation_date'].dt.date >= created_range[0]) &
            (leads['creation_date'].dt.date <= created_range[1]) &
            (leads['club_id'].isin(club_ids)) &
            (leads['staff_id'].isin(staff_ids))
        )
        filtered_leads = leads[mask]
    else:
        filtered_leads = pd.DataFrame()

    # Display Filtered Data (Interactive Tables)
    st.header("Clubs")
    st.dataframe(clubs)

    st.header("Staff")
    st.dataframe(staff)

    st.header("Leads")
    st.dataframe(filtered_leads if not filtered_leads.empty else leads)

    st.header("Members")
    st.dataframe(members)

    st.header("Subscriptions")
    st.dataframe(subscriptions)
    
    # Display Key Performance Indicators (KPIs)
    st.header("Key Metrics")
    total_leads = len(filtered_leads) if not filtered_leads.empty else len(leads)
    converted_leads = filtered_leads['converted_to_member'].sum() if 'converted_to_member' in filtered_leads.columns else 0
    conversion_rate = (converted_leads / total_leads) if total_leads > 0 else 0
    
    st.metric("Total Leads", total_leads)
    st.metric("Converted Leads", converted_leads)
    st.metric("Conversion Rate", f"{conversion_rate:.1%}")

    # Visualize Leads by Source
    st.header("Leads by Source")
    if not filtered_leads.empty:
        source_count = filtered_leads['source'].value_counts().reset_index()
        source_count.columns = ['Source', 'Count']
        st.bar_chart(source_count.set_index('Source'))

    # Visualize Staff Performance
    st.header("Staff Performance")
    if not filtered_leads.empty:
        staff_performance = (
            filtered_leads.groupby('staff_id')['converted_to_member']
            .sum()
            .reset_index()
            .merge(staff[['staff_id', 'name']], on='staff_id')
        )
        staff_performance.columns = ['StaffID', 'Converted Leads', 'Name']
        st.bar_chart(staff_performance.set_index('Name')['Converted Leads'])

if __name__ == "__main__":
    main()