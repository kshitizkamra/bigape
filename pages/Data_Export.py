from navigation import make_sidebar
import streamlit as st
import pandas as pd
import datetime
st.cache_data.clear()
from db import db_data, db_sales_data, db_sales_data_for_side_filter, db_latlong, get_sidebar_data

if not st.session_state.get("logged_in", False):
    st.switch_page("home.py")

make_sidebar()

# Sidebar data
db_channel, db_seller, db_gender, db_brands, db_article_type = get_sidebar_data()

# Convert date columns
db_sales_data_for_side_filter['order_created_date'] = pd.to_datetime(db_sales_data_for_side_filter['order_created_date'], dayfirst=True, format='mixed')
db_data['order_created_date'] = pd.to_datetime(db_data['order_created_date'], dayfirst=True, format='mixed')
db_sales_data['order_created_date'] = pd.to_datetime(db_sales_data['order_created_date'], dayfirst=True, format='mixed')

# Page style
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
        .divder {
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

# Sidebar filters
with st.sidebar:
    st.title('Filters')
    start_date = db_sales_data_for_side_filter['order_created_date'].min()
    end_date = db_sales_data_for_side_filter['order_created_date'].max()

    date_range = st.date_input(
        "Date Range",
        (start_date, end_date),
        start_date,
        end_date,
        format="MM.DD.YYYY",
    )

    channel_list = db_channel['channel'].dropna().unique().tolist()
    channels = st.multiselect("Channel", channel_list, channel_list)

    db_seller = db_seller[db_seller['channel_x'].isin(channels)].drop('channel_x', axis=1).drop_duplicates()
    seller_list = db_seller['seller_id'].dropna().tolist()
    seller = st.multiselect("Seller_id", seller_list, seller_list)

    db_gender = db_gender[db_gender['seller_id'].isin(seller)].drop('seller_id', axis=1).drop_duplicates()
    gender_list = db_gender['gender'].dropna().tolist()
    genders = st.multiselect("Gender", gender_list, gender_list)

    db_brands = db_brands[db_brands['seller_id'].isin(seller)].drop('seller_id', axis=1).drop_duplicates()
    db_brands = db_brands[db_brands['gender'].isin(genders)].drop('gender', axis=1).drop_duplicates()
    brands_list = db_brands['brand'].dropna().tolist()
    brands = st.multiselect("Brands", brands_list, brands_list)

    db_article_type = db_article_type[db_article_type['brand'].isin(brands)].drop('brand', axis=1).drop_duplicates()
    article_type_list = db_article_type['article_type'].dropna().tolist()
    article_type = st.multiselect("Article Types", article_type_list, article_type_list)

# Apply filters
try:
    db_data = db_data[
        (db_data['order_created_date'].dt.date >= date_range[0]) &
        (db_data['order_created_date'].dt.date <= date_range[1]) &
        (db_data['channel'].isin(channels)) &
        (db_data['seller_id'].isin(seller)) &
        (db_data['gender'].isin(genders)) &
        (db_data['brand'].isin(brands)) &
        (db_data['article_type'].isin(article_type))
    ]

    db_sales_data = db_sales_data[
        (db_sales_data['order_created_date'].dt.date >= date_range[0]) &
        (db_sales_data['order_created_date'].dt.date <= date_range[1]) &
        (db_sales_data['channel_x'].isin(channels)) &
        (db_sales_data['seller_id'].isin(seller)) &
        (db_sales_data['gender'].isin(genders)) &
        (db_sales_data['brand'].isin(brands)) &
        (db_sales_data['article_type'].isin(article_type))
    ]
except:
    pass

db_data_final = db_data
db_sales_data_final = db_sales_data

tab1, tab2 = st.tabs(['Sales_Data', 'Settlement_Data'])

# Sales Tab
with tab1:
    db_sales_data_final['month'] = db_sales_data_final['order_created_date'].dt.strftime('%b-%y')
    db_sales_data_final.rename(columns={'channel_x': 'channel'}, inplace=True)
    db_sales_data_final['return_amount'] = db_sales_data_final['final_amount'] * db_sales_data_final['returns']
    db_sales_data_final.reset_index(inplace=True, drop=True)
    db_sales_data_final.sort_values(by='order_created_date', ascending=False, inplace=True)

    with st.container(border=True):
        group_by_list = ['channel', 'seller_id', 'state', 'brand', 'gender', 'article_type', 'month', 'vendor_style_code', 'size', 'collection', 'mrp', 'cost', 'color']
        group_by = st.multiselect("Group By", group_by_list, placeholder="Select for Grouping the data", label_visibility='collapsed')

        if group_by:
            grouped = db_sales_data_final.groupby(group_by, sort=False).agg({
                'order_release_id': 'count',
                'final_amount': 'sum',
                'returns': 'sum',
                'return_amount': 'sum'
            })
            grouped.rename(columns={'order_release_id': 'Total_Orders'}, inplace=True)
            st.divider()
            st.dataframe(grouped)
        else:
            st.dataframe(db_sales_data_final)

# Settlement Tab
with tab2:
    db_data_final['order_count'] = 1
    db_data_final['return_count'] = 0

    db_data_final.loc[db_data_final['order_type'] == 'Reverse', 'order_count'] = 0
    db_data_final.loc[db_data_final['returns'] == 1, ['cost', 'customer_paid_amt', 'platform_fees', 'tcs_amount', 'tds_amount']] = 0
    db_data_final.loc[(db_data_final['returns'] == 1) & (db_data_final['order_type'] == 'Forward'), 'return_count'] = 1

    db_data_final['settlement'] = db_data_final['customer_paid_amt'] - db_data_final['platform_fees'] - db_data_final['tcs_amount'] - db_data_final['tds_amount'] - db_data_final['total_logistics']
    db_data_final['month'] = db_data_final['order_created_date'].dt.strftime('%b-%y')
    db_data_final.sort_values(by='order_created_date', ascending=False, inplace=True)

    with st.container(border=True):
        group_by_list = ['channel', 'seller_id', 'state', 'brand', 'gender', 'article_type', 'month', 'vendor_style_code', 'shipment_zone_classification', 'size', 'collection name', 'mrp', 'cost', 'color']
        group_by = st.multiselect("Group By", group_by_list, placeholder="Select for Grouping the data", label_visibility='collapsed')

        if group_by:
            grouped = db_data_final.groupby(group_by, sort=False).agg({
                'order_count': 'sum',
                'return_count': 'sum',
                'customer_paid_amt': 'sum',
                'platform_fees': 'sum',
                'tcs_amount': 'sum',
                'tds_amount': 'sum',
                'shipping_fee': 'sum',
                'pick_and_pack_fee': 'sum',
                'fixed_fee': 'sum',
                'payment_gateway_fee': 'sum',
                'total_tax_on_logistics': 'sum',
                'total_logistics': 'sum',
                'total_actual_settlement': 'sum',
                'settlement': 'sum',
                'cost': 'sum'
            })
            grouped['commission'] = grouped['platform_fees']
            grouped['taxes'] = grouped['tcs_amount'] + grouped['tds_amount']
            grouped['p/l'] = grouped['settlement'] - grouped['cost']
            grouped['roi'] = grouped['p/l'] / grouped['cost']
            grouped['return %'] = grouped['return_count'] / grouped['order_count']
            grouped['asp'] = grouped['customer_paid_amt'] / (grouped['order_count'] - grouped['return_count'])
            grouped['commission/unit'] = grouped['commission'] / (grouped['order_count'] - grouped['return_count'])
            grouped['taxes/unit'] = grouped['taxes'] / (grouped['order_count'] - grouped['return_count'])
            grouped['logistics/unit'] = grouped['total_logistics'] / (grouped['order_count'] - grouped['return_count'])
            grouped['settlement/unit'] = grouped['settlement'] / (grouped['order_count'] - grouped['return_count'])
            grouped['cost/unit'] = grouped['cost'] / (grouped['order_count'] - grouped['return_count'])
            grouped['p&l/unit'] = grouped['p/l'] / (grouped['order_count'] - grouped['return_count'])

            st.divider()
            st.dataframe(grouped)
        else:
            st.dataframe(db_data_final)
