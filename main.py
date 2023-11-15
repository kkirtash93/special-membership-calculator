import csv
import etherscan
import time
import json
import os
import argparse
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

CSV_FILE_PATH = "in/round_128.csv"
BURN_ADDRESS = "0x0000000000000000000000000000000000000000"
DONUT_CONTRACT = "0xC0F9bD5Fa5698B6505F643900FFA515Ea5dF54A9"

POSITION = 1e18
COST_PER_MONTH = 200
COST_PER_DAY = (12 * COST_PER_MONTH) / 365
SUNSET_DT = datetime(2023, 11, 8)
SUNSET_TIMESTAMP = SUNSET_DT.timestamp()

SLEEP_TIME_SEC = 1
API_LIMIT = 5


def calculate_special_membership(
    name,
    blockchain_address,
    donut_transactions,
    limit_timestamp,
):
    total_donuts_burned = 0
    total_special_memberships_days = 0
    active_membership_timestamp = 0
    has_bought_membership = False
    has_active_membership = False
    for transaction in donut_transactions:
        if transaction["to"] == BURN_ADDRESS:
            has_bought_membership = True
            txn_dt = datetime.utcfromtimestamp(transaction["timestamp"])
            amount = transaction["value"] / POSITION
            total_donuts_burned += amount
            tx_special_memberships_days = amount / COST_PER_DAY
            end_txn_sp_memb_dt = txn_dt + timedelta(days=tx_special_memberships_days)
            end_txn_sp_memb_dt = end_txn_sp_memb_dt.timestamp()

            if end_txn_sp_memb_dt >= limit_timestamp:
                has_active_membership = True
                total_special_memberships_days += tx_special_memberships_days
                if (
                    active_membership_timestamp == 0
                    or active_membership_timestamp > transaction["timestamp"]
                ):
                    active_membership_timestamp = transaction["timestamp"]

    reddit_user = {
        "username": name,
        "address": blockchain_address,
        "activeMembership": has_active_membership,
        "membershipRank": int(total_special_memberships_days / 30),
        "totalDonutsBurned": total_donuts_burned,
        "totalBoughtMonthsMembership": total_donuts_burned / COST_PER_MONTH,
    }

    if has_bought_membership and has_active_membership:
        spent_days = (
            SUNSET_DT - datetime.utcfromtimestamp(active_membership_timestamp)
        ).days
        not_spent_days = total_special_memberships_days - spent_days

        reddit_user.update(
            {
                "spentDays": spent_days,
                "notSpentDays": int(not_spent_days),
            }
        )

        return reddit_user

    if has_bought_membership and not has_active_membership:
        reddit_user.update(
            {
                "spentDays": total_special_memberships_days,
                "notSpentDays": 0,
            }
        )
        return reddit_user

    return None


def get_limit_timestamp(input_data):
    if "isRedditSunset" in input_data and input_data["isRedditSunset"]:
        return SUNSET_TIMESTAMP
    else:
        current_utc_datetime = datetime.utcnow()
        return current_utc_datetime.timestamp()


def create_and_save_data(sp_memb_data, input_data):
    file_name = (
        input_data["fileName"] if "fileName" in input_data else "special_memberships"
    )
    folder_path = "out/"
    os.makedirs(folder_path, exist_ok=True)

    file_name = f"{file_name}.json"

    file_path = os.path.join(folder_path, file_name)

    with open(file_path, "w") as file:
        json.dump(sp_memb_data, file, indent=2)

    print(f"JSON data has been written to {file_path}")


def freeze_process(api_calls):
    if api_calls >= API_LIMIT:
        print(f"API Limit {API_LIMIT} reached, waiting {SLEEP_TIME_SEC} second.")
        time.sleep(SLEEP_TIME_SEC)
        return 0
    return api_calls


def main(input_data):
    es = etherscan.Client(
        api_key="WHHQF6XHN4YDRY81MCV4ZWCGWU5IWX9B3W",
        cache_expire_after=5,
    )

    sp_memb_data = []
    api_calls = 0

    with open(CSV_FILE_PATH, "r") as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            name = row["username"]
            blockchain_address = row["blockchain_address"]

            api_calls = freeze_process(api_calls)

            print(f"Retrieving data from: {name}")
            donut_transactions = es.get_token_transactions(
                contract_address=DONUT_CONTRACT,
                address=blockchain_address,
            )
            api_calls += 1

            if donut_transactions:
                reddit_user = calculate_special_membership(
                    name,
                    blockchain_address,
                    donut_transactions,
                    get_limit_timestamp(input_data),
                )
                if reddit_user:
                    sp_memb_data.append(reddit_user)

    create_and_save_data(sp_memb_data, input_data)


load_dotenv()
main(
    {
        "isRedditSunset": False,
    }
)
