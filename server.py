#import "python-bittrex/bittrex/bittrex" as trex
import sys
sys.path.append('python-bittrex/bittrex/')
import bittrex

class Watcher:
    """ A watcher for price changes """
    def __init__(self, markets):
        self.d_markets = markets
        self.d_bittrex = bittrex.Bittrex("ad0c5a7966bb40f5bcdbaa0eb98fb090", "972fbf91ac2240608ae9cc1a68ed54f6")

    def parse_markets(self, d):
        interested_markets = []
        for key in d:
            market = key["MarketName"]
            base_value = market.split('-')[0]
            if (base_value == "BTC" or base_value == "USDT"):
                interested_markets.append(market)
        print(interested_markets)
        print(len(interested_markets))

    def run(self):
        print("Starting Watcher...")
        self.parse_markets(self.d_bittrex.get_markets()["result"])


if __name__ == "__main__":
    markets = [
        "USDT-BTC",
        "BTC-LTC",
        "BTC-ETH",
        "BTC-XRP",
        "BTC-XMR",
        "BTC-"
    ]

    obj = Watcher(markets)
    obj.run()