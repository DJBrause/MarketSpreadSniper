import requests
import pandas as pd
from dotenv import load_dotenv
import os
import logging
import time

from constants import (TYPE_ID_NAME_MAP, MINIMAL_SPREAD, AMARR_STATION_ID, DOMAIN_REGION_ID, THE_FORGE_REGION_ID,
                       REGION_ID_NAME_MAP, JITA_STATION_ID)
from send_file import send_email_with_attachment

logging.basicConfig(
    filename='logfile.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

load_dotenv()

regions = ['Domain', 'The Forge', 'Heimatar', 'Metropolis', 'Sinq Laison']
region_ids = [DOMAIN_REGION_ID, THE_FORGE_REGION_ID]
result_dataframes = {}

recipients_from_dotenv = os.environ.get('RECIPIENTS')
gmail_scopes = os.environ.get('GMAIL_SCOPES')


def fetch_with_retries(url, max_retries=5, backoff_factor=2):
    """Fetch data from the API with retry logic."""
    retries = 0
    while retries < max_retries:
        response = requests.get(url)
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                logging.warning(f"Invalid JSON response: {response.text}")
                return None
        else:
            logging.warning(f"Error fetching data: {response.json()}, retrying...\n Failed URL: {url}")
            retries += 1
            time.sleep(backoff_factor ** retries)  # Exponential backoff
    logging.error(f"Failed to fetch data after {max_retries} retries.")
    return None


def create_marketspread_df(region_id: int) -> pd.DataFrame:
    """Create a DataFrame with the market spread for a given region."""
    sell_orders_url = f'https://esi.evetech.net/latest/markets/{region_id}/orders/?datasource=tranquility&order_type=sell'
    buy_orders_url = f'https://esi.evetech.net/latest/markets/{region_id}/orders/?datasource=tranquility&order_type=buy'

    sell_orders_initial = requests.get(sell_orders_url)
    buy_orders_initial = requests.get(buy_orders_url)

    sell_order_pages = int(sell_orders_initial.headers['x-pages'])+1
    buy_order_pages = int(buy_orders_initial.headers['x-pages'])+1

    final_sell_orders_list = []
    final_buy_orders_list = []

    if region_id == DOMAIN_REGION_ID:
        station_id = AMARR_STATION_ID
    else:
        station_id = JITA_STATION_ID

    for sell_order_page in range(1, sell_order_pages):
        sell_orders_dict = fetch_with_retries(sell_orders_url+f'&page={sell_order_page}')
        final_sell_orders_list.extend(sell_orders_dict)

    for buy_order_page in range(1, buy_order_pages):
        buy_orders_dict = fetch_with_retries(buy_orders_url+f'&page={buy_order_page}')
        final_buy_orders_list.extend(buy_orders_dict)

    df_sell_orders = pd.DataFrame(final_sell_orders_list)
    df_sell_orders = df_sell_orders[df_sell_orders['location_id'] == station_id]
    df_sell_orders_min_price = df_sell_orders.loc[df_sell_orders.groupby('type_id')['price'].idxmin()]

    df_buy_orders = pd.DataFrame(final_buy_orders_list)
    df_buy_orders = df_buy_orders[df_buy_orders['location_id'] == station_id]
    df_buy_orders_max_price = df_buy_orders.loc[df_buy_orders.groupby('type_id')['price'].idxmax()]

    df_combined = pd.merge(df_sell_orders_min_price, df_buy_orders_max_price, on='type_id', how='outer',
                           suffixes=('_sell', '_buy'))
    df_combined['price_sell'] = df_combined['price_sell'].fillna(0)
    df_combined['price_buy'] = df_combined['price_buy'].fillna(0)

    df_combined['market_spread_station_only'] = df_combined['price_sell'] - df_combined['price_buy']
    df_combined = df_combined[df_combined['market_spread_station_only'] >= MINIMAL_SPREAD]
    df_combined['name'] = df_combined['type_id'].map(TYPE_ID_NAME_MAP)

    return df_combined


def main() -> None:
    file_name = 'markets_spreads.xlsx'
    output_path = os.path.join(os.getcwd(), file_name)
    for region in region_ids:
        region_name = REGION_ID_NAME_MAP[region]
        logging.info(f"Processing region: {region_name}")
        df = create_marketspread_df(region)
        result_dataframes[region_name] = df

    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for df in result_dataframes:
            result_dataframes[df].to_excel(writer, sheet_name=df, index=False)

    sender = os.environ.get('EMAIL')
    recipients = [item.strip() for item in os.getenv('RECIPIENTS', "").split(",") if item]
    subject = "EVE Market Domain and The Forge Region Spreads"
    body_text = "Cześć, \nTabelka w załączniku. Spready zaczynają się od 10 mln ISK. \n\nPozdrawiam, \nPtysiu"

    for recipient in recipients:
        send_email_with_attachment(sender, recipient, subject, body_text, file_name)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(e)
