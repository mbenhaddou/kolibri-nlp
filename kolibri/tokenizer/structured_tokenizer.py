#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'mohamedbenhaddou'

import regex as re
from kolibri.pipeComponent import Component
from kolibri.tokenizer.token_ import Token
from kolibri.stopwords import get_stop_words
from gensim.models.phrases import Phrases, Phraser
types_abstraction={
        'NUM' :  '__NUMBER__',
        'NUMCODE' :  '__CODE__',
        'MAYBECODE': '__MAYBECODE__',
        'DAY' :  '__DAY__',
        'YEAR' :  '__YEAR__',
        'NUM_TS' :  '__NUMBER__',
        'PLUS' :  '__SYMBOL__',
        'MINUS' :  '__SYMBOL__',
        'ELLIPSIS' :  '__PUNCTUATION__',
        'DOT' :  '__PUNCTUATION__',
        'COMA' :  '__PUNCTUATION__',
        'COLON' :  '__PUNCTUATION__',
        'SEMICOLON' :  '__PUNCTUATION__',
        'OTHER' :  '__SYMBOL__',
        'TIMES' :'__SYMBOL__',
        'EQ' : '__SYMBOL__',
        'CANDIDATE' : '__CANDIDATE__',
        'CLOSEPARENTHESIS' :'__SYMBOL__',
        'WEB_ADRESSS' : '__WEB__',
        'EMAIL' :'__EMAIL__',
        'DATE' :'__DATETIME__',
        'TIME' :'__DATETIME__',
        'DATE_NL' : '__DATETIME__',
        'MONTH' :'__DATETIME__',
        'MONTH_NL' :'__DATETIME__',
        'DICIMAL' : '__NUMBER__',
        'PIPE' : '__SYMBOL__',
        'FILE' :'__FILENAME__',
        'MONEY' :'__MONEY__',
        'IBAN' : '__BANKACCOUNT__',
        'PAYMENTCOMMUNICATION' : '__PAYMENTCOMMUNICATION__'
}
class StructuredTokenizer(Component):
    name = "tokenizer_structured"
    provides = ["tokens"]


    def __init__(self, component_config=None, generate_candidates=False):

        super(StructuredTokenizer, self).__init__(component_config=component_config)

        self.stopwords = None
        if "language" in self.component_config:
            self.language = self.component_config['language']
            self.stopwords = get_stop_words(self.language)


        WORD = r"(?P<WORD>[^.'\s,#:!;/\({\[\]\)}?-]+|(?:'s|'t))"  # catch all
        NUM = r'(?P<NUM>\d+)'
        CODE = r'(?P<NUMCODE>\b(?:[A-Z\.-]+[0-9\.-]+|[0-9\.-]+[A-Z\.-]+)[A-Z0-9\.-]*\b)'
        MAYBECODE = r'(?P<MAYBECODE>\b\d{0,3}[ ]?\d{3}[ ]?\d{3}[ ]?\d{3}\b)'
        DAY = r'(?P<DAY>\d+(st|nd|rd|th))'
        NUM_TS = r'(?P<NUM_TS>[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+))'
        PLUS = r'(?P<PLUS>\+)'
        MINUS = r'(?P<MINUS>\-)'
        ELLIPSIS = r'(?P<ELLIPSIS>\.\.\.)'
        DOT = r'(?P<DOT>\.)'
        COMA = r'(?P<COMA>,)'
        QUESTION = r'(?P<QUESTION>\?)'
        EXLAMATION = r'(?P<EXLAMATION>\!)'
        COLON = r'(?P<COLON>\:)'
        SEMICOLON = r'(?P<SEMICOLON>;)'
        OTHER = r'[/\\{}\(\[\)\]#-]'
        TIMES = r'(?P<TIMES>\*)'
        EQ = r'(?P<EQ>=)'
        WS = r'(?P<WS>\s+)'
        IBAN = r'(?P<IBAN>[A-Z]{2}[0-9]{2}(?:[ ]?[0-9X]{4}){3,4}(?:[ ]?[0-9X]{1,2})?)'
        CANDIDATE1 = r'(?P<CANDIDATE>(?:[A-Z]+[-\.\s_]))'
        CANDIDATE2 = r'(?P<CANDIDATE>(?:[A-Z]\w+\s*(?:de\sla|de|du|di|des|van|of)+\s(?:[A-Z]\w+)))'
        CANDIDATE3 = r'(?P<CANDIDATE>[A-Z][\w\.-]*\'?\w(?:[,\. ]{0,2}[A-Z][\w-]*\'?[\w-]*)*\b)'
        OPENPARENTHESIS = r'(?P<OPENPARENTHESIS>[\(\<])'
        CLOSEPARENTHESIS = r'(?P<CLOSEPARENTHESIS>[\)\<])'
        DURATION = r'(?P<DURATION>\d+[\.,]?\d*\s*(?:\w+)?\s*(days?|hours?|minutes?)\s*(\d+[?.]?\d*\s*(days?|hours?|minutes?))?)'
        ACORNYM = r'(?P<ACRONYM>\b[A-Z][A-Z0-9-\&]+\b)'
        AR = r'(?P<AR_CONTRACTED>(?:[lcdjmntsLCDJMNTS]|qu|Qu)[\'’])'
        WA = r'(?P<WEB_ADRESSS>https?://[\S\%]+|www\.\w+(\.\w+)+)'
        EMAIL = r'(?P<EMAIL>[a-zA-Z0-9+_\-\.]+@[0-9a-zA-Z][\.-0-9a-zA-Z]*\.[a-zA-Z]+)'
        DATE = r'(?P<DATE>\b((([0-3]?[0-9]|1st|2nd|3rd|\d{,2}th|(?:19|20)\d{2})[\.\/ -]{1,2}([0-3]?[0-9]|J(an(uary)?|u(ne?|ly?))|Feb(ruary)?|Ma(rch|y|r)|A(pr(il)?|ug(ust)?)|(((Sept?|Nov|Dec)(em)?)|Octo?)(ber)?))|(J(an(uary)?|u(ne?|ly?))|Feb(ruary)?|Ma(rch|y|r)|A(pr(il)?|ug(ust)?)|(((Sept?|Nov|Dec)(em)?)|Octo?)(ber)?[, ]\d{1,2}))([\/\., -]{0,2}(19|20)?[0-9]{2})?\b)'
        DATE_NL = r'(?P<DATE>\b([0-3]?[0-9]|1st|2nd|3rd|\d{,2}th|(?:19|20)\d{2})[\.\/ -]([0-3]?[0-9]|j(?:an(uari)?|u(?:ni?|li?))|feb(ruari)?|m(?:aart|ei)|a(?:pril|ug(ustus)?)|(?:(?:(?:sept|nov|dec)(em)?)|o(k|c)to?)(ber)?)([\/\. -]+(?:19|20)?[0-9]{2})?\b)'
        DATE_NL2 = r'(?P<DATE>\b(?:an(uari)?|u(?:ni?|li?))|feb(ruari)?|m(?:aart|ei)|a(?:pril|ug(ustus)?)|(?:(?:(?:sept|nov|dec)(em)?)|o(k|c)to?)(ber)?([\/\. -]+(?:19|20)?[0-9]{2})?\b)'
        TIME = r'(?P<TIME>(\d{1,2}[:hH]\d{2}\sGMT)|(\d{1,2}[:hH]\d{2}))'
        MONTH = r'\b(?P<MONTH>J(?:anuary|u(?:ne|ly))|February|Ma(?:rch|y)|A(?:pril|ugust)|(?:(?:(?:Sept|Nov|Dec)em)|Octo)ber)\b'
        MONTH_NL = r'(?P<DATE>\b([0-3]?[0-9]|1ste?|2nde?|3rde?|\d{,2}de|(?:19|20)\d{2})[\.\/ -]([0-3]?[0-9]|j(?:an(uari)?|u(?:ni?|li?))|feb(ruari)?|m(?:aart|ei)|a(?:pril|ug(ustus)?)|(?:(?:(?:sept|nov|dec)(em)?)|o(k|c)to?)(ber)?)([\/\. -]+(?:19|20)?[0-9]{2})?\b)'
        DICIMAL = r'(?P<DICIMAL>\d+[.,]\d+)'
        OPENQOTE = r'(?P<OPENQOTE>«+)'
        ENDQOTE = r'(?P<ENDQOTE>»+)'
        EXCEPTIONS = r'(?P<WORD>Aujourd\'hui)'
        DOUBLEQOTE = r'(?P<DOUBLEQOTE>"+)'
        SINGLEQOTE = r'(?P<SINGLEQOTE>\'+)'
        PIPE = r'(?P<PIPE>\|)'
        YEAR = r'(?P<YEAR>\b201\d\b)'
        PAYMENTCOMMUNICATION=r'(?P<PAYMENTCOMMUNICATION>\b(?:\d{3}[\/-]\d{4}[\/-]\d{5})\b)'
        MULTIPLEWORD = r'(?P<MULTIWORD>(?:\w+-)(?!\d{6,})(?:\w+\-?)+)'
        FILE = r'(?P<FILE>(?:\w+-?)(?:\w+\-?)+\.(?:pdf|png|xlsx?|docx?|pptx?|jpe?g|csv|txt|rtf)\b)'
        MONEY = r'(?P<MONEY>-?(?:(?:\$|£|€)\s?\d+([,\.]\d+)*)|\b(?:\d{1,3}[,\. ]?)+\d{0,2}\s*(?:\$|£|€|euro?s?|EUR)\b|\b\d{1,3}[,\.](?:\d{3}[,\.])+\d{0,2}\b)'

        if not generate_candidates:
            self.master_pat = re.compile(r'|'.join(
                [OTHER, AR, EXCEPTIONS, WA, EMAIL, MONEY, DATE, TIME, MONTH, CODE, DURATION, DICIMAL, NUM_TS, ACORNYM,
                 DAY, NUM,
                 OPENPARENTHESIS, CLOSEPARENTHESIS, WS, FILE, MULTIPLEWORD, PLUS, MINUS, ELLIPSIS, DOT, TIMES, EQ,
                 QUESTION,
                 EXLAMATION, COLON, COMA, SEMICOLON, OPENQOTE, ENDQOTE, DOUBLEQOTE, SINGLEQOTE, PIPE, WORD]),
                re.UNICODE)
        else:
            self.master_pat = re.compile(r'|'.join(
                [AR, EXCEPTIONS, WA, EMAIL, MONEY, DATE, TIME, MONTH, CODE, DURATION, DICIMAL, NUM_TS, ACORNYM, DAY,
                 NUM, OTHER,
                 OPENPARENTHESIS, CLOSEPARENTHESIS, WS, CANDIDATE2, CANDIDATE3, CANDIDATE1, FILE, MULTIPLEWORD, PLUS,
                 MINUS, ELLIPSIS, DOT, TIMES, EQ, QUESTION,
                 EXLAMATION, COLON, COMA, SEMICOLON, OPENQOTE, ENDQOTE, DOUBLEQOTE, SINGLEQOTE, PIPE, WORD]),
                re.UNICODE)


    def generate_tokens(self, text):
        text = text.replace(r'\u2019', '\'')
        scanner = self.master_pat.scanner(text)
        i = 0
        for m in iter(scanner.match, None):
            t = Token(text=m.group().strip(), start=m.start(), index=i)
            t.set('type', m.lastgroup)
            i += 1
            yield t

    def tokenize(self, text):
        tokens = []
        counter = 0
        for token in self.generate_tokens(text):
            if token.get('type') != 'WS':
                token.index = counter
                if self.stopwords:
                    token.is_stopword = token.text.lower() in self.stopwords
                token.abstract=types_abstraction.get(token.get('type'), None)
                counter += 1
                tokens.append(token)
        return tokens

    def train(self, training_data, config, **kwargs):

        for example in training_data.training_examples:
            example.tokens=self.tokenize(example.text)

    def process(self, document, **kwargs):

        document.tokens= self.tokenize(document.text)


    def space_tokenize(self, text):
        tokens = self.tokenize(text)
        for token in tokens:
            if len(token.text.split()) > 1:
                print(token.text)

if __name__=='__main__':
    tokenizer = StructuredTokenizer(True)
    text = """This automated mail is triggered for $ 123 to inform you a rescind has been executed in Change Job with an effective date of 2019 10 01"""
    tokens = tokenizer.tokenize(text)

    for t in tokens:
        print(t.text, t.get('type'))