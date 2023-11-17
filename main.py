import etherscan
import time
import os
import json
from dotenv import load_dotenv
from config.config import Config
from utils import utils

config = Config()


def initialize_etherscan_client():
    return etherscan.Client(
        api_key=os.getenv("API_KEY"),
        cache_expire_after=5,
    )


def retrieve_donut_transactions(es, reddit_user, input_data):
    name = reddit_user["username"]
    blockchain_address = reddit_user["address"]

    input_data["api_calls"] = utils.freeze_process(input_data["api_calls"])

    print(f"Retrieving data from: {name}")
    donut_transactions = es.get_token_transactions(
        contract_address=config.donut_contract,
        address=blockchain_address,
    )
    input_data["api_calls"] += 1

    return donut_transactions


def process_reddit_user(reddit_user, donut_transactions, input_data):
    if donut_transactions:
        reddit_user = utils.calculate_special_membership(
            reddit_user,
            donut_transactions,
            utils.get_limit_timestamp(input_data),
        )
    return reddit_user


def main(input_data):
    start_time = time.time()
    es = initialize_etherscan_client()

    sp_memb_data = []

    with open(config.special_membership_file_path, "r") as file:
        reddit_users = json.load(file)

        for reddit_user in reddit_users:
            if reddit_user["activeMembership"]:
                donut_transactions = retrieve_donut_transactions(
                    es, reddit_user, input_data
                )
                reddit_user = process_reddit_user(
                    reddit_user, donut_transactions, input_data
                )

            sp_memb_data.append(reddit_user)

    if len(sp_memb_data) > 0:
        utils.save_data(sp_memb_data, input_data)
    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"The process took {elapsed_time:.2f} seconds to complete.")


load_dotenv()
main({"isRedditSunset": False, "api_calls": 0})
