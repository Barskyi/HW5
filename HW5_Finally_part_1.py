import httpx
import asyncio
import platform
import json
import sys
from datetime import datetime, timedelta


class HttpError(Exception):
    """Custom exception for HTTP errors."""
    pass


async def requests(url: str):
    """Make an HTTP GET request."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                raise HttpError(f"Error status: {response.status_code}, for {url}")
    except HttpError as err:
        print(err)
        return "I'm really sorry"


async def parse_exchange(data) -> list:
    """Parse exchange rate data."""
    formatted_response = []
    for currency in data['exchangeRate']:
        if currency['currency'] in ['EUR', 'USD']:
            entry = {
                data['date']: {
                    currency['currency']: {
                        'sale': currency.get('saleRate', currency['saleRateNB']),
                        'purchase': currency.get('purchaseRate', currency['purchaseRateNB'])
                    }
                }
            }
            formatted_response.append(entry)
    return [item for item in formatted_response if item]


async def get_dates(num_days):
    """Generate dates for the specified number of days."""
    try:
        num_days = int(num_days)
    except ValueError:
        print("Please enter a valid number of days.")
        return None

    if not 1 <= num_days <= 10:
        print("Oops! You should choose any data between 1 and 10.")
        return None

    current_date = datetime.now().date()
    all_dates = [(current_date - timedelta(days=x)).strftime('%d.%m.%Y') for x in range(num_days)]
    return all_dates


async def process_requests(all_dates):
    """Process HTTP requests for each date."""
    try:
        responses = await asyncio.gather(*[
            requests(f"https://api.privatbank.ua/p24api/exchange_rates?date={date}")
            for date in all_dates
        ])

        parsed_responses = []
        for response in responses:
            parsed_data = await parse_exchange(response)
            parsed_responses.append(parsed_data)

        return parsed_responses
    except HttpError as err:
        print(err)
        return None


async def main(num_days):
    """Main function to orchestrate the process."""
    all_dates = await get_dates(num_days)

    if all_dates is not None:
        result = await process_requests(all_dates)
        return result


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    num_days = sys.argv[1] if len(sys.argv) > 1 else '2'
    result = asyncio.run(main(num_days))

    if result:
        final_response = json.dumps(result, indent=2, ensure_ascii=False)
        print(final_response)
