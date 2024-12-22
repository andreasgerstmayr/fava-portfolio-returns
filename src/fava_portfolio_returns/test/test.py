BEANGROW_CONFIG_CORP = """
investments {
  investment {
    currency: "CORP"
    asset_account: "Assets:CORP"
    dividend_accounts: "Income:CORP:Dividend"
    cash_accounts: "Assets:Cash"
  }
}
groups {
  group {
    name: "CORP"
    investment: "Assets:CORP"
  }
}
"""

BEANGROW_CONFIG_CORPAB = """
investments {
  investment {
    currency: "CORPA"
    asset_account: "Assets:CORPA"
    dividend_accounts: "Income:CORPA:Dividend"
    cash_accounts: "Assets:Cash"
  }
  investment {
    currency: "CORPB"
    asset_account: "Assets:CORPB"
    dividend_accounts: "Income:CORPB:Dividend"
    cash_accounts: "Assets:Cash"
  }
}
groups {
  group {
    name: "CORP"
    investment: "Assets:CORP*"
  }
}
"""
