from kolibri.tools.commonReg import Regex
import regex as re


from kolibri.tools.scanner import Scanner
from kolibri.entities.entity import Entity, Entities


class CommonRegexExtractor(Scanner):
    """ Simple JavaScript tokenizer using the Scanner class"""

    def __init__(self):
        super(CommonRegexExtractor, self).__init__()
        self.regexes = Regex()

    def process(self, src):

        # self.entities = Entities() # previous
        self.entities = []
        self.string = src
        while not self.eos():
            """ Scanning is pretty simple in theory: we iterate over the string and
      say 'does this match here?... well how about this? ... ' etc
      
      It pays to do string based checks (isspace, isalpha, etc) before running
      regex methods (scan, check, skip), if possible
      """

            self.counter = 0

            index = self.pos
            c = self.peek()

            if c.isalpha():
                if self.scan(self.regexes.email):
                    tok = 'Email'
                elif self.scan(self.regexes.po_box):
                    tok = 'PoBox'
                elif self.scan(self.regexes.title):
                    tok = 'Title'
                elif self.scan(self.regexes.duration):
                    tok = 'Duration'
#                elif self.scan(self.regexes.link):
#                    tok = 'WEBURL'
                elif self.scan(self.regexes.filename):
                    tok = 'FileName'
                elif self.scan(self.regexes.period):
                    tok= 'Period'
                elif self.scan(self.regexes.period_month_day):
                    tok= 'Period'
                elif self.scan(self.regexes.date_2):
                    tok = 'Date'
                elif self.scan(self.regexes.date):
                    tok = 'Date'
                elif self.scan(self.regexes.date_month_year):
                    tok = 'Date'
                elif self.scan(self.regexes.date_month_day):
                    tok = 'Date'
                elif self.scan(self.regexes.month):
                    tok= 'Month'
                elif self.scan(self.regexes.money):
                    tok = 'Money'
                elif self.scan(self.regexes.money_prefix):
                    tok = 'Money'
                elif self.scan(self.regexes.quarter):
                    tok = 'Period'
                elif self.scan(self.regexes.time_frequecy):
                    tok = 'Frequency'



                else:
                    tok = 'UNKNOWN'
                    self.get()

            elif c.isdigit():

                if self.scan(self.regexes.phone):
                    tok = 'Phone'
                elif self.scan(self.regexes.duration1):
                    tok = 'Duration'
                elif self.scan(self.regexes.date):
                    tok = 'Date'
                elif self.scan(self.regexes.date_2):
                    tok = 'Date'
                elif self.scan(self.regexes.money):
                    tok = 'Money'
                elif self.scan(self.regexes.time):
                    tok = 'Time'
                elif self.scan(self.regexes.ip):
                    tok = 'IpAddress'
                elif self.scan(self.regexes.ipv6):
                    tok = 'IpAddressV6'
                elif self.scan(self.regexes.credit_card):
                    tok = 'CreditCard'
                elif self.scan(self.regexes.street_address):
                    tok = 'StreetAddress'
                elif self.scan(self.regexes.social_security_nbr):
                    tok = 'SocialSecurityNumber'
                elif self.scan(self.regexes.year):
                    tok = 'Year'
                else:
                    tok = 'UNKNOWN'
                    self.get()
            else:
                if self.scan(self.regexes.money):
                    tok = 'Money'
                else:
                    tok = 'UNKNOWN'
                    self.get()

            assert (index < self.pos)

            if tok != 'UNKNOWN':
                value = self.string[index:self.pos]
                self.addEntity(tok, value, index, self.pos)

        return self.entities

    def get_matches(self, text):
        return self.process(text)

    def addEntity(self, tok, value, start, end):
        t = Entity(tok, value.strip(), start, end)
        t.idx = self.counter
        self.counter += 1
        self.entities.append(t)


if __name__=='__main__':
    text="""Please pay the associate to be paid £500 gross in August pay. WT 2328

Employee Referral Payments
Hi Both,
Please can you arrange payment of the following employee referrals.
Associate to be paid
Name of associate referred
Probation Complete
Amount
Carl Palmer
Andrew Wilson
Yes
£500
Caitlin Wiendl
Umme Ali
Yes
£500
Mohamed Nurain
Anna Power
Yes
£500
Amber McGuigan
Gregory Stoneman
Yes
£500
Andy Markham
Jonathan Tomlinson
Yes
£500
Francesco Mercurio
Luke Hodgson
Yes
£500
Any questions please let me know."""

    ext=CommonRegexExtractor()


    ents=ext.get_matches(text)
    for ent in ents:
        print(ent.tojson())