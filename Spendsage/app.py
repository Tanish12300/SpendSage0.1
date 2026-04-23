# SpendSage - Ultimate Expense Tracker
# All features included: Salary, Budget, Charts, Export, Dark Mode, Edit/Delete

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json

# ----------------------------- Dark Mode Toggle -----------------------------
dark_mode = st.toggle("🌙 Dark Mode", value=False)
if dark_mode:
    st.markdown("""
        <style>
        .stApp { background-color: #1e1e1e; color: #ffffff; }
        .stButton button { background-color: #4CAF50; color: white; }
        .stMetric { background-color: #2d2d2d; border-radius: 10px; padding: 10px; }
        </style>
    """, unsafe_allow_html=True)

# ----------------------------- Page Config -----------------------------
st.set_page_config(page_title="SpendSage", page_icon="🪄", layout="wide")
st.title("🪄 SpendSage")
st.markdown("*Your All‑in‑One Smart Expense Tracker*")
st.divider()

# ----------------------------- Currency Options -----------------------------
currencies = {
    "🇮🇳 Indian Rupee (INR)": {"symbol": "₹", "code": "INR"},
    "🇺🇸 US Dollar (USD)": {"symbol": "$", "code": "USD"},
    "🇪🇺 Euro (EUR)": {"symbol": "€", "code": "EUR"},
    "🇬🇧 British Pound (GBP)": {"symbol": "£", "code": "GBP"},
    "🇯🇵 Japanese Yen (JPY)": {"symbol": "¥", "code": "JPY"},
}

# ----------------------------- Session State Init -----------------------------
if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=['date', 'description', 'amount', 'currency', 'category'])
if 'salary' not in st.session_state:
    st.session_state.salary = 0.0
if 'last_added' not in st.session_state:
    st.session_state.last_added = None
if 'budget_limits' not in st.session_state:
    st.session_state.budget_limits = {
        "Food": 5000, "Shopping": 3000, "Entertainment": 2000,
        "Transport": 2000, "Bills": 5000, "Health": 2000
    }

# ----------------------------- Helper Functions -----------------------------
def format_currency(amount):
    return f"{currency_symbol}{amount:,.2f}"

def get_total_spent(df):
    return df['amount'].sum() if not df.empty else 0

def get_remaining_salary():
    if st.session_state.salary > 0:
        return st.session_state.salary - get_total_spent(st.session_state.expenses)
    return None

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    selected_currency = st.selectbox("Select Currency", list(currencies.keys()))
    currency_symbol = currencies[selected_currency]["symbol"]
    currency_code = currencies[selected_currency]["code"]
    
    st.divider()
    st.header("💰 Salary")
    salary_input = st.number_input(f"Monthly Salary ({currency_symbol})", min_value=0.0, step=1000.0,
                                   value=float(st.session_state.salary))
    if st.button("Set Salary", use_container_width=True):
        st.session_state.salary = salary_input
        st.success(f"Salary set to {currency_symbol}{salary_input:,.2f}")
        st.rerun()
    
    if st.session_state.salary > 0:
        st.info(f"Salary: {currency_symbol}{st.session_state.salary:,.2f}")
    
    st.divider()
    st.header("🎯 Budget Limits")
    for cat in st.session_state.budget_limits:
        st.session_state.budget_limits[cat] = st.number_input(f"{cat} Budget", min_value=0,
                                                              value=st.session_state.budget_limits[cat],
                                                              key=f"budget_{cat}")
    
    st.divider()
    page = st.radio("📱 Navigate", ["➕ Add Expense", "📜 History", "📈 Dashboard", "💰 Salary View", "📥 Backup & Export"])

