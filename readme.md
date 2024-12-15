# EVE Market Spread Analyzer

This project retrieves market orders from the EVE Online API for specific regions, processes the data to calculate profitable market spreads, and sends the results as an email attachment using AWS SES.

## Features

- Fetches market buy and sell orders for predefined EVE Online regions.
- Filters orders to include only those at a specific trade station.
- Calculates market spreads between the highest buy prices and the lowest sell prices.
- Generates a spreadsheet with the results.
- Sends the spreadsheet as an email attachment using AWS SES.

## Requirements

### Prerequisites
- Python 3.8+
- An AWS account with SES configured.
- An `.env` file with the following variables:
  ```env
  EMAIL=<your_email_address>
  RECIPIENTS=<recipient_email_addresses>
  GMAIL_SCOPES=<gmail_scopes>
  AWS_ACCESS_KEY=<aws_access_key>
  AWS_SECRET_KEY=<aws_secret_key>
  AWS_REGION=<aws_region>
  ```
- Install the required Python packages:
  ```bash
  pip install requests pandas python-dotenv boto3 openpyxl
  ```

## Usage

1. Clone the repository and navigate to the project directory.
2. Ensure the `.env` file is correctly configured.
3. Run the script:
   ```bash
   python main.py
   ```

## File Overview

### `main.py`
This script handles the core logic of the project:
- Fetches market orders from the EVE Online API.
- Processes the data to calculate spreads.
- Generates a spreadsheet (`spread.xlsx`).
- Sends the spreadsheet as an email attachment.

### `send_file.py`
Contains the function `send_email_with_attachment`, which uses AWS SES to send an email with the generated spreadsheet attached.

### `constants.py`
Defines the following constants (you need to create this file):
- `TYPE_ID_NAME_MAP`: A dictionary mapping item type IDs to their names.
- `MINIMAL_SPREAD`: The minimum spread value to include in the results.
- `TRADE_STATION_ID`: The ID of the trade station to filter orders.
- `DOMAIN_REGION_ID`: The ID of the Domain region.
- `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_REGION`: AWS credentials and region.

## Output

The script generates an Excel file named `spread.xlsx` containing the following columns:
- `type_id`: The type ID of the item.
- `price_sell`: The lowest sell price.
- `price_buy`: The highest buy price.
- `market_spread_station_only`: The calculated spread.
- `name`: The name of the item.

## Logging

Logs are saved to `logfile.log`. The log includes:
- Information about data fetching and processing.
- Errors encountered during the email-sending process.

## Notes

- Ensure AWS SES is configured to allow emails from your sender address to your recipient address.
- This script only processes market orders from predefined regions.

## License
This project is open source and available under the [MIT License](LICENSE).

