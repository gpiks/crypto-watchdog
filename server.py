#import "python-bittrex/bittrex/bittrex" as trex
import sys
sys.path.append('python-bittrex/bittrex/')
import bittrex
import pprint
import json


# noinspection PyInterpreter
class Watcher:
    """ A watcher for price changes """
    def __init__(self):
        print("Initializing Watcher...")
        self.d_bittrex = bittrex.Bittrex("ad0c5a7966bb40f5bcdbaa0eb98fb090", "972fbf91ac2240608ae9cc1a68ed54f6")
        self.d_markets = self.parse_markets(self.d_bittrex.get_markets()["result"])

    def parse_markets(self, d):
        interested_markets = []
        for key in d:
            market = key["MarketName"]
            base_value = market.split('-')[0]
            if (base_value == "BTC" or base_value == "USDT"):
                interested_markets.append(market)
        print(interested_markets)
        return interested_markets

    def get_ticks_all(self):
        all_market_ticks = []
        for market in self.d_markets:
            market_tick = self.d_bittrex.get_ticker(market)["result"]
            market_tick["Market"] = market
            all_market_ticks.append(market_tick)
            pp = pprint.PrettyPrinter(indent=2)
            pp.pprint(market_tick)
        return all_market_ticks


class Logger:
    """
    ***Logs data for you***

    json structure:
    {
            "BTC-LTC" : {"ask" : [1.5,1.6,2.0],
                         "bid" : [1.5,1.6,2.0],
                         "last" : [1.5,1.6,2.0]},
            ...
            "BTC-NEO" : {"ask" : [2.5,3.5,6.0],
                         "bid" : [1.5,1.6,2.0],
                         "last" : [1.5,1.6,2.0]}
    }

    """
    def __init__(self):
        """ Initializing file logger """
        with open('market_summaries.txt') as json_file:
            try:
                self.d_values = json.load(json_file)
            except ValueError:
                print("Decoding failed.")
                self.d_values = dict()

    def insert_key_value(self, key, sub_key, value):
        full_object = []
        try:
            full_object = self.d_values[key]
        except KeyError:
            self.d_values[key] = {}

        data_array = []
        try:
            data_array = self.d_values[key][sub_key]
        except KeyError:
            self.d_values[key][sub_key] = []

        # add new value
        self.d_values[key][sub_key].append(value)

        if len(self.d_values[key][sub_key]) > 10:
            # remove the older element if more than 10 elements
            del self.d_values[key][sub_key][0]

    def write(self):
        with open('market_summaries.txt', 'w') as outfile:
            json.dump(self.d_values, outfile)


if __name__ == "__main__":

    obj = Watcher()
    logger = Logger()

    # get all ticks
    all_ticks = obj.get_ticks_all()

    # write all ticks to log file
    for row in all_ticks:
        try:
            logger.insert_key_value(row["Market"], "Bid",  row["Bid"])
            logger.insert_key_value(row["Market"], "Ask",  row["Ask"])
            logger.insert_key_value(row["Market"], "Last", row["Last"])
        except NameError:
            print("Skipped bad row")

    logger.write()

