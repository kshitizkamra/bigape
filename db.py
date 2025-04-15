import streamlit as st
import pandas as pd
from sqlalchemy import create_engine,text

secrets = st.secrets["mysql"]
DB_URL = f"mysql+pymysql://{secrets['user']}:{secrets['password']}@{secrets['host']}:{secrets['port']}/{secrets['database']}"

# Connect to MySQL
conn = st.connection("mysql", type="sql", url=DB_URL)

# Read tables
db_data = conn.query("SELECT * FROM final_data", ttl=600)
db_sales_data = conn.query("SELECT * FROM final_sales", ttl=600)
db_sales_data_for_side_filter = db_sales_data.copy()
db_latlong = conn.query("SELECT * FROM latlong", ttl=600)
db_settlement_upload=conn.query("SELECT * FROM settlement_upload", ttl=600)
db_sales_upload=conn.query("SELECT * FROM sales_upload", ttl=600)
db_master=conn.query("SELECT * FROM master", ttl=600)
db_settlement=conn.query("SELECT * FROM settlement", ttl=600)
db_sales=conn.query("SELECT * from sales", ttl=600)
# For sidebar filters
def get_sidebar_data():
    db_channel = conn.query("SELECT DISTINCT channel FROM master", ttl=600)
    db_seller = conn.query("SELECT DISTINCT channel_x, seller_id FROM final_sales", ttl=600)
    db_gender = conn.query("SELECT DISTINCT gender, seller_id FROM final_sales", ttl=600)
    db_brands = conn.query("SELECT DISTINCT brand, gender, seller_id FROM final_sales", ttl=600)
    db_article_type = conn.query("SELECT DISTINCT article_type, brand FROM master", ttl=600)
    return db_channel, db_seller, db_gender, db_brands, db_article_type

# For actions
def get_actions_data():
    db_styles_action = conn.query("SELECT * FROM actions_upload", ttl=600)
    db_actual_action = conn.query("SELECT * FROM recommendation_upload", ttl=600)
    db_accepted_actions = conn.query("SELECT * FROM action_items_manual", ttl=600)
    selling_price_list = conn.query("SELECT DISTINCT selling_price FROM recommendation_upload", ttl=600)
    pla_list = conn.query("SELECT DISTINCT pla FROM recommendation_upload", ttl=600)
    replenishment_list = conn.query("SELECT DISTINCT replenishment FROM recommendation_upload", ttl=600)
    return db_styles_action, db_actual_action, db_accepted_actions, selling_price_list, pla_list, replenishment_list

# ✅ INSERT DataFrame to MySQL table
def insert_df_to_db(df, table_name, db_url=DB_URL):
    engine = create_engine(db_url)
    with engine.connect() as connection:
        df.to_sql(name=table_name, con=connection, if_exists='append', index=False)
        

def insert_df_to_db_masters(df, table_name, db_url=DB_URL):
    engine = create_engine(db_url)
    with engine.begin() as conn:
        try:
            # Read existing data from the table
            existing_df = pd.read_sql_table(table_name, conn)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            
            # Drop duplicates based on all columns, keep last
            deduped_df = combined_df.drop_duplicates(keep="last")
        except ValueError:
            # Table doesn't exist or is empty — just use incoming df
            deduped_df = df
        
        # Overwrite the table with deduped data
        deduped_df.to_sql(name=table_name, con=conn, if_exists='replace', index=False)


def clear_table_data(table_name, db_url=DB_URL):
    engine = create_engine(db_url)
    with engine.begin() as conn:
        stmt = text(f"DELETE FROM `{table_name}`")
        conn.execute(stmt)