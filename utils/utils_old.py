import json
import os
from datetime import datetime, timedelta
import time

from config.config import Config

# BURN_ADDRESS = "0x0000000000000000000000000000000000000000"
# DONUT_CONTRACT = "0xC0F9bD5Fa5698B6505F643900FFA515Ea5dF54A9"

# POSITION = 1e18
# COST_PER_MONTH = 200
# COST_PER_DAY = (12 * COST_PER_MONTH) / 365
# SUNSET_DT = datetime(2023, 11, 8)
# SUNSET_TIMESTAMP = SUNSET_DT.timestamp()

# SLEEP_TIME_SEC = 1
# API_LIMIT = 5

config = Config()


def calculate_special_membership(
    reddit_user,
    donut_transactions,
    limit_timestamp,
):
    total_donuts_burned = 0
    total_special_memberships_days = 0
    active_membership_timestamp = 0
    has_bought_membership = False
    has_active_membership = False
    for transaction in donut_transactions:
        if transaction["to"] == config.burn_address:
            has_bought_membership = True
            txn_dt = datetime.utcfromtimestamp(transaction["timestamp"])
            amount = transaction["value"] / config.decimal_position
            total_donuts_burned += amount
            tx_special_memberships_days = amount / config.cost_per_day
            end_txn_sp_memb_dt = txn_dt + timedelta(days=tx_special_memberships_days)
            end_txn_sp_memb_dt = end_txn_sp_memb_dt.timestamp()

            total_special_memberships_days += tx_special_memberships_days
            if end_txn_sp_memb_dt >= limit_timestamp:
                has_active_membership = True
                if (
                    active_membership_timestamp == 0
                    or active_membership_timestamp > transaction["timestamp"]
                ):
                    active_membership_timestamp = transaction["timestamp"]

    reddit_user.update(
        {
            "activeMembership": has_active_membership,
            "membershipRank": int(total_special_memberships_days / 30),
            "totalDonutsBurned": total_donuts_burned,
            "totalBoughtMonthsMembership": total_donuts_burned / config.cost_per_month,
        }
    )

    if has_bought_membership and has_active_membership:
        spent_days = (
            datetime.utcfromtimestamp(limit_timestamp)
            - datetime.utcfromtimestamp(active_membership_timestamp)
        ).days
        not_spent_days = total_special_memberships_days - spent_days

        reddit_user.update(
            {
                "spentDays": spent_days,
                "notSpentDays": int(not_spent_days),
            }
        )

        return reddit_user
    else:
        reddit_user.update(
            {
                "spentDays": total_special_memberships_days,
                "notSpentDays": 0,
            }
        )
        return reddit_user


def get_limit_timestamp(input_data):
    if "isRedditSunset" in input_data and input_data["isRedditSunset"]:
        return config.sunset_timestamp
    else:
        current_utc_datetime = datetime.utcnow()
        return current_utc_datetime.timestamp()


def save_data(sp_memb_data, input_data):
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
    if api_calls >= config.api_limit:
        print(
            f"API Limit {config.api_limit} reached, waiting {config.sleep_time_sec} second."
        )
        time.sleep(config.sleep_time_sec)
        return 0
    return api_calls
