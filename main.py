import csv
import etherscan
import time
import json
from datetime import datetime, timedelta

CSV_FILE_PATH = "round_128.csv"
BURN_ADDRESS = "0x0000000000000000000000000000000000000000"
DONUT_CONTRACT = "0xC0F9bD5Fa5698B6505F643900FFA515Ea5dF54A9"

POSITION = 1e18
COST_PER_MONTH = 200
COST_PER_DAY = (12 * COST_PER_MONTH) / 365
SUNSET_DT = datetime(2023, 11, 8)
SUNSET_TIMESTAMP = SUNSET_DT.timestamp()

SLEEP_TIME_SEC = 1
API_LIMIT = 5
API_KEY = "WHHQF6XHN4YDRY81MCV4ZWCGWU5IWX9B3W"


def calculate_data(name, blockchain_address, donut_transactions):
    total_donuts_burned = 0
    total_special_memberships_days = 0
    older_timestamp = 0
    has_bought_membership = False
    for transaction in donut_transactions:
        if transaction["to"] == BURN_ADDRESS:
            has_bought_membership = True
            txn_dt = datetime.utcfromtimestamp(transaction["timestamp"])
            amount = transaction["value"] / POSITION
            total_donuts_burned += amount
            tx_special_memberships_days = amount / COST_PER_DAY
            end_txn_sp_memb_dt = txn_dt + timedelta(days=tx_special_memberships_days)
            end_txn_sp_memb_dt = end_txn_sp_memb_dt.timestamp()

            if end_txn_sp_memb_dt >= SUNSET_TIMESTAMP:
                total_special_memberships_days += tx_special_memberships_days
                if older_timestamp == 0 or older_timestamp > transaction["timestamp"]:
                    older_timestamp = transaction["timestamp"]

    if has_bought_membership:
        spent_days = (SUNSET_DT - datetime.utcfromtimestamp(older_timestamp)).days
        not_spent_days = total_special_memberships_days - spent_days
        sp_memb_until = SUNSET_DT + timedelta(days=not_spent_days)

        return {
            "username": name,
            "address": blockchain_address,
            "currentMembershipRank": int(spent_days / 30),
            "totalDonutsBurned": total_donuts_burned,
            "totalMonthsMembership": total_donuts_burned / COST_PER_MONTH,
            "spentDays": spent_days,
            "notSpentDays": not_spent_days,
            "specialMembershipUntil": sp_memb_until.strftime("%Y-%m-%d"),
        }
    return None


def main():
    es = etherscan.Client(
        api_key=API_KEY,
        cache_expire_after=5,
    )

    sp_memb_data = []
    api_calls = 0
    with open(CSV_FILE_PATH, "r") as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            name = row["username"]
            blockchain_address = row["blockchain_address"]

            if api_calls >= API_LIMIT:
                print(
                    f"API Limit {API_LIMIT} reached, waiting {SLEEP_TIME_SEC} second."
                )
                time.sleep(SLEEP_TIME_SEC)
                api_calls = 0

            print(f"Retrieving data from: {name}")
            donut_transactions = es.get_token_transactions(
                contract_address=DONUT_CONTRACT, address=blockchain_address
            )
            api_calls += 1

            if donut_transactions:
                reddit_user = calculate_data(
                    name, blockchain_address, donut_transactions
                )
                if reddit_user:
                    sp_memb_data.append(reddit_user)

    file_name = "output.json"

    with open(file_name, "w") as file:
        json.dump(sp_memb_data, file)

    print(f"JSON data has been written to {file_name}")


main()
