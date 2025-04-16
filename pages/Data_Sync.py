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
st.cache_data.clear()

if not st.session_state.get("logged_in", False):
    st.switch_page("home.py")
make_sidebar()

# upload_conn = st.connection("upload", type=GSheetsConnection)

# master_conn = st.connection("master", type=GSheetsConnection)

# final_data_conn = st.connection("final_settlement", type=GSheetsConnection)
# final_sales_conn = st.connection("final_sales", type=GSheetsConnection)





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






        
container=st.container(border=True)


# db_settlement

with st.container(border=True) :
    st.subheader("Sync All Data")
    
    if st.button('Sync Now',key="sync_btn"):
        st.cache_data.clear()
        
        from db import db_latlong,db_settlement, get_sidebar_data, get_actions_data, insert_df_to_db,insert_df_to_db_masters,clear_table_data,db_sales,db_master

        

        final_bar=st.progress(0,text="Syncing all data")
        # db_sales=master_conn.read(worksheet="sales")
        # db_settlement=master_conn.read(worksheet="settlement")
        # db_master=master_conn.read(worksheet="master")
        db_sales=db_sales.drop_duplicates()
        db_settlement=db_settlement.drop_duplicates()
        db_master=db_master.drop_duplicates()
        
        final_bar.progress(1/4,text="Merging the Data")
        db_sales
        db_data=db_sales.merge(db_settlement,left_on=['order_release_id'],right_on=['order_release_id'])
        
        db_data
        db_data=db_data.merge(db_master,left_on=['sku_code'],right_on=['channel_product_id'])
        db_data
        db_data['seller_id']=db_data['seller_id'].astype(str)
        db_data.drop(['sku_code_x','channel_x','channel_y','channel_product_id','sku_code_y','channel_style_id'],axis=1,inplace=True)
        db_data
        db_sales_final=db_sales.merge(db_master,left_on=['sku_code'],right_on=['channel_product_id'])
        db_sales_final['seller_id']=db_sales_final['seller_id'].astype(str)
        final_bar.progress(2/4,text="Final Magic ")
        
        db_data.drop(['order_status'],axis=1,inplace=True)
        # db_sales_final.drop(['fabric'],axis=1,inplace=True)
        db_sales_final.drop(['channel_y'],axis=1,inplace=True)

        abcd=db_data[(db_data['order_type']=='Reverse') & (db_data['returns']==0)]
        db_data.loc[(db_data['order_release_id'].isin(abcd['order_release_id'])),'returns']=1
        db_sales_final.loc[(db_sales_final['order_release_id'].isin(abcd['order_release_id'])),'returns']=1


        clear_table_data('final_data')
        clear_table_data('final_sales')
        insert_df_to_db_masters(db_sales_final,"final_sales")
        insert_df_to_db_masters(db_data,"final_data")
        
        # final_data_conn.update(worksheet="final_data",data=db_data)
        # final_sales_conn.update(worksheet="final_sales",data=db_sales_final)
        
        final_bar.progress(3/4,text="Final Magic")

        # db_data=final_data_conn.read(worksheet="final_data")
        db_data['order_count']=0
        db_data.loc[db_data['order_type']=='Forward','order_count']=1
        db_data.loc[db_data['returns']==1,'cost']=0
        db_data.loc[db_data['returns']==1,'customer_paid_amt']=0
        db_data.loc[db_data['returns']==1,'platform_fees']=0
        db_data.loc[db_data['returns']==1,'tcs_amount']=0
        db_data.loc[db_data['returns']==1,'tds_amount']=0
        db_data['return_count']=0
        db_data.loc[(db_data['returns']==1)&(db_data['order_type']=='Forward'),'return_count']=1
        # db_style_data_try=db_data.groupby(['vendor_style_code','channel','brand','gender','article_type'],as_index=False).agg({'order_count':'sum','return_count':'sum','platform_fees':'sum','tcs_amount':'sum','tds_amount':'sum','shipping_fee':'sum','pick_and_pack_fee':'sum','fixed_fee':'sum','payment_gateway_fee':'sum','total_tax_on_logistics':'sum','cost':'sum','order_created_date':'min'})
        # db_style_data_try
        db_data['settlement']=db_data['customer_paid_amt']-db_data['platform_fees']-db_data['tcs_amount']-db_data['tds_amount']-db_data['shipping_fee']-db_data['pick_and_pack_fee']-db_data['fixed_fee']-db_data['payment_gateway_fee']-db_data['total_tax_on_logistics']
        # db_data['settlement']=db_data['total_actual_settlement']
        db_data.sort_values(by=['order_created_date'],inplace=True)
        db_data['total_actual_settlement'] = pd.to_numeric(db_data['total_actual_settlement'], errors='coerce')
        db_data['cost'] = pd.to_numeric(db_data['cost'], errors='coerce')
        db_data['p/l']=db_data['total_actual_settlement']-db_data['cost']
        # db_data

        # db_style_data['order_created_date']).dt.days
        db_data['order_created_date']=pd.to_datetime(db_data['order_created_date'], format='mixed')
        db_style_data=db_data.groupby(['vendor_style_code','channel','brand','gender','article_type'],as_index=False).agg({'order_count':'sum','return_count':'sum','p/l':'sum','cost':'sum','order_created_date':'min'})
        # db_style_data['order_created_date']=pd.to_datetime(db_style_data['order_created_date'], format='mixed')
        try:
            db_style_data['ros']=db_style_data['order_count']/(pd.to_datetime(datetime.date.today(),format='ISO8601')-db_style_data['order_created_date']).dt.days
        except:
            
            db_style_data['ros']=db_style_data['order_count']/(pd.to_datetime(datetime.date.today(),format='ISO8601')-pd.to_datetime(db_style_data['order_created_date'], dayfirst=True, format='ISO8601')).dt.days
        db_style_data['days']=(pd.to_datetime(datetime.date.today(),format='ISO8601')-pd.to_datetime(db_style_data['order_created_date'], dayfirst=True, format='ISO8601')).dt.days
        db_style_data['returns']=db_style_data['return_count']/db_style_data['order_count']
        db_style_data.loc[db_style_data['cost']==0,'cost']=0.0001
        db_style_data['roi']=db_style_data['p/l']/db_style_data['cost']
        
        db_style_data['ros_action']=db_style_data['roi_action']=db_style_data['return_action']='D'
        # db_style_data.drop(['order_count','return_count','p/l','cost','order_created_date'],inplace=True,axis=1)
        
        db_styles_action, db_actual_action, db_accepted_actions,selling_price_list,pla_list,replenishment_list=get_actions_data()

        # db_styles_action=master_conn.read(worksheet="actions_upload")
        # db_actual_action=master_conn.read(worksheet="recommendation_upload")

        db_styles_action.sort_values(by=['metrics'],inplace=True)
        
        for index,rows in db_style_data.iterrows():
            
            db_styles_action_tab=db_styles_action[(db_styles_action['brand']==rows.brand)&(db_styles_action['gender']==rows.gender)&(db_styles_action['article_type']==rows.article_type)&(db_styles_action['channel']==rows.channel)]
            db_styles_action_tab.reset_index(inplace=True)
        
            
            if rows.ros>=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='ros','a'].sum():
                db_style_data.loc[index,'ros_action']='A'
            elif rows.ros>=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='ros','b'].sum():
                db_style_data.loc[index,'ros_action']='B'
            else:
                db_style_data.loc[index,'ros_action']='C'
            
            if rows.roi>=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='roi','a'].sum():
                db_style_data.loc[index,'roi_action']='A'
            elif rows.roi>=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='roi','b'].sum():
                db_style_data.loc[index,'roi_action']='B'
            else:
                db_style_data.loc[index,'roi_action']='C'


            if rows.returns<=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='return %','a'].sum():
                db_style_data.loc[index,'return_action']='A'
            elif rows.returns<=db_styles_action_tab.loc[db_styles_action_tab['metrics']=='return %','b'].sum():
                db_style_data.loc[index,'return_action']='B'
            else:
                db_style_data.loc[index,'return_action']='C'


            db_actual_action_tab=db_actual_action[(db_actual_action['ros']==db_style_data.loc[index,'ros_action'])&(db_actual_action['roi']==db_style_data.loc[index,'roi_action'])&(db_actual_action['return %']==db_style_data.loc[index,'return_action'])]
            db_actual_action_tab.reset_index(inplace=True)
            db_style_data.loc[index,'selling_price']=db_actual_action_tab['selling_price'][0]
            
            db_style_data.loc[index,'pla']=db_actual_action_tab['pla'][0]
            db_style_data.loc[index,'replenishment']=db_actual_action_tab['replenishment'][0]
            db_style_data.loc[index,'remarks']=db_actual_action_tab['remarks'][0]

            db_style_data['date_updated']=datetime.datetime.now()

        # db_style_data  

        clear_table_data("action_items_suggestion")
        insert_df_to_db(db_style_data,"action_items_suggestion")
        # master_conn.update(worksheet="action_items_suggestion",data=db_style_data)
            

        final_bar.progress(4/4,text="All syncing done - Happy Analysing")