# ============================= PAGE 1: ADD EXPENSE =============================
if page == "➕ Add Expense":
    st.subheader("➕ Add New Expense")
    
    if st.session_state.last_added:
        st.success(f"✅ Added: {st.session_state.last_added}")
    
    with st.form(key="expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            description = st.text_input("What did you buy?", placeholder="e.g., Starbucks, Netflix")
        with col2:
            amount = st.number_input(f"Amount ({currency_symbol})", min_value=0.0, step=0.01, value=0.00)
        
        date = st.date_input("Date", datetime.now())
        category = st.selectbox("Category", ["Food", "Shopping", "Entertainment", "Transport", "Bills", "Health", "Education", "Groceries", "Rent"])
        
        if st.form_submit_button("💾 Save Expense", use_container_width=True, type="primary"):
            if description and amount > 0:
                new_expense = pd.DataFrame({
                    'date': [date],
                    'description': [description],
                    'amount': [amount],
                    'currency': [currency_code],
                    'category': [category]
                })
                st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
                st.session_state.last_added = f"{description} - {currency_symbol}{amount:.2f}"
                st.success("Saved!")
                st.balloons()
                st.rerun()
            else:
                st.error("Please fill both description and amount")
    
    if not st.session_state.expenses.empty:
        st.divider()
        st.subheader("📋 Recent Expenses")
        recent = st.session_state.expenses.tail(5).copy()
        recent['amount'] = recent['amount'].apply(format_currency)
        st.dataframe(recent[['date', 'description', 'amount', 'category']], use_container_width=True)

# ============================= PAGE 2: HISTORY (Edit/Delete) =============================
elif page == "📜 History":
    st.subheader("📜 Expense History")
    
    if st.session_state.expenses.empty:
        st.info("No expenses yet. Add some!")
    else:
        # Filtering
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_type = st.selectbox("Time Filter", ["All Time", "This Month", "Last Month", "Custom Range"])
        with col_f2:
            search = st.text_input("🔍 Search", placeholder="Type to filter description")
        
        df = st.session_state.expenses.copy()
        now = datetime.now()
        if filter_type == "This Month":
            df = df[pd.to_datetime(df['date']).dt.month == now.month]
        elif filter_type == "Last Month":
            last = now.replace(day=1) - timedelta(days=1)
            df = df[pd.to_datetime(df['date']).dt.month == last.month]
        elif filter_type == "Custom Range":
            col_a, col_b = st.columns(2)
            with col_a:
                start = st.date_input("From", datetime.now().replace(day=1))
            with col_b:
                end = st.date_input("To", datetime.now())
            df = df[(pd.to_datetime(df['date']) >= pd.to_datetime(start)) & (pd.to_datetime(df['date']) <= pd.to_datetime(end))]
        
        if search:
            df = df[df['description'].str.contains(search, case=False)]
        
        # Total
        total = df['amount'].sum()
        st.metric("💰 Total for selected period", format_currency(total))
        
        # Remaining if salary set
        if st.session_state.salary > 0:
            remaining = st.session_state.salary - get_total_spent(st.session_state.expenses)
            st.metric("💰 Remaining (overall)", format_currency(remaining))
        
        st.divider()
        
        # Display each row with edit/delete
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
            with col1:
                st.write(row['description'])
            with col2:
                st.write(format_currency(row['amount']))
            with col3:
                st.write(str(row['date']))
            with col4:
                st.write(row['category'])
            with col5:
                if st.button(f"✏️", key=f"edit_{idx}"):
                    new_amount = st.number_input("New amount", value=row['amount'], key=f"newamt_{idx}")
                    if st.button("Update", key=f"upd_{idx}"):
                        st.session_state.expenses.at[idx, 'amount'] = new_amount
                        st.rerun()
            with col6:
                if st.button(f"🗑️", key=f"del_{idx}"):
                    st.session_state.expenses.drop(idx, inplace=True)
                    st.rerun()
        
        # Clear all
        if st.button("🗑️ Clear All History", type="secondary"):
            st.session_state.expenses = pd.DataFrame(columns=['date', 'description', 'amount', 'currency', 'category'])
            st.rerun()

# ============================= PAGE 3: DASHBOARD =============================
elif page == "📈 Dashboard":
    st.subheader("📊 Spending Dashboard")
    
    if st.session_state.expenses.empty:
        st.info("No data to display. Add expenses first.")
    else:
        df = st.session_state.expenses.copy()
        total = get_total_spent(df)
        
        # Salary overview card
        if st.session_state.salary > 0:
            remaining = st.session_state.salary - total
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Monthly Salary", format_currency(st.session_state.salary))
            with col2:
                st.metric("💸 Total Spent", format_currency(total))
            with col3:
                st.metric("✅ Money Left", format_currency(remaining))
            spent_percent = (total / st.session_state.salary) * 100
            st.progress(min(spent_percent/100, 1.0))
            st.caption(f"Used {spent_percent:.1f}% of salary")
            st.divider()
        
        # Charts
        col_ch1, col_ch2 = st.columns(2)
        with col_ch1:
            st.subheader("📈 Spending Trend")
            if len(df) > 1:
                trend = df.groupby('date')['amount'].sum().reset_index()
                fig = px.line(trend, x='date', y='amount', markers=True, title="Daily Spending")
                fig.update_traces(line=dict(color='#4CAF50', width=3))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Add at least 2 transactions to see trend")
        
        with col_ch2:
            st.subheader("🥧 Category Breakdown")
            cat_sum = df.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(cat_sum, values='amount', names='category', hole=0.3, title="Spending by Category")
            st.plotly_chart(fig, use_container_width=True)
        
        # Budget Alerts
        st.subheader("⚠️ Budget Alerts")
        for cat, limit in st.session_state.budget_limits.items():
            spent = df[df['category'] == cat]['amount'].sum() if cat in df['category'].values else 0
            percent = (spent / limit) * 100 if limit > 0 else 0
            if percent > 100:
                st.error(f"🚨 {cat}: {format_currency(spent)} / {format_currency(limit)} ({percent:.0f}% OVER BUDGET!)")
            elif percent > 80:
                st.warning(f"⚠️ {cat}: {format_currency(spent)} / {format_currency(limit)} ({percent:.0f}% near limit)")
            else:
                st.info(f"✅ {cat}: {format_currency(spent)} / {format_currency(limit)} ({percent:.0f}%)")
        
        # Top expenses
        st.subheader("🔥 Top 5 Expenses")
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0) 
        top = df.nlargest(5, 'amount')[['date', 'description', 'amount', 'category']].copy()
        top['amount'] = top['amount'].apply(format_currency)
        st.dataframe(top, use_container_width=True)

