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

# Displaying Title and Final Data
st.title("💹 Sales Overview")
db_data_final = db_data
db_sales_data_final = db_sales_data

total_channel = db_sales_data['channel_x'].unique().tolist()
total_channel.insert(0, "All")


with stylable_container(
        key="main",
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
                db_data_so=db_data_final
                db_sales_data_so=db_sales_data_final
            else :
                db_data_so=db_data_final[db_data_final['channel']==total_channel[i]]
                db_sales_data_so=db_sales_data_final[db_sales_data_final['channel_x']==total_channel[i]]
            
            container=st.container(border=True)
            container1=st.container(border=True)

            db_data_forward=db_data_so[db_data_so['order_type']=='Forward']
            db_data_reverse=db_data_so[db_data_so['order_type']=='Reverse']
            total_orders=len(db_sales_data_so)
            cancelled_orders=len(db_sales_data_so[db_sales_data_so['order_status']=='F'])
            shipped_orders=total_orders-cancelled_orders
            RTO=len(db_sales_data_so[db_sales_data_so['order_status']=='RTO'])
            in_transit=len(db_sales_data_so[db_sales_data_so['order_status'].isin({'SH','L','PK','WP'})])
            delivered=shipped_orders-RTO-in_transit
            total_returns=len(db_sales_data_so[db_sales_data_so['returns']==1])
            successful_order=delivered-total_returns
            db_sales_value=db_sales_data_so[db_sales_data_so['returns']==0]
            db_sales_value=db_sales_value[db_sales_value['order_status']=='C']
            total_sales_value=sum(db_sales_value['final_amount'])
            profit=sum(db_data_forward['customer_paid_amt'])


            with st.container(border=True) :
                
                col1,col2,col3,col4,col5,col6,col7,col8=st.columns(8,gap='small')
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
                            st.markdown('<p class="value-font"><b>Orders</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(total_orders))+'</p>', unsafe_allow_html=True)

                with col2:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 10px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/cancelled_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"><b>Cancelled</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(cancelled_orders))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(cancelled_orders/total_orders*100,2))+'%</p>', unsafe_allow_html=True)
                        
                with col3:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 10px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/shipped_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"><b>Shipped</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(shipped_orders))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(shipped_orders/total_orders*100,2))+'%</p>', unsafe_allow_html=True)
                
                with col4:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 10px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/rto_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"><b>RTO</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(RTO))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(RTO/shipped_orders*100,2))+'%</p>', unsafe_allow_html=True)

                with col5:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 10px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/in_transit_icon.png")
                        with col10:
                            st.markdown('<p class="value-font"><b>In Transit</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(in_transit))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(in_transit/shipped_orders*100,2))+'%</p>', unsafe_allow_html=True)

                
                with col6:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 10px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/return_icon.png")
                        with col10:
                         st.markdown('<p class="value-font"><b>Returns</b></p>', unsafe_allow_html=True)
                         st.markdown('<p class="value-font">'+('{:,}'.format(total_returns))+'</p>', unsafe_allow_html=True)
                         st.markdown('<p class="value-font">'+str(round(total_returns/shipped_orders*100,2))+'%</p>', unsafe_allow_html=True)

                with col7:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 10px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/net_sales_icon.png")
                        with col10:
                            st.markdown('<p class="box-font"><b>Net Sales</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(successful_order))+'</p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+str(round(successful_order/shipped_orders*100,2))+'%</p>', unsafe_allow_html=True)



                with col8:
                    count=count+1
                    with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 10px;
                    margin : 0px;
                    
                }
                
                """,
        ):
                        col9,col10=st.columns([2,3.5],gap="small")
                        with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                            st.image("assets/sales_value_icon.png", width=30)
                        with col10:
                            st.markdown('<p class="box-font"><b>Sales Value</b></p>', unsafe_allow_html=True)
                            st.markdown('<p class="value-font">'+('{:,}'.format(total_sales_value))+'</p>', unsafe_allow_html=True)

            with st.container(border=True) :
                    st.subheader("Sales Trend (Shipped Orders)")
                    # db_sales_data_daily=db_sales_data[db_sales_data['order_status']!='F']
                    # db_sales_data_daily['order_created_date']=db_sales_data_daily['order_created_date'].dt.date
                    # db_sales_data_daily['order_created_date']=db_sales_data_daily['order_created_date'].astype(str)
                    # db_sales_data_daily['asp']=db_sales_data_daily['final_amount']
                    # db_sales_data_daily=db_sales_data_daily.groupby(['order_created_date']).agg({'final_amount':'sum','asp':'mean','order_release_id':'count'})
                    # db_sales_data_daily.reset_index(inplace=True)
                    # db_sales_data_daily.set_index('order_created_date',inplace=True)
                    # st.line_chart(data=db_sales_data_daily, x=None, y=['final_amount'], x_label='Date', y_label='Sales_Value', color=None, width=None, height=None, use_container_width=True)
                    # st.bar_chart(data=db_sales_data_daily, x=None, y=['asp'], x_label='Date', y_label='ASP', color=None, width=None, height=None, use_container_width=True)
                    
                    db_sales_data_daily=db_sales_data_so[db_sales_data_so['order_status']!='F']
                    db_sales_data_daily['order_created_date']=db_sales_data_daily['order_created_date'].dt.date
                    db_sales_data_daily['asp']=db_sales_data_daily['final_amount']
                    db_sales_data_daily=db_sales_data_daily.groupby(['order_created_date']).agg({'final_amount':'sum','asp':'mean','order_release_id':'count'})
                    db_sales_data_daily.reset_index(inplace=True)
                    db_sales_data_daily.set_index('order_created_date',inplace=True)
                    


                    fig, ax = plt.subplots(1, figsize=(15,5))
                    ax_2 = ax.twinx()
                    ax.set_xlabel('Date')
                    # ax.set_xticklabels('Date',rotation = 90)
                    ax.set_ylabel('Sales Value',color='darkturquoise')
                    ax_2.set_ylabel('ASP',color='red')
                    ax_2.plot(db_sales_data_daily.index, db_sales_data_daily['asp'],color='red')
                    ax_2.tick_params(axis='y', labelcolor='red')
                    ax.bar(db_sales_data_daily.index, db_sales_data_daily['final_amount'],color='darkturquoise')
                    ax.tick_params(axis='y', labelcolor='darkturquoise')
                    # fig.tight_layout()
                    st.pyplot(fig)


            with st.container(border=True):
                st.subheader("Contributions")
                st.divider()
                tab1,tab2,tab3,tab4,tab5=st.tabs(['👕 Category','🔠 Brand','⚧️ Gender','🗺️ State','📏 Size'])



                with tab1 :
                
                    # st.subheader("Category Contribution")
                    db_sales_category=db_sales_data_so[db_sales_data_so['order_status']!='F']
                    db_sales_category=db_sales_category.groupby(['article_type']).agg({'final_amount':'sum'})
                    db_sales_category.reset_index(inplace=True)

                    fig=px.pie(db_sales_category,values='final_amount',names='article_type',title=None)
                    # fig = go.Figure(data=[go.Pie(labels=db_sales_category['article_type'], values=db_sales_category['final_amount'])])
                    count=count+1
                    st.plotly_chart(fig,use_container_width=True,key=str(count))
                    

                with tab2 :
                
                    # st.subheader("Brand Contribution")
                    db_sales_brand=db_sales_data_so[db_sales_data_so['order_status']!='F']
                    db_sales_brand=db_sales_brand.groupby(['brand']).agg({'final_amount':'sum'})
                    db_sales_brand.reset_index(inplace=True)

                    fig1=px.pie(db_sales_brand,values='final_amount',names='brand',title=None)
                    count=count+1
                    st.plotly_chart(fig1,use_container_width=True,key=str(count))
                    


                with tab3 :
                
                    # st.subheader("Gender Contribution")
                    db_sales_brand=db_sales_data_so[db_sales_data_so['order_status']!='F']
                    db_sales_brand=db_sales_brand.groupby(['gender']).agg({'final_amount':'sum'})
                    db_sales_brand.reset_index(inplace=True)

                    fig2=px.pie(db_sales_brand,values='final_amount',names='gender',title=None)
                    count=count+1
                    st.plotly_chart(fig2,use_container_width=True,key=str(count))
                    


                    
                with tab4 :
                    db_sales_latlong=db_sales_data_so[db_sales_data_so['order_status']!='F']
                    db_sales_latlong=db_sales_latlong.groupby(['state']).agg({'final_amount':'sum'})
                    db_sales_latlong.reset_index(inplace=True)
                    size=db_sales_latlong['final_amount'].max()
                    db_sales_latlong['amount']=db_sales_latlong['final_amount']/size*200000
                    db_sales_latlong=db_sales_latlong.merge(db_latlong,left_on='state',right_on='state')

                    st.map(db_sales_latlong, latitude='lat', longitude='lon',size='amount')
                    
                with tab5 :
                
                    # st.subheader("Size Contribution")
                    db_sales_brand=db_sales_data_so[db_sales_data_so['order_status']!='F']
                    db_sales_brand=db_sales_brand.groupby(['size']).agg({'final_amount':'sum'})
                    db_sales_brand.reset_index(inplace=True)
                    count0=0
                    count0
                    fig3=px.pie(db_sales_brand,values='final_amount',names='size',title=None)
                    count=count+1
                    st.plotly_chart(fig3,use_container_width=True,key=str(count))
                    