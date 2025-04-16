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
st.cache_data.clear()
from db import db_data, db_sales_data, db_sales_data_for_side_filter, db_latlong, get_sidebar_data, get_actions_data, insert_df_to_db

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






st.title ("👕 Style Review")
db_data_sr=db_data
db_sales_data_sr=db_sales_data


db_data_forward=db_data_sr[db_data_sr['order_type']=='Forward']
# db_data_reverse=db_data[db_data['order_type']=='Reverse']
# db_sales_data=db_sales_data[db_sales_data['order_status']=='C']

# db_vendor_style_code=db_data[['vendor_style_code','image_link','brand','gender','article_type','color','fabric','cost']]
# db_vendor_style_code=db_vendor_style_code.drop_duplicates()

db_search_style_code=db_sales_data_sr['vendor_style_code'].drop_duplicates()
search_style_code_list = db_search_style_code.values.tolist()
search_style_code = st.multiselect(
    "Search/Select Style Code",
    search_style_code_list,
    placeholder="Search/Select Style Code",
    label_visibility='collapsed'
    )

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
    if len(search_style_code)>0 :
        db_style_code=db_data_sr[(db_data_sr['vendor_style_code'].isin(search_style_code))]

        st.session_state['page_number'] = 1
    else :
        db_style_code=db_data_sr

    db_style_code['order_count']=0
    db_style_code.loc[db_style_code['order_type']=='Forward','order_count']=1
    db_style_code.loc[db_style_code['returns']==1,'cost']=0
    db_style_code.loc[db_style_code['returns']==1,'customer_paid_amt']=0
    db_style_code.loc[db_style_code['returns']==1,'platform_fees']=0
    db_style_code.loc[db_style_code['returns']==1,'tcs_amount']=0
    db_style_code.loc[db_style_code['returns']==1,'tds_amount']=0
    db_style_code['return_count']=0
    db_style_code.loc[(db_style_code['returns']==1)&(db_style_code['order_type']=='Forward'),'return_count']=1
    db_style_code['month']=pd.to_datetime(db_style_code['order_created_date']).dt.strftime('%b-%y')
    db_style_code_funnel=db_style_code


    db_style_code['settlement']=db_style_code['customer_paid_amt']-db_style_code['platform_fees']-db_style_code['tcs_amount']-db_style_code['tds_amount']-db_style_code['shipping_fee']-db_style_code['pick_and_pack_fee']-db_style_code['fixed_fee']-db_style_code['payment_gateway_fee']-db_style_code['total_tax_on_logistics']
    db_style_code.sort_values(by=['order_created_date'],inplace=True)

    db_style_code.fillna(0,inplace=True)
    db_style_code['state'] = db_style_code['state'].astype(str)
    db_style_code['order_type'] = db_style_code['order_type'].astype(str)
    db_style_code['channel'] = db_style_code['channel'].astype(str)
    db_style_code['vendor_style_code'] = db_style_code['vendor_style_code'].astype(str)
    db_style_code['brand'] = db_style_code['brand'].astype(str)
    db_style_code['gender'] = db_style_code['gender'].astype(str)
    db_style_code['article_type'] = db_style_code['article_type'].astype(str)
    db_style_code['color'] = db_style_code['color'].astype(str)
    db_style_code['collection'] = db_style_code['collection'].astype(str)
    db_style_code['month'] = db_style_code['month'].astype(str)
    db_style_code['size'] = db_style_code['size'].astype(str)

    db_style_code['returns'] = pd.to_numeric(db_style_code['returns'], errors='coerce')
    db_style_code['customer_paid_amt'] = pd.to_numeric(db_style_code['customer_paid_amt'], errors='coerce')
    db_style_code['order_count'] = pd.to_numeric(db_style_code['order_count'], errors='coerce')
    db_style_code['settlement'] = pd.to_numeric(db_style_code['settlement'], errors='coerce')
    db_style_code['return_count'] = pd.to_numeric(db_style_code['return_count'], errors='coerce')
    db_style_code['cost'] = pd.to_numeric(db_style_code['cost'], errors='coerce')
    db_style_code['total_actual_settlement'] = pd.to_numeric(db_style_code['total_actual_settlement'], errors='coerce')


    # Ensure there are no NaN values in columns before performing the groupby
    db_style_code.fillna(0,inplace=True)
    
    
    db_style_code=db_style_code.groupby(['state','order_type','channel','vendor_style_code','order_created_date','brand','gender','article_type','image_link','color','collection','month','size'], as_index=False,sort=False).agg({'returns':'sum','customer_paid_amt':'sum','order_count':'sum','settlement':'sum','return_count':'sum','cost':'sum','total_actual_settlement':'sum'})

    db_style_code['p/l']=db_style_code['total_actual_settlement']-db_style_code['cost']
    db_style_code=db_style_code.merge(db_latlong,left_on='state',right_on='state')
    # db_style_code['order_count']=db_style_code['vendor_style_code'].map(db_data_forward['vendor_style_code'].value_counts())
    db_style_code_for_sequence=db_style_code.groupby(['vendor_style_code'],as_index=False,sort=False).agg({'order_count':'sum'})

    db_style_code_for_sequence=db_style_code_for_sequence.sort_values('order_count',ascending=False)
    db_style_code_for_sequence.reset_index(inplace=True)
    db_style_code_for_sequence.drop(['index'],axis=1,inplace=True)
    db_style_code_for_sequence.index +=1
    db_style_code_for_sequence.fillna(0,inplace=True)


    # db_sales_data=db_sales_data.drop(['order_release_id','sku_code_x','channel_y','sku_code_y','vendor_sku_code'],axis=1)
    # db_sales_data['order_count']=1
    total_pages=len(db_style_code_for_sequence)



    if 'page_number' not in st.session_state:
        st.session_state['page_number'] = 1
    else:
        page_number = st.session_state['page_number']

    count=count+1
    with stylable_container(
        key=str(count),
        css_styles="""
            {
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: 5px;
                margin : 0px;
                line-height: 0%;
                
            }
            
            """,
    ):
        
        col1,col2=st.columns([4,1],gap="small")
        with col2 :
            subcol1,subcol2,subcol3,subcol4=st.columns([2,3,3,2],gap='small')

            with subcol1 :
                if st.button("⬅️", use_container_width=True):
                    st.session_state['page_number'] -= 1 
                if st.session_state['page_number']==0 :
                    st.session_state['page_number']=total_pages
            with subcol4 :
                if st.button("➡️", use_container_width=True):
                    st.session_state['page_number'] += 1 
                if st.session_state['page_number']==total_pages+1 :
                    st.session_state['page_number']=1
            with subcol2:
                page_number = st.number_input("",value=st.session_state['page_number'],min_value=1, max_value=total_pages,label_visibility='collapsed')
                st.session_state['page_number']=page_number
            with subcol3:
                st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                st.write("/"+str(total_pages))    


        
        
        db_style_code_display_final=db_style_code[db_style_code['vendor_style_code']==db_style_code_for_sequence.loc[st.session_state['page_number'],'vendor_style_code']]
        db_style_code_display_final.reset_index(inplace=True)
        
        
        total_channel=db_style_code_display_final['channel'].unique().tolist()

        total_channel.insert(0, "All")
        tab=st.tabs(total_channel)
        tab_len=len(total_channel)

        
        for i in range(tab_len):
                with tab[i]:
                    if i==0 :
                        db_style_code_display=db_style_code_display_final
                        db_style_code_funnel=db_style_code_funnel
                # db_sales_data=db_sales_data_final
                    else :
                        db_style_code_display=db_style_code_display_final[db_style_code_display_final['channel']==total_channel[i]]
                        db_style_code_funnel=db_style_code_funnel[db_style_code_funnel['channel']==total_channel[i]]
                # db_sales_data=db_sales_data_final[db_sales_data_final['channel_x']==total_channel[i]]  
                
                    subcol1,subcol2,subcol3,subcol4,subcol5=st.columns(5,gap="small")
                    orders=db_style_code_display['order_count'].sum()
                    returns=db_style_code_display['return_count'].sum()
                    db_style_net_sales=orders-returns
                    value=db_style_code_display['customer_paid_amt'].sum()



                    db_style_code_display_unit=db_style_code_display.groupby(['vendor_style_code','channel','brand','gender','article_type'],as_index=False).agg({'order_count':'sum','return_count':'sum','cost':'sum','p/l':'sum','customer_paid_amt':'sum'})
                    db_style_code_display_unit['net_order']=db_style_code_display_unit['order_count']-db_style_code_display_unit['return_count']
                    db_style_code_display_unit['asp']=db_style_code_display_unit['customer_paid_amt']/db_style_code_display_unit['net_order']
                    db_style_code_display_unit['cogs']=db_style_code_display_unit['cost']/db_style_code_display_unit['net_order']
                    db_style_code_display_unit['codb']=(db_style_code_display_unit['customer_paid_amt']-db_style_code_display_unit['cost']-db_style_code_display_unit['p/l'])/db_style_code_display_unit['net_order']
                    # db_style_code_display_unit.drop(['order_count','return_count','cost','p/l','customer_paid_amt','net_order'],axis=1,inplace=True)
                    db_style_code_display_unit['p/l']=db_style_code_display_unit['asp']-db_style_code_display_unit['codb']-db_style_code_display_unit['cogs']
                    db_style_code_actions=db_style_code_display.groupby(['vendor_style_code','channel','brand','gender','article_type'],as_index=False).agg({'order_created_date':'min','order_count':'sum','return_count':'sum','cost':'sum','p/l':'sum'})
                    db_style_code_actions['return %']=db_style_code_actions['return_count']/db_style_code_actions['order_count']
                    db_style_code_actions['roi']=db_style_code_actions['p/l']/db_style_code_actions['cost']
                    db_style_code_actions['ros']=(db_style_code_actions['order_count'])/(pd.to_datetime(datetime.date.today(),format='ISO8601')-db_style_code_actions['order_created_date']).dt.days
            

                    #   db_style_data['order_count']=1
                
                    with subcol1:
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
                            col8,col9,col10,col11=st.columns([1,2,4,1],gap="small")
                            with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                                st.image("assets/order_icon.png")
                            with col10:
                
                                st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font"><b>Orders</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(round(orders),0))+'</p>', unsafe_allow_html=True)
                        
                    with subcol2:
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
                            col8,col9,col10,col11=st.columns([1,2,4,1],gap="small")
                            with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                                st.image("assets/return_icon.png")
                            with col10:
                
                                st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font"><b>Returns</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(round(returns),0))+'</p>', unsafe_allow_html=True)

                    with subcol3:
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
                            col8,col9,col10,col11=st.columns([1,2,4,1],gap="small")
                            with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                                st.image("assets/delivered_icon.png")
                            with col10:
                
                                st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font"><b>Net Orders</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(round(orders-returns),0))+'</p>', unsafe_allow_html=True)

                    with subcol4:
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
                            col8,col9,col10,col11=st.columns([1,2,4,1],gap="small")
                            with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                                st.image("assets/sales_value_icon.png")
                            with col10:
                
                                st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font"><b>Value</b></p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font">'+('{:,}'.format(round(value),0))+'</p>', unsafe_allow_html=True)

                    with subcol5:
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
                            col8,col9,col10,col11=st.columns([1,2,4,1],gap="small")
                            with col9 :

                            # st.markdown('<p class="value-font"><b></b></p>', unsafe_allow_html=True)
                            
                                st.image("assets/rto_icon.png")
                            with col10:
                
                                st.markdown('<p class="value-font"> </p>', unsafe_allow_html=True)
                                st.markdown('<p class="value-font"><b>Return %</b></p>', unsafe_allow_html=True)
                                try:
                                    st.markdown('<p class="value-font">'+str(round(db_style_code_actions['return %'][0]*100,2))+'%</p>', unsafe_allow_html=True)
                                except:
                                    st.markdown('<p class="value-font"> error </p>', unsafe_allow_html=True)

                    


                  




                    col3,col4=st.columns([0.65,2],gap="small")
                    with col3:
                        with st.container(border=True):
                            try:
                            
                                st.image(db_style_code_display['image_link'][0], width=250)
                                st.subheader(db_style_code_display['vendor_style_code'][0])
                            except: 
                                st.text("Please check image url")
                        
                    with col4:
                      count=count+1
                      with stylable_container(
            key=str(count),
            css_styles="""
                {
                    border: 2px solid rgba(49, 51, 63, 0.2);
                    border-radius: 0.5rem;
                    padding: 5px;
                    margin : 0px;
                    height: 355px;
                    
                }
                
                """,
        ):  
                        
                        if i==0:
                            tab1,tab2,tab3,tab4,tab5,tab6,tab7=st.tabs(['Orders-return','p/l','State Distribution','Size Contribution','Channel Contribution','CODB','Suggested Actions'])
                        else :
                            tab1,tab2,tab3,tab4,tab6=st.tabs(['Orders-return','p/l','State Distribution','Size Contribution','CODB'])

                        with tab1:
                            db_style_code_display_tab=db_style_code_display.groupby(['month'], as_index=False,sort=False).agg({'order_count':'sum','return_count':'sum'})
                            db_style_code_display_tab['net_order_count']=db_style_code_display_tab['order_count']-db_style_code_display_tab['return_count']
                            
                            fig = px.line(height=320)
                            
                            fig.add_scatter(x=db_style_code_display_tab['month'], y=db_style_code_display_tab['order_count'],name="Total orders")
                            fig.add_scatter(x=db_style_code_display_tab['month'], y=db_style_code_display_tab['return_count'],name="Returns")
                            fig.add_scatter(x=db_style_code_display_tab['month'], y=db_style_code_display_tab['net_order_count'],name="Net Sales")
                            count=count+1
                            st.plotly_chart(fig, theme="streamlit",key=str(count))
                            

                        with tab2:
                            db_style_code_display_tab=db_style_code_display.groupby(['month'], as_index=False,sort=False).agg({'customer_paid_amt':'sum','total_actual_settlement':'sum','cost':'sum','p/l':'sum'})
                            
                            fig = px.line(height=320)
                            
                            fig.add_scatter(x=db_style_code_display_tab['month'], y=db_style_code_display_tab['customer_paid_amt'],name="Net Sales")
                            fig.add_scatter(x=db_style_code_display_tab['month'], y=db_style_code_display_tab['total_actual_settlement'],name="Settlement Amount")
                            fig.add_scatter(x=db_style_code_display_tab['month'], y=db_style_code_display_tab['cost'],name="COGS")
                            fig.add_scatter(x=db_style_code_display_tab['month'], y=db_style_code_display_tab['p/l'],name="P/L")
                            # with st.container(height=355):
                            count=count+1
                            st.plotly_chart(fig, theme="streamlit",key=str(count))
                           

                        with tab3:
                            db_style_code_display_tab=db_style_code_display.groupby(['latitude','longitude','state'], as_index=False,sort=False).agg({'order_count':'sum','return_count':'sum'})
                            db_style_code_display_tab['net_order_count']=db_style_code_display_tab['order_count']-db_style_code_display_tab['return_count']
                            size=db_style_code_display_tab['net_order_count'].max()
                            db_style_code_display_tab['amount']=db_style_code_display_tab['net_order_count']/size*200000
                            # with st.container(height=355):
                            st.map(db_style_code_display_tab, latitude='latitude', longitude='longitude',size='amount')
                            # fig = px.scatter_geo(db_style_code_display_tab, lat='latitude', lon='longitude',hover_name='state', size='amount',title=None,color='net_order_count')
                            
                            # fig.show()

                        with tab4:
                            db_style_code_display_tab=db_style_code_display.groupby(['size'], as_index=False,sort=False).agg({'order_count':'sum','return_count':'sum'})
                            db_style_code_display_tab['net_order_count']=db_style_code_display_tab['order_count']-db_style_code_display_tab['return_count']
                            
                            
                            fig=px.pie(db_style_code_display_tab,values='net_order_count',names='size',title=None,height=320)
                            # with st.container(height=355):
                            count=count+1
                            st.plotly_chart(fig,use_container_width=True,key=str(count))
                           

                        if i==0:
                            with tab5:
                                db_style_code_display_tab=db_style_code_display.groupby(['channel'], as_index=False,sort=False).agg({'order_count':'sum','return_count':'sum'})
                                db_style_code_display_tab['net_order_count']=db_style_code_display_tab['order_count']-db_style_code_display_tab['return_count']
                            
                            
                                fig=px.pie(db_style_code_display_tab,values='net_order_count',names='channel',title=None,height=320)
                                # with st.container(height=355):
                                count=count+1
                                st.plotly_chart(fig,use_container_width=True,key=str(count))
                                

                             
                                
                        else:
                            with tab7: 
                                db_styles_action, db_actual_action, db_accepted_actions,selling_price_list,pla_list,replenishment_list=get_actions_data()
                                # db_styles_action=master_conn.query("select * from actions_upload;")
                                # db_actual_action=master_conn.query("select * from recommendation_upload")
                                
                                # selling_price_list=master_conn.query("select distinct selling_price from recommendation_upload")
                                selling_price_list=selling_price_list['selling_price'].values.tolist()
                                # pla_list=master_conn.query("select distinct pla from recommendation_upload")
                                pla_list=pla_list['pla'].values.tolist()
                                # replenishment_list=master_conn.query("select distinct replenishment from recommendation_upload")
                                replenishment_list=replenishment_list['replenishment'].values.tolist()
                                total_channel=db_style_code_display_final['channel'].unique().tolist()
                                tab_suggestion=st.tabs(total_channel)
                                tab_len=len(total_channel)

                                
                                
                                
                                

                                for i in range(tab_len):
                                    with tab_suggestion[i]:
                                            

                                            db_style_code_actions_tab=db_style_code_actions[db_styles_action['channel']==total_channel[i]]
                                            
                                            db_styles_action_tab=db_styles_action[(db_styles_action['brand']==db_style_code_display.loc[0,'brand'])&(db_styles_action['gender']==db_style_code_display['gender'][0])&(db_styles_action['article_type']==db_style_code_display['article_type'][0])]
                                            
                                            if db_style_code_actions_tab['ros'].sum()>=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='ros','a'].sum() :
                                                ros_action="A"
                                            elif db_style_code_actions_tab['ros'].sum()>=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='ros','b'].sum() :
                                                ros_action="B"
                                            else :
                                                ros_action="C"
                                            
                                            if db_style_code_actions_tab['roi'].sum()>=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='roi','a'].sum() :
                                                roi_action="A"
                                            elif db_style_code_actions_tab['roi'].sum()>=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='roi','b'].sum() :
                                                roi_action="B"
                                            else :
                                                roi_action="C"

                                            if db_style_code_actions_tab['return %'].sum()<=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='return %','a'].sum() :
                                                return_action="A"
                                            elif db_style_code_actions_tab['return %'].sum()<=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='return %','b'].sum() :
                                                return_action="B"
                                            else :
                                                return_action="C"
                                            # db_sales_data.loc[db_sales_data['order_status']=='F','final_amount'].sum()
                                            # ros_action
                                            # roi_action
                                            # return_action
                                            # db_styles_action_tab
                                            
                                            db_actual_action_final=db_actual_action[(db_actual_action['ros']==ros_action)&(db_actual_action['roi']==roi_action)&(db_actual_action['return %']==return_action)]  
                                            
                                            db_actual_action_final.reset_index(inplace=True)
                                            
                                            
                                            # db_style_code_actions_tab
                                            # db_style_code_display_unit
                                            
                                            with st.container(border=True):
                                                subcolm1,subcolm2,subcol3=st.columns([1,3,1])    
                                                with subcolm1:
                                                    st.markdown('<p class="small-font"></p>', unsafe_allow_html=True)
                                                    st.markdown('<p class="small-font">Selling Price</p>', unsafe_allow_html=True)
                                                with subcolm2:
                                                    action_sp=st.selectbox("Select",selling_price_list,index=selling_price_list.index(db_actual_action_final.loc[0,'selling_price']),label_visibility='collapsed')
                                                    
                                            with st.container(border=True):
                                                subcolm1,subcolm2,subcol3=st.columns([1,3,1])
                                                with subcolm1:
                                                    st.markdown('<p class="small-font"></p>', unsafe_allow_html=True)
                                                    st.markdown('<p class="small-font">PLA</p>', unsafe_allow_html=True)
                                                with subcolm2:
                                                    
                                                    action_pla=st.selectbox("Select",pla_list,index=pla_list.index(db_actual_action_final.loc[0,'pla']),label_visibility='collapsed')   
                                            
                                            with st.container(border=True):
                                                subcolm1,subcolm2,subcol3=st.columns([1,3,1])
                                                with subcolm1:
                                                    st.markdown('<p class="small-font"></p>', unsafe_allow_html=True)
                                                    st.markdown('<p class="small-font">Replenishment</p>', unsafe_allow_html=True)
                                                with subcolm2:
                                                    
                                                    action_replenishment=st.selectbox("Select",replenishment_list,index=replenishment_list.index(db_actual_action_final.loc[0,'replenishment']),label_visibility='collapsed')   

                                            with st.container(border=True):
                                                subcolm1,subcolm2,subcol3=st.columns([1,3,1])
                                                with subcolm1:
                                                    st.markdown('<p class="small-font"></p>', unsafe_allow_html=True)
                                                    st.markdown('<p class="small-font">Remarks</p>', unsafe_allow_html=True)
                                                with subcolm2:
                                                    if db_actual_action_final.loc[0,'remarks']==None:
                                                        db_actual_action_final.loc[0,'remarks']="no remarks"
                                                    action_remarks=st.text_input("textbox",value=db_actual_action_final.loc[0,'remarks'],max_chars=None,label_visibility='collapsed')
                                                    # action_replenishment=st.selectbox("Select",replenishment_list,index=replenishment_list.index(db_actual_action_final.loc[0,'replenishment']),label_visibility='collapsed')   

                                            

                                            brand=db_style_code_actions_tab['brand'][0]
                                            gender=db_style_code_actions_tab['gender'][0]
                                            article_type=db_style_code_actions_tab['article_type'][0]
                                            channel=db_style_code_actions_tab['channel'][0]
                                            ros=db_style_code_actions_tab['ros'][0]
                                            roi=db_style_code_actions_tab['roi'][0]
                                            returns=db_style_code_actions_tab['return %'][0]
                                            db_action_items_manual_1=db_style_code_actions_tab.drop(['order_created_date','order_count','return_count','cost','p/l'],axis=1)
                                            
                                            if st.button("Accept Actions ✅"):
                                                
                                                    # db_action_items_manual=db_accepted_actions
                                                    
                                                    db_action_items_manual_1=db_style_code_actions_tab.drop(['order_created_date','order_count','return_count','cost','p/l'],axis=1)
                                                    db_action_items_manual_1.rename(columns={'return %': 'returns'},inplace=True)
                                                    style_code=db_style_code_actions_tab['vendor_style_code'][0]
                                                    db_action_items_manual_1['ros_action']=ros_action
                                                    db_action_items_manual_1['roi_action']=roi_action
                                                    db_action_items_manual_1['return_action']=return_action
                                                    db_action_items_manual_1['selling_price']=action_sp
                                                    db_action_items_manual_1['pla']=action_pla
                                                    db_action_items_manual_1['replenishment']=action_replenishment
                                                    db_action_items_manual_1['remarks']=action_remarks
                                                    db_action_items_manual_1['date_updated']=pd.to_datetime(datetime.date.today(),dayfirst=True, format='mixed')
                                                    # conn.append_row(db_action_items_manual_1)
                                                    insert_df_to_db(db_action_items_manual_1,"action_items_manual")
                                                    st.toast("✅ Action saved to database!", icon="🎯")
                        
                        with tab6:
                            db_style_code_funnel_final=db_style_code_funnel[db_style_code_funnel['vendor_style_code']==db_style_code_for_sequence.loc[st.session_state['page_number'],'vendor_style_code']]
                            # db_style_code_funnel_final
                            db_style_code_funnel_final.reset_index(inplace=True)
                            
                            db_style_code_funnel_final['taxes']=db_style_code_funnel_final['tcs_amount']+db_style_code_funnel_final['tds_amount']
                            db_style_code_funnel_final['settlement']=db_style_code_funnel_final['customer_paid_amt']-db_style_code_funnel_final['platform_fees']-db_style_code_funnel_final['taxes']-db_style_code_funnel_final['total_logistics']
                            db_style_code_funnel_final=db_style_code_funnel_final.groupby(['channel'],as_index=False).agg({'customer_paid_amt':'sum','platform_fees':'sum','taxes':'sum','total_logistics':'sum','settlement':'sum','cost':'sum','total_actual_settlement':'sum'})
                            db_style_code_funnel_final['p/l']=db_style_code_funnel_final['total_actual_settlement']-db_style_code_funnel_final['cost']
                            db_style_code_funnel_final['mktg & others']=db_style_code_funnel_final['settlement']-db_style_code_funnel_final['total_actual_settlement']
                            # db_style_code_funnel_final
                            funnel_channel_list=db_style_code_funnel_final['channel'].unique().tolist()
                            funnel_channel_len=len(funnel_channel_list)
                            db_style_code_funnel_final_funnel=pd.DataFrame()
                            for i in range(funnel_channel_len):
                                db_style_code_funnel_final_1=db_style_code_funnel_final[db_style_code_funnel_final['channel']==funnel_channel_list[i] ]
                                db_style_code_funnel_final_1.drop(['channel'],inplace=True,axis=1)
                                
                                db_style_code_funnel_final_1_T=db_style_code_funnel_final_1.T
                                db_style_code_funnel_final_1_T.reset_index(inplace=True)
                                db_style_code_funnel_final_1_T.rename(columns = {'index':'metric',0:'value'},inplace=True)
                                db_style_code_funnel_final_1_T['channel']=funnel_channel_list[i]
                                db_style_code_funnel_final_funnel=pd.concat([db_style_code_funnel_final_funnel, db_style_code_funnel_final_1_T], ignore_index=True, sort=False)

                            db_style_code_funnel_final_funnel['value']=round(db_style_code_funnel_final_funnel['value'],0)
                            # db_style_code_funnel_final_funnel
                            # db_style_code_funnel_final_funnel
                            
                            fig = go.Figure(go.Waterfall(
                            name = "CODB", orientation = "h", measure = ["relative", "relative", "relative", "relative", "relative","total", "relative",
                                                                    "total"],
                            y = ["Customer_Paid_Amount", "Platform Fee", "Taxes", "Logistics","Marketing & Others", "Settlement", "COGS", "P/L"],
                            x = [db_style_code_funnel_final_funnel['value'][0],-db_style_code_funnel_final_funnel['value'][1],-db_style_code_funnel_final_funnel['value'][2],-db_style_code_funnel_final_funnel['value'][3],-db_style_code_funnel_final_funnel['value'][8],None,-db_style_code_funnel_final_funnel['value'][5], None],
                            connector = {"mode":"between", "line":{"width":4, "color":"rgb(0, 0, 0)", "dash":"solid"}}
                        ))

                            fig.update_layout(title = "Profit and loss statement")
                            count=count+1

                            st.plotly_chart(fig,key=str(count))
                          