# ============================= PAGE 4: SALARY VIEW =============================
elif page == "💰 Salary View":
    st.subheader("💰 Salary & Financial Overview")
    
    if st.session_state.salary == 0:
        st.warning("Please set your monthly salary in the sidebar first!")
    else:
        total_spent = get_total_spent(st.session_state.expenses)
        remaining = st.session_state.salary - total_spent
        percent_used = (total_spent / st.session_state.salary) * 100
        percent_saved = max((remaining / st.session_state.salary) * 100, 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Salary", format_currency(st.session_state.salary))
        with col2:
            st.metric("💸 Spent", format_currency(total_spent))
        with col3:
            st.metric("✅ Left", format_currency(remaining))
        
        st.subheader("📊 Budget Usage")
        st.progress(min(percent_used/100, 1.0))
        st.caption(f"Spent: {percent_used:.1f}% | Saved: {percent_saved:.1f}%")
        
        # Simple bar chart
        fig = px.bar(x=['Salary', 'Spent', 'Left'], y=[st.session_state.salary, total_spent, max(remaining, 0)],
                     title="Salary Breakdown", color=['Salary', 'Spent', 'Left'],
                     color_discrete_map={'Salary': '#2196F3', 'Spent': '#FF6B6B', 'Left': '#4CAF50'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Advice
        st.subheader("💡 Financial Advice")
        if remaining < 0:
            st.error(f"⚠️ You overspent by {format_currency(abs(remaining))}. Review expenses and cut unnecessary costs!")
        elif remaining < st.session_state.salary * 0.1:
            st.warning(f"📉 You're saving only {percent_saved:.1f}% of your salary. Try to reduce dining out and subscriptions.")
        elif remaining < st.session_state.salary * 0.2:
            st.info(f"📈 Good! You're saving {percent_saved:.1f}%. Aim for 20% to build wealth faster.")
        else:
            st.success(f"🎉 Excellent! You're saving {percent_saved:.1f}% of your salary. Consider investing the surplus!")

# ============================= PAGE 5: BACKUP & EXPORT =============================
elif page == "📥 Backup & Export":
    st.subheader("📥 Data Backup & Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Export as CSV")
        if not st.session_state.expenses.empty:
            csv = st.session_state.expenses.to_csv(index=False)
            st.download_button("Download CSV", csv, f"spendsage_{datetime.now().strftime('%Y%m%d')}.csv")
        else:
            st.info("No data to export")
    
    with col2:
        st.subheader("💾 Backup (JSON)")
        if not st.session_state.expenses.empty:
            backup_data = {
                'expenses': st.session_state.expenses.to_dict('records'),
                'salary': st.session_state.salary,
                'budget_limits': st.session_state.budget_limits
            }
            backup_json = json.dumps(backup_data, indent=2, default=str)
            st.download_button("Download Backup", backup_json, "spendsage_backup.json")
        else:
            st.info("No data to backup")
    
    st.divider()
    st.subheader("🔄 Restore from Backup")
    uploaded = st.file_uploader("Choose backup file", type=['json'])
    if uploaded:
        try:
            data = json.load(uploaded)
            st.session_state.expenses = pd.DataFrame(data['expenses'])
            st.session_state.salary = data.get('salary', 0)
            if 'budget_limits' in data:
                st.session_state.budget_limits = data['budget_limits']
            st.success("✅ Restore successful! Refreshing...")
            st.rerun()
        except Exception as e:
            st.error(f"Invalid backup file: {e}")

# ----------------------------- Footer -----------------------------
st.divider()
st.caption(f"🪄 SpendSage - {currency_code} | Built with Streamlit | Made with ❤️")