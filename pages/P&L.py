from navigation import make_sidebar
import hmac
import streamlit as st
import pandas as pd
import numpy as np
import sys
import glob
import os
import altair as alt
import plotly.express as px
import datetime
import time
import math
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from streamlit_extras.stylable_container import stylable_container
from annotated_text import annotated_text
from db import db_data, db_sales_data, db_sales_data_for_side_filter, db_latlong, get_sidebar_data, get_actions_data

if not st.session_state.get("logged_in", False):
    st.switch_page("home.py")
make_sidebar()

# Get sidebar data from db.py (MySQL)
db_channel, db_seller, db_gender, db_brands, db_article_type = get_sidebar_data()

# Read and process data from db.py (MySQL)
db_data['order_created_date'] = pd.to_datetime(db_data['order_created_date'], dayfirst=True, format='mixed')
db_sales_data['order_created_date'] = pd.to_datetime(db_sales_data['order_created_date'], dayfirst=True, format='mixed')
db_sales_data_for_side_filter['order_created_date'] = pd.to_datetime(db_sales_data_for_side_filter['order_created_date'], dayfirst=True, format='mixed')

count = 0
st.markdown("""
    <style>
             .reportview-container .main .block-container{{
            padding-top: {padding_top}rem;
        }}

            div[class^='st-emotion-cache-10oheav'] {{ padding-top: {padding_top}rem; }}
            
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem;
                padding-left: 0rem;
                padding-right: 1rem;
                margin-left: 1rem;
                line-height: 0%;
                text-align: center;
                font-size : 12px;
                gap: 0rem;
                
            }
            .divder{
                padding-top: 0rem;
                padding-bottom: 0rem;
                padding-left: 0rem;
                padding-right: 0rem;
                width: 50%;
        }

            .box-font {
font-size:13px !important;

}       
           

        .value-font {
font-size:14px !important;

}
            .stTabs [data-baseweb="tab-list"] {
		gap: 5px;
    }

	.stTabs [data-baseweb="tab"] {
		height: 40px;
        white-space: pre-wrap;
		background-color: #F0F2F6;
		border-radius: 4px 4px 0px 0px;
		gap: 1px;
		padding-top: 10px;
		padding-bottom: 10px;
        padding: 10px;
    }

	.stTabs [aria-selected="true"] {
  		background-color: #FFFFFF;
	}
                </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title('Filters')
    today = datetime.datetime.now()
    next_year = today.year + 1
    start_date = db_sales_data_for_side_filter['order_created_date'].min()
    end_date = db_sales_data_for_side_filter['order_created_date'].max()

    date_range = st.date_input(
        "Date Range",
        (start_date, end_date),
        start_date,
        end_date,
        format="MM.DD.YYYY",
    )

    # Filters from the sidebar data obtained from db.py (MySQL)
    channel_list = db_channel['channel'].values.tolist()
    channels = st.multiselect("Channel", channel_list, channel_list)

    db_seller = db_seller[(db_seller['channel_x'].isin(channels))]
    db_seller = db_seller.drop(['channel_x'], axis=1).drop_duplicates()
    seller_list = db_seller['seller_id'].values.tolist()
    seller = st.multiselect("Seller_id", seller_list, seller_list)

    db_gender = db_gender[(db_gender['seller_id'].isin(seller))]
    db_gender = db_gender.drop(['seller_id'], axis=1).drop_duplicates()
    gender_list = db_gender['gender'].values.tolist()
    genders = st.multiselect("Gender", gender_list, gender_list)

    db_brands = db_brands[(db_brands['seller_id'].isin(seller)) & (db_brands['gender'].isin(genders))]
    db_brands = db_brands.drop(['seller_id', 'gender'], axis=1).drop_duplicates()
    brands_list = db_brands['brand'].values.tolist()
    brands = st.multiselect("Brands", brands_list, brands_list)

    db_article_type = db_article_type[(db_article_type['brand'].isin(brands))]
    db_article_type = db_article_type.drop(['brand'], axis=1).drop_duplicates()
    article_type_list = db_article_type['article_type'].values.tolist()
    article_type = st.multiselect("Article Types", article_type_list, article_type_list)

try:
    db_data = db_data[(db_data['order_created_date'].dt.date >= date_range[0]) & (db_data['order_created_date'].dt.date <= date_range[1])]
    db_data = db_data[(db_data['channel'].isin(channels))]
    db_data = db_data[(db_data['seller_id'].isin(seller))]
    db_data = db_data[(db_data['gender'].isin(genders))]
    db_data = db_data[(db_data['brand'].isin(brands))]
    db_data = db_data[(db_data['article_type'].isin(article_type))]

    db_sales_data = db_sales_data[(db_sales_data['order_created_date'].dt.date >= date_range[0]) & (db_sales_data['order_created_date'].dt.date <= date_range[1])]
    db_sales_data = db_sales_data[(db_sales_data['channel_x'].isin(channels))]
    db_sales_data = db_sales_data[(db_sales_data['seller_id'].isin(seller))]
    db_sales_data = db_sales_data[(db_sales_data['gender'].isin(genders))]
    db_sales_data = db_sales_data[(db_sales_data['brand'].isin(brands))]
    db_sales_data = db_sales_data[(db_sales_data['article_type'].isin(article_type))]

except Exception as e:
    st.error(f"An error occurred: {e}")
    db_data = db_data
    db_sales_data = db_sales_data

st.title("💸 P&L Overview")

db_data_final = db_data
db_sales_data_final = db_sales_data


total_channel=db_sales_data['channel_x'].unique().tolist()

total_channel.insert(0, "All")

count=count+1
with stylable_container(
        key=str(count),
        css_styles="""
            {
                border: 4px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: 10px;
                margin : 0px;
                
            }
            
            """,
    ):
    tab=st.tabs(total_channel)
    tab_len=len(total_channel)

    for i in range(tab_len):
        with tab[i]:
            if i==0 :
                db_data_pnl=db_data_final
                db_sales_data_pnl=db_sales_data_final
            else :
                db_data_pnl=db_data_final[db_data_final['channel']==total_channel[i]]
                db_sales_data_pnl=db_sales_data_final[db_sales_data_final['channel_x']==total_channel[i]]
            


            container=st.container(border=True)
            container1=st.container(border=True)

            
            total_orders=len(db_sales_data_pnl)
            ordered_gmv=sum(db_sales_data_pnl['final_amount'])
            cancelled_orders=len(db_sales_data_pnl[db_sales_data_pnl['order_status']=='F'])
            cancelled_value=db_sales_data_pnl.loc[db_sales_data_pnl['order_status']=='F','final_amount'].sum()

            shipped_orders=total_orders-cancelled_orders
            shipped_value=ordered_gmv-cancelled_value
            RTO=len(db_sales_data_pnl[db_sales_data_pnl['order_status']=='RTO'])
            rto_value=db_sales_data_pnl.loc[db_sales_data_pnl['order_status']=='RTO','final_amount'].sum()
            in_transit=len(db_sales_data_pnl[db_sales_data_pnl['order_status'].isin({'SH','L','PK','WP'})])
            in_transit_value=db_sales_data_pnl.loc[db_sales_data_pnl['order_status'].isin({'SH','L','PK','WP'}),'final_amount'].sum()
            delivered=shipped_orders-RTO-in_transit
            delivered_value=shipped_value-in_transit_value-rto_value
            total_returns=len(db_sales_data_pnl[db_sales_data_pnl['returns']==1])
            returns_value=db_sales_data_pnl.loc[db_sales_data_pnl['returns']==1,'final_amount'].sum()
            successful_order=delivered-total_returns
            db_sales_value=db_sales_data_pnl[db_sales_data_pnl['returns']==0]
            db_sales_value=db_sales_value[db_sales_value['order_status']=='C']
            total_sales_value=sum(db_sales_value['final_amount'])
            
            settled_orders_value=db_data_pnl.loc[db_data_pnl['order_type']=='Forward','customer_paid_amt'].sum()
            settled_order_qty=db_data_pnl.loc[db_data_pnl['order_type']=='Forward','customer_paid_amt'].count()
            non_settled_orders_value=round(delivered_value-settled_orders_value,2)
            db_data_pnl['total_actual_settlement'] = pd.to_numeric(db_data_pnl['total_actual_settlement'], errors='coerce')
            db_data_pnl['cost'] = pd.to_numeric(db_data_pnl['cost'], errors='coerce')
            settled_orders_value_net_sales=round(db_data_pnl.loc[db_data_pnl['returns']==0,'customer_paid_amt'].sum(),2)
            net_sales_order_qty=round(db_data_pnl.loc[db_data_pnl['returns']==0,'customer_paid_amt'].count(),2)
            settled_orders_value_returns=round(settled_orders_value-settled_orders_value_net_sales,2)
            return_order_qty=round(settled_order_qty-net_sales_order_qty,2)
            
            non_settled_orders_count=len(db_sales_data[db_sales_data['order_status'].isin({'C'})])-db_data_pnl.loc[db_data_pnl['order_type']=='Forward','customer_paid_amt'].count()
            

        
            commission_net_sales=db_data_pnl.loc[db_data_pnl['returns']==0,'platform_fees'].sum()
            commission_returns=0
            taxes_net_sales=db_data_pnl.loc[db_data_pnl['returns']==0,'tcs_amount'].sum()+db_data_pnl.loc[db_data_pnl['returns']==0,'tds_amount'].sum()
            taxes_returns=0
            logistics_net_sales=db_data_pnl.loc[db_data_pnl['returns']==0,'shipping_fee'].sum()+db_data_pnl.loc[db_data_pnl['returns']==0,'total_tax_on_logistics'].sum()
            logistics_returns=db_data_pnl.loc[db_data_pnl['returns']==1,'shipping_fee'].sum()+db_data_pnl.loc[db_data_pnl['returns']==1,'total_tax_on_logistics'].sum()
            pick_pack_net_sales=db_data_pnl.loc[db_data_pnl['returns']==0,'pick_and_pack_fee'].sum()
            pick_pack_return=db_data_pnl.loc[db_data_pnl['returns']==1,'pick_and_pack_fee'].sum()
            payment_gateway_net_sales=db_data_pnl.loc[db_data_pnl['returns']==0,'payment_gateway_fee'].sum()
            payment_gateway_return=db_data_pnl.loc[db_data_pnl['returns']==1,'payment_gateway_fee'].sum()
            settlement_net_sales=db_data_pnl.loc[db_data_pnl['returns']==0,'total_actual_settlement'].sum()
            
            payment_gateway_return=db_data_pnl.loc[db_data_pnl['returns']==1,'payment_gateway_fee'].sum()
            fixed_fee_net_sales=db_data_pnl.loc[db_data_pnl['returns']==0,'fixed_fee'].sum()
            fixed_fee_return=db_data_pnl.loc[db_data_pnl['returns']==1,'fixed_fee'].sum()
            actual_settlement_net_sales=settled_orders_value_net_sales-commission_net_sales-taxes_net_sales-logistics_net_sales-fixed_fee_net_sales-pick_pack_net_sales-payment_gateway_net_sales
            settlement_return=0-logistics_returns-fixed_fee_return-pick_pack_return-payment_gateway_return

            marketing_net_sales=actual_settlement_net_sales-settlement_net_sales
            marketing_return=0
            cogs_net_sales=db_data_pnl.loc[db_data_pnl['returns']==0,'cost'].sum()
            cogs_return=0
            pnl_net_sales=settlement_net_sales-cogs_net_sales
            pnl_return=settlement_return
            pnl_total=pnl_net_sales+pnl_return
            returns_data = [['Order_qty', '{:,}'.format(round(return_order_qty,2))],['Comission', '{:,}'.format(round(commission_returns,2))], ['Taxes', '{:,}'.format(round(taxes_returns,2))], ['Logistics', '{:,}'.format(round(logistics_returns,2))], ['Fixed-Fee', '{:,}'.format(round(fixed_fee_return,2))], ['Pick-Pack Fee', '{:,}'.format(round(pick_pack_return,2))], ['Pay Gate Fee', '{:,}'.format(round(payment_gateway_return,2))], ['Mktg & Others', '{:,}'.format(round(marketing_return,2))], ['Settlement', '{:,}'.format(round(settlement_return,2))], ['COGS', '{:,}'.format(round(cogs_return,2))], ['P/L', '{:,}'.format(round(pnl_return,2))]]
            returns_dataframe=pd.DataFrame(returns_data, columns=['Metric', 'Value'])
            net_sales_data = [['Order_qty', '{:,}'.format(round(net_sales_order_qty,2))],['Comission', '{:,}'.format(round(commission_net_sales,2))], ['Taxes', '{:,}'.format(round(taxes_net_sales,2))], ['Logistics', '{:,}'.format(round(logistics_net_sales,2))], ['Fixed-Fee', '{:,}'.format(round(fixed_fee_net_sales,2))], ['Pick-Pack Fee', '{:,}'.format(round(pick_pack_net_sales,2))], ['Pay Gate Fee', '{:,}'.format(round(payment_gateway_net_sales,2))], ['Mktg & Others', '{:,}'.format(round(marketing_net_sales,2))], ['Settlement', '{:,}'.format(round(settlement_net_sales,2))], ['COGS', '{:,}'.format(round(cogs_net_sales,2))], ['P/L', '{:,}'.format(round(pnl_net_sales,2))]]
            net_sales_dataframe=pd.DataFrame(net_sales_data, columns=['Metric', 'Value'])



            estimated_settled_orders_value_net_sales=settled_orders_value_net_sales/settled_orders_value*non_settled_orders_value
            estimated_settled_orders_value_returns=settled_orders_value_returns/settled_orders_value*non_settled_orders_value
            estimated_settled_orders_count=round(net_sales_order_qty/settled_order_qty*non_settled_orders_count,0)
            estimated_settled_orders_count_returns=non_settled_orders_count-estimated_settled_orders_count

            estimated_commission_net_sales=commission_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_commission_returns=0
            estimated_taxes_net_sales=taxes_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_taxes_returns=0
            estimated_logistics_net_sales=logistics_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_logistics_returns=logistics_returns/settled_orders_value_returns*estimated_settled_orders_value_returns
            estimated_pick_pack_net_sales=pick_pack_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_pick_pack_return=pick_pack_return/settled_orders_value_returns*estimated_settled_orders_value_returns
            estimated_payment_gateway_net_sales=payment_gateway_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_payment_gateway_return=payment_gateway_return/settled_orders_value_returns*estimated_settled_orders_value_returns

            estimated_mktg_net_sales=marketing_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_mktg_return=marketing_return/settled_orders_value_returns*estimated_settled_orders_value_returns

            estimated_fixed_fee_net_sales=fixed_fee_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_fixed_fee_return=fixed_fee_return/settled_orders_value_returns*estimated_settled_orders_value_returns
            estimated_settlement_net_sales=settlement_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_settlement_return=settlement_return/settled_orders_value_returns*estimated_settled_orders_value_returns
            estimated_cogs_net_sales=cogs_net_sales/settled_orders_value_net_sales*estimated_settled_orders_value_net_sales
            estimated_cogs_return=0
            estimated_pnl_net_sales=estimated_settlement_net_sales-estimated_cogs_net_sales
            estimated_pnl_return=estimated_settlement_return
            estimated_pnl_total=estimated_pnl_net_sales+estimated_pnl_return
            estimated_returns_data = [['Order_qty', '{:,}'.format(estimated_settled_orders_count_returns)],['Comission', '{:,}'.format(round(estimated_commission_returns,2))], ['Taxes', '{:,}'.format(round(estimated_taxes_returns,2))], ['Logistics', '{:,}'.format(round(estimated_logistics_returns,2))], ['Fixed-Fee', '{:,}'.format(round(estimated_fixed_fee_return,2))], ['Pick-Pack Fee', '{:,}'.format(round(estimated_pick_pack_return,2))], ['Pay Gate Fee', '{:,}'.format(round(estimated_payment_gateway_return,2))], ['Mktg & Others', '{:,}'.format(round(estimated_mktg_return,2))], ['Settlement', '{:,}'.format(round(estimated_settlement_return,2))], ['COGS', '{:,}'.format(round(estimated_cogs_return,2))], ['P/L', '{:,}'.format(round(estimated_pnl_return,2))]]
            estimated_returns_dataframe=pd.DataFrame(estimated_returns_data, columns=['Metric', 'Value'])
            estimated_net_sales_data = [['Order_qty', '{:,}'.format(estimated_settled_orders_count)],['Comission', '{:,}'.format(round(estimated_commission_net_sales,2))], ['Taxes', '{:,}'.format(round(estimated_taxes_net_sales,2))], ['Logistics', '{:,}'.format(round(estimated_logistics_net_sales,2))], ['Fixed-Fee', '{:,}'.format(round(estimated_fixed_fee_net_sales,2))], ['Pick-Pack Fee', '{:,}'.format(round(estimated_pick_pack_net_sales,2))], ['Pay Gate Fee', '{:,}'.format(round(estimated_payment_gateway_net_sales,2))], ['Mktg & Others', '{:,}'.format(round(estimated_mktg_net_sales,2))], ['Settlement', '{:,}'.format(round(estimated_settlement_net_sales,2))], ['COGS', '{:,}'.format(round(estimated_cogs_net_sales,2))], ['P/L', '{:,}'.format(round(estimated_pnl_net_sales,2))]]
            estimated_net_sales_dataframe=pd.DataFrame(estimated_net_sales_data, columns=['Metric', 'Value'])





            with st.container(border=True) :
                
                col1,col2,col3,col4,col5,col6=st.columns(6,gap='small')
                with col1:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 5px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/order_icon.png")
                        with col10:
                
                                st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font"><b>Ordered Value</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(ordered_gmv))+'</p>', unsafe_allow_html=True)

                with col2:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 2px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/cancelled_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font"><b>Cancelled Value</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(cancelled_value))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(cancelled_value/ordered_gmv*100,2))+'%</p>', unsafe_allow_html=True)
                        
                with col3:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 2px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/shipped_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                    
                            st.markdown('<p class="value-font"><b>Shipped Value</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(shipped_value))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(shipped_value/ordered_gmv*100,2))+'%</p>', unsafe_allow_html=True)
                
                with col4:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 2px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/rto_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                    
                            st.markdown('<p class="value-font"><b>RTO Value</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(rto_value))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(rto_value/shipped_value*100,2))+'%</p>', unsafe_allow_html=True)

                with col5:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 2px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/in_transit_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                    
                            st.markdown('<p class="value-font"><b>In Transit Value</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(in_transit_value))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(in_transit_value/shipped_value*100,2))+'%</p>', unsafe_allow_html=True)

                
                with col6:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 2px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/delivered_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                    
                            st.markdown('<p class="value-font"><b>Delivered Value</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(delivered_value))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(delivered_value/shipped_value*100,2))+'%</p>', unsafe_allow_html=True)

            
            st.markdown("")

            with st.container(border=True):
                count=count+1
                with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 20px;
                    margin : 0px;
                    background-color: #77dd77;
                    
                }
                
                """,
        ):
                        st.markdown('<p class="value-font"><b>Delivered Value</b></p>', unsafe_allow_html=True)
                        st.markdown('<p class="value-font">'+('{:,}'.format(delivered_value))+'</p>', unsafe_allow_html=True)
                        
                plcol1,plcol2=st.columns(2,gap='small')
                with plcol1:
                    with st.container(border=True):
                        st.markdown('<p class="value-font"><b>Settled GMV</b></p>', unsafe_allow_html=True)
                        st.markdown('<p class="value-font">'+('{:,}'.format(settled_orders_value))+'</p>', unsafe_allow_html=True)
                        st.markdown('<p class="value-font">'+str(round(settled_orders_value/delivered_value*100,2))+'%</p>', unsafe_allow_html=True)
                    subplcol1,subplcol2=st.columns(2,gap='small')
                    with subplcol1:
                        with st.container(border=True):
                            st.markdown('<p class="value-font"><b>Return GMV</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(settled_orders_value_returns))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(settled_orders_value_returns/settled_orders_value*100,2))+'%</p>', unsafe_allow_html=True)  
                        
                        with st.container(border=True):
                                st.dataframe(returns_dataframe.set_index(returns_dataframe.columns[0]),height=422)
                                # st.markdown(returns_dataframe.style.hide(axis="index").to_html(), unsafe_allow_html=True)
                        
                    with subplcol2:
                        with st.container(border=True):
                            st.markdown('<p class="value-font"><b>Net Sales GMV</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(round(settled_orders_value_net_sales,2)))+'</p>', unsafe_allow_html=True)  
                            st.markdown('<p class="value-font">'+str(round(settled_orders_value_net_sales/settled_orders_value*100,2))+'%</p>', unsafe_allow_html=True)
                        with st.container(border=True):
                                # st.markdown(f"<div style='background-color: green;text-align: center;'>{net_sales_dataframe.style.hide(axis="index").to_html()}</div>",
                                #  unsafe_allow_html=True)
                                # st.markdown(net_sales_dataframe.style.hide(axis="index").to_html(), unsafe_allow_html=True)
                                st.dataframe(net_sales_dataframe.set_index(net_sales_dataframe.columns[0]),height=422)
                    count=count+1
                    with   stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 20px;
                    margin : 0px;
                    background-color: #77dd77;
                    
                }
                
                """,
        ):
                            subplcol1,subplcol2,subplcol3=st.columns(3,gap='small')
                            with subplcol1:
                                st.markdown('<p class="value-font"><b>Settlement</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(round(settlement_net_sales+settlement_return,2)))+'</p>', unsafe_allow_html=True)
                            

                            with subplcol2:
                                st.markdown('<p class="value-font"><b>P/L</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(round(pnl_total,2)))+'</p>', unsafe_allow_html=True)
                            
                            with subplcol3:
                                st.markdown('<p class="value-font"><b>ROI</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+str(round(pnl_total/cogs_net_sales*100,2))+'%</p>', unsafe_allow_html=True)  
                        
                with plcol2:
                    with st.container(border=True):
                        st.markdown('<p class="value-font"><b>Non-Settled GMV</b></p>', unsafe_allow_html=True)
                        st.markdown('<p class="value-font">'+('{:,}'.format(non_settled_orders_value))+'</p>', unsafe_allow_html=True)
                        st.markdown('<p class="value-font">'+str(round(non_settled_orders_value/delivered_value*100,2))+'%</p>', unsafe_allow_html=True)

                    subplcol1,subplcol2=st.columns(2,gap='small')
                    with subplcol1:
                        with st.container(border=True):
                            st.markdown('<p class="value-font"><b>Estimated Return GMV</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(round(settled_orders_value_returns/settled_orders_value*non_settled_orders_value,2)))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">Actuals may vary</p>', unsafe_allow_html=True)
                        with st.container(border=True):
                                st.dataframe(estimated_returns_dataframe.set_index(estimated_returns_dataframe.columns[0]),height=422)
                                # st.markdown(estimated_returns_dataframe.style.hide(axis="index").to_html(), unsafe_allow_html=True)
                        
                    with subplcol2:
                        with st.container(border=True):
                            st.markdown('<p class="value-font"><b>Estimated Net Sales GMV</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(round(settled_orders_value_net_sales/settled_orders_value*non_settled_orders_value,2)))+'</p>', unsafe_allow_html=True)  
                            st.markdown('<p class="value-font">Actuals may vary</p>', unsafe_allow_html=True)
                        with st.container(border=True):
                                st.dataframe(estimated_net_sales_dataframe.set_index(estimated_net_sales_dataframe.columns[0]),height=422)
                                # st.markdown(estimated_net_sales_dataframe.style.hide(axis="index").to_html(), unsafe_allow_html=True)

                    count=count+1
                    with   stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 20px;
                    margin : 0px;
                    background-color: #FFC067;
                    
                }
                
                """,
        ):
                            subplcol1,subplcol2=st.columns(2,gap='small')
                            with subplcol1:
                                st.markdown('<p class="value-font"><b>Estimated Settlement</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(round(estimated_settlement_net_sales+estimated_settlement_return,2)))+'</p>', unsafe_allow_html=True)
                            
                            with subplcol2:
                                st.markdown('<p class="value-font"><b>Estimated P/L</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(round(estimated_pnl_total,2)))+'</p>', unsafe_allow_html=True)
                            
            # with st.container(border=True):
            #     st.subheader("ASP-Settlement Co-relation")
            #     db_data_scatter=db_data
            #     db_data_scatter['order_created_date']=db_data_scatter['order_created_date'].dt.date
            #     db_data_scatter['order_created_date']=db_data_scatter['order_created_date'].astype(str)
            #     db_data_scatter=db_data_scatter.groupby(['order_created_date']).agg({'total_actual_settlement':'sum','customer_paid_amt':'mean'}) 
            #     db_data_scatter.reset_index(inplace=True)

            #     c = np.corrcoef(db_data_scatter['customer_paid_amt'],db_data_scatter['total_actual_settlement'])
            #     fig = px.imshow(c, text_auto=True,x=['ASP','Settlement_Amount'],y=['ASP','Settlement_Amount'])
            #     st.plotly_chart(fig, theme="streamlit")

            with st.container(border=True):
                db_data_monthly=db_data_pnl[['order_created_date','order_type','customer_paid_amt','total_actual_settlement','platform_fees','tcs_amount','tds_amount','shipping_fee','pick_and_pack_fee','fixed_fee','payment_gateway_fee','total_tax_on_logistics','returns','cost']]
                db_data_monthly.loc[db_data_monthly['returns']==1,'platform_fees']=0
                db_data_monthly.loc[db_data_monthly['returns']==1,'tcs_amount']=0
                db_data_monthly.loc[db_data_monthly['returns']==1,'tds_amount']=0
                db_data_monthly['final_amount']=db_data_monthly['customer_paid_amt']
                db_data_monthly.loc[db_data_monthly['order_type']=='Reverse','final_amount']=0
                db_data_monthly.loc[db_data_monthly['returns']==1,'customer_paid_amt']=0
                db_data_monthly.loc[db_data_monthly['returns']==1,'cost']=0
                
                db_data_monthly['settlement']=db_data_monthly['customer_paid_amt']-db_data_monthly['platform_fees']-db_data_monthly['tcs_amount']-db_data_monthly['tds_amount']-db_data_monthly['shipping_fee']-db_data_monthly['pick_and_pack_fee']-db_data_monthly['fixed_fee']-db_data_monthly['payment_gateway_fee']-db_data_monthly['total_tax_on_logistics']
                db_data_monthly['month']=pd.to_datetime(db_data_monthly['order_created_date']).dt.strftime('%b-%y')
                db_data_monthly.sort_values(by=['order_created_date'],inplace=True)
                
                db_data_monthly.drop(['returns','total_actual_settlement','order_created_date','total_actual_settlement','platform_fees','tcs_amount','tds_amount','shipping_fee','pick_and_pack_fee','fixed_fee','payment_gateway_fee','total_tax_on_logistics'],inplace=True,axis=1)
                
                db_data_monthly=db_data_monthly.groupby(['month'], sort=False, as_index=False).agg({'final_amount':'sum','customer_paid_amt':'sum','settlement':'sum','cost':'sum'})
                
                db_data_monthly['P/L']=db_data_monthly['settlement']-db_data_monthly['cost']
                
                db_data_monthly.rename(columns={'final_amount':'Delivered_Value','customer_paid_amt':'Net_Sales_Value'},inplace=True)
                fig = px.line(title="MOM P/L")
                #    update_traces  
                fig.add_scatter(x=db_data_monthly['month'], y=db_data_monthly['Delivered_Value'],name="Settled Sales Value")
                fig.add_scatter(x=db_data_monthly['month'], y=db_data_monthly['Net_Sales_Value'],name="Net Sales_Value")
                fig.add_scatter(x=db_data_monthly['month'], y=db_data_monthly['settlement'],name="Settlement")
                fig.add_scatter(x=db_data_monthly['month'], y=db_data_monthly['cost'],name="COGS")
                fig.add_scatter(x=db_data_monthly['month'], y=db_data_monthly['P/L'],name="P/L")
                count=count+1
                st.plotly_chart(fig, theme="streamlit", key=str(count))
                

            