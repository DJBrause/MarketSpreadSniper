import requests
import pandas as pd
from dotenv import load_dotenv
import os
import logging

from constants import TYPE_ID_NAME_MAP, MINIMAL_SPREAD, TRADE_STATION_ID, DOMAIN_REGION_ID
from send_file import send_email_with_attachment

logging.basicConfig(
    filename='logfile.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

load_dotenv()

regions = ['Domain', 'The Forge', 'Heimatar', 'Metropolis', 'Sinq Laison']

domain_sell_orders_url = f'https://esi.evetech.net/latest/markets/{DOMAIN_REGION_ID}/orders/?datasource=tranquility&order_type=sell'
domain_buy_orders_url = f'https://esi.evetech.net/latest/markets/{DOMAIN_REGION_ID}/orders/?datasource=tranquility&order_type=buy'


recipients_from_dotenv = os.environ.get('RECIPIENTS')
gmail_scopes = os.environ.get('GMAIL_SCOPES')


def main() -> None:
    buy_orders_initial = requests.get(domain_buy_orders_url)
    sell_orders_initial = requests.get(domain_sell_orders_url)

    buy_order_pages = int(buy_orders_initial.headers['x-pages'])+1
    sell_order_pages = int(sell_orders_initial.headers['x-pages'])+1

    current_directory = os.getcwd()
    final_sell_orders_list = []
    final_buy_orders_list = []

    for buy_order_page in range(1, buy_order_pages):
        buy_orders = requests.get(domain_buy_orders_url+f'&page={buy_order_page}')
        buy_orders_dict = buy_orders.json()
        final_buy_orders_list.extend(buy_orders_dict)

    for sell_order_page in range(1, sell_order_pages):
        sell_orders = requests.get(domain_sell_orders_url+f'&page={sell_order_page}')
        sell_orders_dict = sell_orders.json()
        final_sell_orders_list.extend(sell_orders_dict)

    df_buy_orders = pd.DataFrame(final_buy_orders_list)
    # limiting results to just the trade station offers
    df_buy_orders = df_buy_orders[df_buy_orders['location_id'] == TRADE_STATION_ID]
    df_buy_orders_max_price = df_buy_orders.loc[df_buy_orders.groupby('type_id')['price'].idxmax()]

    df_sell_orders = pd.DataFrame(final_sell_orders_list)
    # limiting results to just the trade station offers
    df_sell_orders = df_sell_orders[df_sell_orders['location_id'] == TRADE_STATION_ID]
    df_sell_orders_min_price = df_sell_orders.loc[df_sell_orders.groupby('type_id')['price'].idxmin()]

    df_combined = pd.merge(df_sell_orders_min_price, df_buy_orders_max_price, on='type_id', how='outer',
                           suffixes=('_sell', '_buy'))
    df_combined['price_sell'] = df_combined['price_sell'].fillna(0)
    df_combined['price_buy'] = df_combined['price_buy'].fillna(0)

    df_combined['market_spread_station_only'] = df_combined['price_sell'] - df_combined['price_buy']
    df_combined = df_combined[df_combined['market_spread_station_only'] >= MINIMAL_SPREAD]
    df_combined['name'] = df_combined['type_id'].map(TYPE_ID_NAME_MAP)

    df_combined.to_excel('spread.xlsx', sheet_name='spread', index=False)

    sender = os.environ.get('EMAIL')
    recipient = os.environ.get('RECIPIENTS')

    subject = "EVE Market Domain Region Spreads"
    body_text = "Witaj, \nTabelka w załączniku."
    attachment_path = os.path.join(current_directory, 'spread.xlsx')

    send_email_with_attachment(sender, recipient, subject, body_text, attachment_path)


if __name__ == '__main__':
    main()
