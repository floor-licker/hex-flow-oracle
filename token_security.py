from goplus.token import Token

# Initialize Token checker, add access token if needed
token_checker = Token(access_token=None)

def check_token_security(token_address):
    """
    Based on a stringified response from GoPlus.
    """
    try:
        response = token_checker.token_security(
            chain_id="1",
            addresses=[token_address],
            **{"_request_timeout": 10}
        )
        data_str = str(response)

        if "'trust_list': '1'" in data_str:
            return True

        return is_token_safe(data_str)
    except Exception as e:
        return False

def is_token_safe(data_str):
    safety_criteria = [
        "'is_honeypot': '0'",
        "'is_blacklisted': '0'",
        "'can_take_back_ownership': '0'",
        "'cannot_buy': '0'",
        "'cannot_sell_all': '0'",
        "'personal_slippage_modifiable': '0'",
        "'slippage_modifiable': '0'",
        "'sell_tax': '0'",
        "'buy_tax': '0'",
        "'is_airdrop_scam': '0'",
        "'is_proxy': '0'",
        "'trading_cooldown': '0'",
        "'transfer_pausable': '0'",
        "'is_in_dex': '1'"
    ]

    for criterion in safety_criteria:
        if criterion not in data_str:
            return False

    return True
