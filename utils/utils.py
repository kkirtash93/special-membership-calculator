import json
import os
from datetime import datetime, timedelta
import time

from config.config import Config

config = Config()


def calculate_special_membership(reddit_user, donut_transactions, limit_timestamp):
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
            tx_special_memberships_days = amount / config.cost_per_day
            end_txn_sp_memb_dt = txn_dt + timedelta(days=tx_special_memberships_days)

            total_donuts_burned += amount
            total_special_memberships_days += tx_special_memberships_days

            if end_txn_sp_memb_dt.timestamp() >= limit_timestamp:
                has_active_membership = True
                if (
                    active_membership_timestamp == 0
                    or active_membership_timestamp > transaction["timestamp"]
                ):
                    active_membership_timestamp = transaction["timestamp"]

    update_reddit_user(
        reddit_user,
        has_bought_membership,
        has_active_membership,
        total_donuts_burned,
        total_special_memberships_days,
        limit_timestamp,
        active_membership_timestamp,
    )

    return reddit_user


def update_reddit_user(
    reddit_user,
    has_bought_membership,
    has_active_membership,
    total_donuts_burned,
    total_special_memberships_days,
    limit_timestamp,
    active_membership_timestamp,
):
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
    else:
        reddit_user.update(
            {
                "spentDays": total_special_memberships_days,
                "notSpentDays": 0,
            }
        )


def get_limit_timestamp(input_data):
    if "isRedditSunset" in input_data and input_data["isRedditSunset"]:
        return config.sunset_timestamp
    else:
        return datetime.utcnow().timestamp()


def save_data(sp_memb_data, input_data):
    file_name = input_data.get("fileName", "special_memberships")
    folder_path = "out/"
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{file_name}.json")

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
