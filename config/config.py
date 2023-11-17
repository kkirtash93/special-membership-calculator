from datetime import datetime


class Config:
    users_file = "https://ethtrader.github.io/donut.distribution/users.json"
    special_membership_file_path = "out/special_memberships.json"
    burn_address = "0x0000000000000000000000000000000000000000"
    donut_contract = "0xC0F9bD5Fa5698B6505F643900FFA515Ea5dF54A9"
    decimal_position = 1e18
    cost_per_month = 200
    cost_per_day = (12 * cost_per_month) / 365
    sunset_dt = datetime(2023, 11, 8)
    sunset_timestamp = sunset_dt.timestamp()
    sleep_time_sec = 1
    api_limit = 5
