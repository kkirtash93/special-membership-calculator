import etherscan
import time
import json
from datetime import datetime
import time
from dotenv import load_dotenv
from utils import utils

USERS_FILE_URL = "https://ethtrader.github.io/donut.distribution/users.json"
SPECIAL_MEMBERSHIP_FILE = "out/special_memberships.json"
CSV_FILE_PATH = "in/round_128.csv"
BURN_ADDRESS = "0x0000000000000000000000000000000000000000"
DONUT_CONTRACT = "0xC0F9bD5Fa5698B6505F643900FFA515Ea5dF54A9"

COST_PER_MONTH = 200
COST_PER_DAY = (12 * COST_PER_MONTH) / 365
SUNSET_DT = datetime(2023, 11, 8)
SUNSET_TIMESTAMP = SUNSET_DT.timestamp()

SLEEP_TIME_SEC = 1
API_LIMIT = 5


def main(input_data):
    start_time = time.time()
    es = etherscan.Client(
        api_key="WHHQF6XHN4YDRY81MCV4ZWCGWU5IWX9B3W",
        cache_expire_after=5,
    )

    sp_memb_data = []
    api_calls = 0

    with open(SPECIAL_MEMBERSHIP_FILE, "r") as file:
        user_json = json.load(file)

        for user in user_json:
            if user["activeMembership"]:
                name = user["username"]
                blockchain_address = user["address"]

                api_calls = utils.freeze_process(api_calls)

                print(f"Retrieving data from: {name}")
                donut_transactions = es.get_token_transactions(
                    contract_address=DONUT_CONTRACT,
                    address=blockchain_address,
                )
                api_calls += 1

                if donut_transactions:
                    reddit_user = utils.calculate_special_membership(
                        name,
                        blockchain_address,
                        donut_transactions,
                        utils.get_limit_timestamp(input_data),
                    )
                    if reddit_user:
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
    }
)

# main({"isRedditSunset": True, "fileName": "special_memberships_since_reddit_sunset"})
