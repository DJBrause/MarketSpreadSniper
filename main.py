import requests
import pandas as pd
from dotenv import load_dotenv
import os
import logging

from constants import TYPE_ID_NAME_MAP, MINIMAL_SPREAD
from send_file import send_email_with_attachment

logging.basicConfig(
    filename='logfile.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


load_dotenv()

domain_region_id = 10000043
regions = ['Domain', 'The Forge', 'Heimatar', 'Metropolis', 'Sinq Laison']

domain_sell_orders_url = 'https://esi.evetech.net/latest/markets/10000043/orders/?datasource=tranquility&order_type=sell'
domain_buy_orders_url = 'https://esi.evetech.net/latest/markets/10000043/orders/?datasource=tranquility&order_type=buy'


recipients_from_dotenv = os.environ.get('RECIPIENTS')
gmail_scopes = os.environ.get('GMAIL_SCOPES')


def get_item_names_from_buy_orders(input_buy_orders: dict) -> list:
    names = [get_item_name_with_type_id(buy_order['type_id']) for buy_order in input_buy_orders]
    return names


def get_item_name_with_type_id(type_id: int) -> str:
    type_id_url = f'https://esi.evetech.net/latest/universe/types/{type_id}/?datasource=tranquility&language=en'
    result = requests.get(type_id_url).json()
    return result['name']


def get_type_ids_and_names_from_sell_orders(input_sell_orders: dict) -> dict:
    type_ids_and_names = {sell_order['type_id']: get_item_name_with_type_id(sell_order['type_id'])
                          for sell_order in input_sell_orders}
    return type_ids_and_names


def main() -> None:
    buy_orders_initial = requests.get(domain_buy_orders_url)
    sell_orders_initial = requests.get(domain_sell_orders_url)

    current_directory = os.getcwd()
    final_sell_orders_list = []
    final_buy_orders_list = []

    for page in range(1, int(sell_orders_initial.headers['x-pages'])):
        sell_orders = requests.get(domain_sell_orders_url+f'&page={page}')
        sell_orders_dict = sell_orders.json()
        final_sell_orders_list.extend(sell_orders_dict)

    for page in range(1, int(buy_orders_initial.headers['x-pages'])):
        buy_orders = requests.get(domain_buy_orders_url+f'&page={page}')
        buy_orders_dict = buy_orders.json()
        final_buy_orders_list.extend(buy_orders_dict)

    df_sell_orders = pd.DataFrame(final_sell_orders_list)

    df_sell_orders_min_price = df_sell_orders.loc[df_sell_orders.groupby('type_id')['price'].idxmin()]
    df_sell_filtered = df_sell_orders_min_price[df_sell_orders_min_price['location_id'] != 60008494]

    df_buy_orders = pd.DataFrame(final_buy_orders_list)
    df_buy_orders_max_price = df_buy_orders.loc[df_buy_orders.groupby('type_id')['price'].idxmax()]
    df_buy_orders_max_price_filtered = df_buy_orders_max_price[df_buy_orders_max_price['location_id'] != 60008494]

    df_combined = pd.merge(df_sell_filtered, df_buy_orders_max_price_filtered, on='type_id', how='outer',
                           suffixes=('_sell', '_buy'))

    df_combined['spread'] = df_combined['price_sell'] - df_combined['price_buy']
    df_combined = df_combined[df_combined['spread'] >= MINIMAL_SPREAD]
    df_combined['name'] = df_combined['type_id'].map(TYPE_ID_NAME_MAP)

    df_combined.to_excel('spread.xlsx', sheet_name='spread', index=False)

    sender = os.environ.get('EMAIL')
    recipient = os.environ.get('RECIPIENTS')
    aws_region = 'eu-central-1'
    subject = "EVE Market Domain Region Spreads"
    body_text = "Witaj, \nTabelka w załączniku."
    attachment_path = os.path.join(current_directory, 'spread.xlsx')

    send_email_with_attachment(sender, recipient, aws_region, subject, body_text, attachment_path)


if __name__ == '__main__':
    main()
