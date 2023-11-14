import csv
import etherscan
import time
import json
from datetime import datetime,timedelta
from decimal import *

es = etherscan.Client(
    api_key='WHHQF6XHN4YDRY81MCV4ZWCGWU5IWX9B3W',
    cache_expire_after=5,
)


csv_file_path = 'round_128.csv'
burn_address = '0x0000000000000000000000000000000000000000'
donut_contract= '0xC0F9bD5Fa5698B6505F643900FFA515Ea5dF54A9'

position = 1e18
sp_memb_cost_per_month= 200
sp_memb_cost_per_day = (12*sp_memb_cost_per_month)/365
sp_memb_sunsent_dt = datetime(2023, 11, 8)
sp_memb_sunsent_timestamp = sp_memb_sunsent_dt.timestamp()

sleep_time_sec = 1
api_limit = 5

sp_memb_data =[]

def calculate_data(name, blockchain_address, donut_transactions):
    total_donuts_burned = 0
    total_special_memberships_days = 0
    older_timestamp = 0
    has_bought_membership = False
    for transaction in donut_transactions:
        if (transaction['to'] == burn_address):
            has_bought_membership = True
            txn_dt = datetime.utcfromtimestamp(transaction['timestamp'])
            amount = (transaction['value']/position)
            total_donuts_burned+=amount
            tx_special_memberships_days = amount/sp_memb_cost_per_day
            end_txn_sp_memb_dt = txn_dt + timedelta(days=tx_special_memberships_days)
            end_txn_sp_memb_dt = end_txn_sp_memb_dt.timestamp()

            if (end_txn_sp_memb_dt >= sp_memb_sunsent_timestamp):
                total_special_memberships_days+=tx_special_memberships_days
                if (older_timestamp == 0 or older_timestamp > transaction['timestamp'] ):
                    older_timestamp = transaction['timestamp']

    if (has_bought_membership):
        spent_days = (sp_memb_sunsent_dt - datetime.utcfromtimestamp(older_timestamp)).days
        not_spent_days = total_special_memberships_days-spent_days
        sp_memb_until = sp_memb_sunsent_dt+timedelta(days=not_spent_days)
            
        print(sp_memb_until.strftime('%Y-%m-%d'))
        return {
            "username": name,
            "address":  blockchain_address,
            "currentMembershipRank": int(spent_days/30),
            "totalDonutsBurned": total_donuts_burned, 
            "totalMonthsMembership": total_donuts_burned/sp_memb_cost_per_month,
            "spentDays": spent_days,
            "notSpentDays": not_spent_days,
            "specialMembershipUntil": sp_memb_until.strftime('%Y-%m-%d')
            }
    return None         

def main():
    api_calls = 0
    with open(csv_file_path, 'r') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            name = row['username']
            blockchain_address = row['blockchain_address']

            if (api_calls >= 5):
                print(f'API Limit {api_limit} reached, waiting {sleep_time_sec} second.')
                time.sleep(sleep_time_sec)
                api_calls = 0
            
            print(f'Retrieving data from: {name}')
            donut_transactions = es.get_token_transactions(
                contract_address=donut_contract,
                address=blockchain_address
            )
            api_calls +=1
        
            if donut_transactions:
                reddit_user = calculate_data(name, blockchain_address, donut_transactions)
                if reddit_user:
                    sp_memb_data.append(reddit_user)

    file_name = "output.json"

    with open(file_name, 'w') as file:
        json.dump(sp_memb_data, file)

    print(f"JSON data has been written to {file_name}")

main()

