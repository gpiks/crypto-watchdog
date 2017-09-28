#import "python-bittrex/bittrex/bittrex" as trex
import sys
sys.path.append('python-bittrex/bittrex/')
import bittrex
import pprint
import json
from time import sleep
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import numpy


# noinspection PyInterpreter
class Watcher:
    """ A watcher for price changes """
    def __init__(self):
        print("Initializing Watcher...")
        self.d_bittrex = bittrex.Bittrex("ad0c5a7966bb40f5bcdbaa0eb98fb090", "972fbf91ac2240608ae9cc1a68ed54f6")
        self.d_markets = self.parse_markets(self.d_bittrex.get_markets()["result"])
        self.d_currentBTCPrice = self.d_bittrex.get_ticker("USDT-BTC")["result"]["Last"]

    def parse_markets(self, d):
        interested_markets = []
        for key in d:
            market = key["MarketName"]
            currency = market.split('-')
            base_currency = currency[0]
            exchange_currency = currency[1]
            if (base_currency == "BTC" or (base_currency == "USDT" and exchange_currency == "BTC")):
                interested_markets.append(market)
        print(interested_markets)
        return interested_markets

    def get_ticks_all(self):
        self.d_currentBTCPrice = self.d_bittrex.get_ticker("USDT-BTC")["result"]["Last"]
        all_market_ticks = []
        for market in self.d_markets:
            market_tick = self.d_bittrex.get_ticker(market)["result"]
            market_tick.update((x, y*self.d_currentBTCPrice) for x, y in market_tick.items())
            market_tick["Market"] = market
            all_market_ticks.append(market_tick)
            #pp = pprint.PrettyPrinter(indent=2)
            #pp.pprint(market_tick)
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
        print("Initializing Logger...")
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

    def get_array(self, key, sub_key):
        full_object = []
        try:
            full_object = self.d_values[key]
        except KeyError:
            return []

        data_array = []
        try:
            data_array = self.d_values[key][sub_key]
        except KeyError:
            return []

        return self.d_values[key][sub_key]

    def write(self):
        with open('market_summaries.txt', 'w') as outfile:
            json.dump(self.d_values, outfile)


class Model:

    def __init__(self, deviation_constant):
        self.d_dc = deviation_constant

    @staticmethod
    def deviation_from_avg(values_array):
        average = sum(values_array) / len(values_array)
        numpy_values_array = numpy.array(values_array)
        std_dev = numpy.std(numpy_values_array)
        return [average, std_dev]

    @staticmethod
    def mail_for_row(values_array, tick, market, key):
        calculated_params = Model.deviation_from_avg(values_array)
        if abs(tick - calculated_params[0]) > calculated_params[1]:
            # more than standard deviation
            #Mailer.send_email("Check %s" % market, "Current %s is at %f" % (key, tick))
            print("Return True for %s, %s" % (market, key))
            return True
        return False


class Mailer:

    @staticmethod
    def send_email(subject, body):
        fromaddr = "gpiks.play@gmail.com"
        #toaddr = ["arvindmrao58@gmail.com", "hemant.pikale@gmail.com", "gaurav.pikale@gmail.com"]
        toaddr = ["gaurav.pikale@gmail.com"]
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = ";".join(toaddr)
        msg['Subject'] = subject

        body = body
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        try:
            server.login(fromaddr, "bittrexmailer")
        except:
            print("Login error")

        text = msg.as_string()
        server.sendmail(fromaddr, ";".join(toaddr), text)
        server.quit()


if __name__ == "__main__":

    obj = Watcher()
    logger = Logger()

    while 1:
        # get all ticks
        all_ticks = obj.get_ticks_all()
        for row in all_ticks:
            print(row)
            try:
                current_bid_row = logger.get_array(row["Market"], "Bid")
                current_ask_row = logger.get_array(row["Market"], "Ask")
                current_last_row = logger.get_array(row["Market"], "Last")

                Model.mail_for_row(current_bid_row, row["Bid"], row["Market"], "Bid")
                Model.mail_for_row(current_ask_row, row["Ask"], row["Market"], "Ask")
                Model.mail_for_row(current_last_row, row["Last"], row["Market"], "Last")

                logger.insert_key_value(row["Market"], "Bid",  row["Bid"])
                logger.insert_key_value(row["Market"], "Ask",  row["Ask"])
                logger.insert_key_value(row["Market"], "Last", row["Last"])
            except NameError:
                print("Skipped bad row '%s'" % row)

        # write all ticks to log file
        logger.write()

        sleep(60)


