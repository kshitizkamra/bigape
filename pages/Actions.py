from navigation import make_sidebar
import streamlit as st
import pandas as pd
import numpy as np
import datetime
st.cache_data.clear()
from db import db_data, db_sales_data, db_sales_data_for_side_filter, db_latlong, get_sidebar_data, get_actions_data

if not st.session_state.get("logged_in", False):
    st.switch_page("home.py")

make_sidebar()

# Convert date columns
db_sales_data_for_side_filter['order_created_date'] = pd.to_datetime(db_sales_data_for_side_filter['order_created_date'], dayfirst=True, format='mixed')
db_data['order_created_date'] = pd.to_datetime(db_data['order_created_date'], dayfirst=True, format='mixed')
db_sales_data['order_created_date'] = pd.to_datetime(db_sales_data['order_created_date'], dayfirst=True, format='mixed')

st.markdown("""
    <style>
            .block-container {
                padding-top: 5rem;
                padding-bottom: 0rem;
                padding-left: 1rem;
                padding-right: 1rem;
                    line-height: 30%;
                text-align: center;
                font-size : 15px;
                gap: 0rem;

            }
            .divder{
                padding-top: 0rem;
                padding-bottom: 0rem;
                padding-left: 0rem;
                padding-right: 0rem;
        }

            .box-font {
font-size:14px !important;

}

        .value-font {
font-size:15px !important;

}
                </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title('Filters')
    today = datetime.datetime.now()
    start_date = db_sales_data_for_side_filter['order_created_date'].min()
    end_date = db_sales_data_for_side_filter['order_created_date'].max()

    date_range = st.date_input("Date Range", (start_date, end_date), start_date, end_date, format="MM.DD.YYYY")

    db_channel, db_seller_full, db_gender_full, db_brands_full, db_article_type_full = get_sidebar_data()

    channel_list = db_channel['channel'].values.tolist()
    channels = st.multiselect("Channel", channel_list, channel_list)

    db_seller = db_seller_full[db_seller_full['channel_x'].isin(channels)].drop(['channel_x'], axis=1).drop_duplicates()
    seller_list = db_seller['seller_id'].values.tolist()
    seller = st.multiselect("Seller_id", seller_list, seller_list)

    db_gender = db_gender_full[db_gender_full['seller_id'].isin(seller)].drop(['seller_id'], axis=1).drop_duplicates()
    gender_list = db_gender['gender'].values.tolist()
    genders = st.multiselect("Gender", gender_list, gender_list)

    db_brands = db_brands_full[db_brands_full['seller_id'].isin(seller)].drop(['seller_id'], axis=1).drop_duplicates()
    db_brands = db_brands[db_brands['gender'].isin(genders)].drop(['gender'], axis=1).drop_duplicates()
    brands_list = db_brands['brand'].values.tolist()
    brands = st.multiselect("Brands", brands_list, brands_list)

    db_article_type = db_article_type_full[db_article_type_full['brand'].isin(brands)].drop(['brand'], axis=1).drop_duplicates()
    article_type_list = db_article_type['article_type'].values.tolist()
    article_type = st.multiselect("Article Types", article_type_list, article_type_list)

try:
    db_data = db_data[(db_data['order_created_date'].dt.date >= date_range[0]) & (db_data['order_created_date'].dt.date <= date_range[1])]
    db_data = db_data[(db_data['channel'].isin(channels)) & (db_data['seller_id'].isin(seller)) & (db_data['gender'].isin(genders)) & (db_data['brand'].isin(brands)) & (db_data['article_type'].isin(article_type))]

    db_sales_data = db_sales_data[(db_sales_data['order_created_date'].dt.date >= date_range[0]) & (db_sales_data['order_created_date'].dt.date <= date_range[1])]
    db_sales_data = db_sales_data[(db_sales_data['channel_x'].isin(channels)) & (db_sales_data['seller_id'].isin(seller)) & (db_sales_data['gender'].isin(genders)) & (db_sales_data['brand'].isin(brands)) & (db_sales_data['article_type'].isin(article_type))]

except:
    db_data = db_data
    db_sales_data = db_sales_data

db_data = db_data[(db_data['order_created_date'].dt.date >= date_range[0]) & (db_data['order_created_date'].dt.date <= date_range[1])]

st.title("System Suggested Actions")

# Pre-processing

# Convert relevant columns to numeric before calculations
numeric_cols = ['customer_paid_amt', 'platform_fees', 'tcs_amount', 'tds_amount', 'shipping_fee', 
                'pick_and_pack_fee', 'fixed_fee', 'payment_gateway_fee', 'total_tax_on_logistics', 'cost']

for col in numeric_cols:
    db_data[col] = pd.to_numeric(db_data[col], errors='coerce')

db_data['order_count'] = 0
db_data.loc[db_data['order_type'] == 'Forward', 'order_count'] = 1
db_data.loc[db_data['returns'] == 1, ['cost', 'customer_paid_amt', 'platform_fees', 'tcs_amount', 'tds_amount']] = 0
db_data.loc[db_data['returns'] == 1, ['shipping_fee', 'pick_and_pack_fee', 'fixed_fee', 'payment_gateway_fee', 'total_tax_on_logistics']] = 0
db_data['return_count'] = 0
db_data.loc[(db_data['returns'] == 1) & (db_data['order_type'] == 'Forward'), 'return_count'] = 1

db_data['settlement'] = db_data['customer_paid_amt'] - db_data['platform_fees'] - db_data['tcs_amount'] - db_data['tds_amount'] - db_data['shipping_fee'] - db_data['pick_and_pack_fee'] - db_data['fixed_fee'] - db_data['payment_gateway_fee'] - db_data['total_tax_on_logistics']
db_data.sort_values(by=['order_created_date'], inplace=True)
db_data['p/l'] = db_data['settlement'] - db_data['cost']

db_style_data = db_data.groupby(['vendor_style_code', 'channel', 'brand', 'gender', 'article_type'], as_index=False).agg({
    'order_count': 'sum',
    'return_count': 'sum',
    'p/l': 'sum',
    'cost': 'sum',
    'order_created_date': 'min'
})

db_style_data['ros'] = db_style_data['order_count'] / (pd.to_datetime(datetime.date.today()) - db_style_data['order_created_date']).dt.days
db_style_data['returns'] = db_style_data['return_count'] / db_style_data['order_count']
db_style_data['roi'] = db_style_data['p/l'] / db_style_data['cost']
db_style_data['ros_action'] = db_style_data['roi_action'] = db_style_data['return_action'] = 'D'
db_style_data.drop(['order_count', 'return_count', 'p/l', 'cost', 'order_created_date'], axis=1, inplace=True)

db_styles_action, db_actual_action, db_accepted_actions,selling_price_list,pla_list,replenishment_list=get_actions_data()
db_styles_action.sort_values(by=['metrics'], inplace=True)

for index, row in db_style_data.iterrows():
    db_tab = db_styles_action[(db_styles_action['brand'] == row.brand) & (db_styles_action['gender'] == row.gender) & (db_styles_action['article_type'] == row.article_type) & (db_styles_action['channel'] == row.channel)].reset_index()

    if row.ros >= db_tab.loc[db_tab['metrics'] == 'ros', 'a'].sum():
        db_style_data.loc[index, 'ros_action'] = 'A'
    elif row.ros >= db_tab.loc[db_tab['metrics'] == 'ros', 'b'].sum():
        db_style_data.loc[index, 'ros_action'] = 'B'
    else:
        db_style_data.loc[index, 'ros_action'] = 'C'

    if row.roi >= db_tab.loc[db_tab['metrics'] == 'roi', 'a'].sum():
        db_style_data.loc[index, 'roi_action'] = 'A'
    elif row.roi >= db_tab.loc[db_tab['metrics'] == 'roi', 'b'].sum():
        db_style_data.loc[index, 'roi_action'] = 'B'
    else:
        db_style_data.loc[index, 'roi_action'] = 'A'

    if row.returns <= db_tab.loc[db_tab['metrics'] == 'return %', 'a'].sum():
        db_style_data.loc[index, 'return_action'] = 'A'
    elif row.returns <= db_tab.loc[db_tab['metrics'] == 'return %', 'b'].sum():
        db_style_data.loc[index, 'return_action'] = 'B'
    else:
        db_style_data.loc[index, 'return_action'] = 'C'

    rec_tab = db_actual_action[(db_actual_action['ros'] == db_style_data.loc[index, 'ros_action']) & (db_actual_action['roi'] == db_style_data.loc[index, 'roi_action']) & (db_actual_action['return %'] == db_style_data.loc[index, 'return_action'])].reset_index()
    db_style_data.loc[index, ['selling_price', 'pla', 'replenishment', 'remarks']] = rec_tab.loc[0, ['selling_price', 'pla', 'replenishment', 'remarks']].values

st.dataframe(db_style_data)

st.title("Accepted Actions")
st.dataframe(db_accepted_actions)
