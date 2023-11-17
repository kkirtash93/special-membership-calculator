import etherscan
import time
import os
import json
from datetime import datetime
import time
from dotenv import load_dotenv
from config.config import Config
from utils import utils

# USERS_FILE_URL = "https://ethtrader.github.io/donut.distribution/users.json"
# SPECIAL_MEMBERSHIP_FILE = "out/special_memberships.json"
# BURN_ADDRESS = "0x0000000000000000000000000000000000000000"
# DONUT_CONTRACT = "0xC0F9bD5Fa5698B6505F643900FFA515Ea5dF54A9"

# COST_PER_MONTH = 200
# COST_PER_DAY = (12 * COST_PER_MONTH) / 365
# SUNSET_DT = datetime(2023, 11, 8)
# SUNSET_TIMESTAMP = SUNSET_DT.timestamp()

# SLEEP_TIME_SEC = 1
# API_LIMIT = 5

config = Config()


def main(input_data):
    start_time = time.time()
    es = etherscan.Client(
        api_key=os.getenv("API_KEY"),
        cache_expire_after=5,
    )

    sp_memb_data = []
    api_calls = 0

    with open(config.special_membership_file_path, "r") as file:
        reddit_users = json.load(file)

        for reddit_user in reddit_users:
            if reddit_user["activeMembership"]:
                name = reddit_user["username"]
                blockchain_address = reddit_user["address"]

                api_calls = utils.freeze_process(api_calls)

                print(f"Retrieving data from: {name}")
                donut_transactions = es.get_token_transactions(
                    contract_address=config.donut_contract,
                    address=blockchain_address,
                )
                api_calls += 1

                if donut_transactions:
                    reddit_user = utils.calculate_special_membership(
                        reddit_user,
                        donut_transactions,
                        utils.get_limit_timestamp(input_data),
                    )

            sp_memb_data.append(reddit_user)

    if len(sp_memb_data) > 0:
        utils.save_data(sp_memb_data, input_data)
    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"The process took {elapsed_time:.2f} seconds to complete.")


load_dotenv()
main(
    {
        "isRedditSunset": False,
    },
)


# main({"isRedditSunset": True, "fileName": "special_memberships_since_reddit_sunset"})
