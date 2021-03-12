import regex as re

currencies_prefix = ['£', '€', '\$', '(AR|CL)\s?\$', '¥', 'chf', r'\brs', r'\beur', 'usd', 'inr', 'idr', 'rmb', 'jpy', 'rmb',
                     'gbp', 'rub', 'krw', r'\btry', 'lkr', 'cny', 'dkk', 'aed', 'lpa', 'pln', 'huf', 'czk', 'ych']

currencies_postfix = ['chinese\s+yuans?', 'dollars?', 'euro?s?', 'pounds?', 'renminbi', 'yens?', 'yuans?']

currencies: str="|".join(currencies_postfix+currencies_prefix)
money_expressions = ['allowances?\s+of', 'pay\s+is']

amount = r"\d+([',\.]\d+)*|\d+,\d+\.\d+\b"

re_day = r"(?P<day>\b(?:31|30|0?1st|0?2nd|0?3rd|[1-9][0-9]th|(?:\b[1-2][0-9]|\b0?[1-9]))(?:\s*of)?)"
re_month = r"(?P<month>(?:january|february|march|april|may|june|july|august|september|october|november|december|jan\.?|feb\.?|mar\.?|apr\.?|may\.?|jun\.?|jul\.?|aug\.?|sep\.?|sept\.?|oct\.?|nov\.?|dec\.?)|(?:\b30|31|\b[0-2]?[0-9]\b))"
re_year_4 = r"(?P<year>(?:20|19)\d{2})"
re_year_2 = r"(?P<year>(?:20|19)?\d{2})"
date_delimiters = r"(?:(?:\s+of\s+)|(?:\s+\')|[/\-\,\s\.])"

re_date_format = r"\b{}[/\-\\ ]\s*{}[/\-\\ ]\s*{}\b"
dates = []
dates.append(re_date_format.format(re_month, re_day, re_year_2))  # dates in the form of MDY
dates.append(re_date_format.format(re_year_4, re_month, re_day))  # dates in the form of YMD
dates.append(re_date_format.format(re_day, re_month, re_year_2))  # dates in the form of DMY

re_date = r"|".join(dates)
re_date_month_day = r"\b{}[/\-\,\s\.]{}\b".format(re_month, re_day)

re_period = r"(?P<period>(?:From:?)\s+(?P<from>{})\s+(?:to|through|until:?)?\s+(?P<to>{}))".format(re_date, re_date)
re_period_month_day = r"(?P<period>(?:From:?)\s+(?P<from>{})\s+(?:to|through|until:?)?\s+(?P<to>{}))".format(
    re_date_month_day, re_date_month_day)


class Regex:
    def __init__(self):
        self.titles = ["mr", "mrs", "md", "Phd", "Ph.D", "iii", "ii", "miss", "jr", "sr", "prof",
                       "professor", "dr"]
        self.date_year = re.compile(r"\b{}\b".format(re_year_4))
        self.date_year_month = re.compile(r"\b{}\b".format(re_year_4 + re_month), re.IGNORECASE)
        self.date_month_day = re.compile(re_date_month_day, re.IGNORECASE)
        self.date_year_month_day = re.compile(re_date_format.format(re_year_4, re_month, re_day), re.IGNORECASE)
        self.date_day_month_year = re.compile(re_date_format.format(re_day, re_month, re_year_2), re.IGNORECASE)
        self.date_month_day_year = re.compile(re_date_format.format(re_month, re_day, re_year_2), re.IGNORECASE)
        self.date_2 = re.compile(
            r'\b((Mon|Tues|Wedned|thurs|Fri|Satur|Sun)day|(?:3?2?1st|2nd|3rd|[1-9][0-9]th|(?:\b[1-2][0-9]|\b0?[1-9]|30|31))),?\s*(of)?\s*(?:january|february|march|april|may|june|july|august|september|october|november|december|jan\.?|feb\.?|mar\.?|apr\.?|may\.?|jun\.?|jul\.?|aug\.?|sep\.?|sept\.?|oct\.?|nov\.?|dec\.?)\s*(?:3?2?1st|2nd|3rd|[1-9][0-9]th|(?:\b[1-2][0-9]|\b0?[1-9]|30|31))?\b',
            re.I)

        self.date = re.compile(re_date, re.IGNORECASE)
        self.date_month_year = re.compile(re_month + date_delimiters + re_year_2, re.IGNORECASE)
        self.month = re.compile(
            r"(?P<month>\b(?:jan(uary|vier)|fe(bruary|vrier)|march|a(p|v)ril|jui?ne?|ju(ll|illet)?y?|august|aout|september|octob(er|re)|novemb(er|re)|decemb(er|re)|jan\.?|feb\.?|mar\.?|apr\.?|ma(y|i)\.?|jun\.?|jul\.?|aug\.?|sep\.?|sept\.?|oct\.?|nov\.?|dec\.?)\b)",
            re.IGNORECASE)
        self.money = re.compile(
            r"(?P<Currency>"+currencies+r")\s?(?P<Amount>"+amount+")|(?P<Amount>"+amount+r")\s?(?P<Currency>"+currencies+r")|(?:\s*negative\s?)?(?P<amount2>\b\d{1,3}[,\.](?:\d{3}[,\.])+\d{0,2}\b)", re.IGNORECASE)
        self.money_prefix = re.compile(r"(?P<prefix>{})\s*(?:\s*negative\s*)?(?P<amount>[+-]?[\.,\d]+k?)".format(
            r"\b|\b".join(currencies_postfix + currencies_prefix)), re.IGNORECASE)

        self.period = re.compile(re_period, re.IGNORECASE)
        self.period_month_day = re.compile(re_period_month_day, re.IGNORECASE)
        self.time = re.compile(r'\b(\d{1,2}:\d{2} ?(?:[ap]\.?m\.?)?|\d[ap]\.?m\.?)\b', re.IGNORECASE)
        self.phone = re.compile(
            r'\b(\+|00)?\d{1,3}(?:(?:-|\.|\s)?)\(?\d{2,3}\)?((?:(?:-|\.|\s)?)\d{3,5}){2,3}\s*(ext[:\.]\s*\d{3,5})?\b')
        self.phones_with_exts = re.compile(
            r'((?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*(?:[2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|(?:[2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?(?:[2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?(?:[0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(?:\d+)?))',
            re.IGNORECASE)
        self.link = re.compile(
            u'(?i)((?:https?://|www\d{0,3}[.])?[a-z0-9.\-]+[.](?:(?:international)|(?:construction)|(?:contractors)|(?:enterprises)|(?:photography)|(?:immobilien)|(?:management)|(?:technology)|(?:directory)|(?:education)|(?:equipment)|(?:institute)|(?:marketing)|(?:solutions)|(?:builders)|(?:clothing)|(?:computer)|(?:democrat)|(?:diamonds)|(?:graphics)|(?:holdings)|(?:lighting)|(?:plumbing)|(?:training)|(?:ventures)|(?:academy)|(?:careers)|(?:company)|(?:domains)|(?:florist)|(?:gallery)|(?:guitars)|(?:holiday)|(?:kitchen)|(?:recipes)|(?:shiksha)|(?:singles)|(?:support)|(?:systems)|(?:agency)|(?:berlin)|(?:camera)|(?:center)|(?:coffee)|(?:estate)|(?:kaufen)|(?:luxury)|(?:monash)|(?:museum)|(?:photos)|(?:repair)|(?:social)|(?:tattoo)|(?:travel)|(?:viajes)|(?:voyage)|(?:build)|(?:cheap)|(?:codes)|(?:dance)|(?:email)|(?:glass)|(?:house)|(?:ninja)|(?:photo)|(?:shoes)|(?:solar)|(?:today)|(?:aero)|(?:arpa)|(?:asia)|(?:bike)|(?:buzz)|(?:camp)|(?:club)|(?:coop)|(?:farm)|(?:gift)|(?:guru)|(?:info)|(?:jobs)|(?:kiwi)|(?:land)|(?:limo)|(?:link)|(?:menu)|(?:mobi)|(?:moda)|(?:name)|(?:pics)|(?:pink)|(?:post)|(?:rich)|(?:ruhr)|(?:sexy)|(?:tips)|(?:wang)|(?:wien)|(?:zone)|(?:biz)|(?:cab)|(?:cat)|(?:ceo)|(?:com)|(?:edu)|(?:gov)|(?:int)|(?:mil)|(?:net)|(?:onl)|(?:org)|(?:pro)|(?:red)|(?:tel)|(?:uno)|(?:xxx)|(?:ac)|(?:ad)|(?:ae)|(?:af)|(?:ag)|(?:ai)|(?:al)|(?:am)|(?:an)|(?:ao)|(?:aq)|(?:ar)|(?:as)|(?:at)|(?:au)|(?:aw)|(?:ax)|(?:az)|(?:ba)|(?:bb)|(?:bd)|(?:be)|(?:bf)|(?:bg)|(?:bh)|(?:bi)|(?:bj)|(?:bm)|(?:bn)|(?:bo)|(?:br)|(?:bs)|(?:bt)|(?:bv)|(?:bw)|(?:by)|(?:bz)|(?:ca)|(?:cc)|(?:cd)|(?:cf)|(?:cg)|(?:ch)|(?:ci)|(?:ck)|(?:cl)|(?:cm)|(?:cn)|(?:co)|(?:cr)|(?:cu)|(?:cv)|(?:cw)|(?:cx)|(?:cy)|(?:cz)|(?:de)|(?:dj)|(?:dk)|(?:dm)|(?:do)|(?:dz)|(?:ec)|(?:ee)|(?:eg)|(?:er)|(?:en)|(?:et)|(?:eu)|(?:fi)|(?:fj)|(?:fk)|(?:fm)|(?:fo)|(?:fr)|(?:ga)|(?:gb)|(?:gd)|(?:ge)|(?:gf)|(?:gg)|(?:gh)|(?:gi)|(?:gl)|(?:gm)|(?:gn)|(?:gp)|(?:gq)|(?:gr)|(?:gs)|(?:gt)|(?:gu)|(?:gw)|(?:gy)|(?:hk)|(?:hm)|(?:hn)|(?:hr)|(?:ht)|(?:hu)|(?:id)|(?:ie)|(?:il)|(?:im)|(?:in)|(?:io)|(?:iq)|(?:ir)|(?:is)|(?:it)|(?:je)|(?:jm)|(?:jo)|(?:jp)|(?:ke)|(?:kg)|(?:kh)|(?:ki)|(?:km)|(?:kn)|(?:kp)|(?:kr)|(?:kw)|(?:ky)|(?:kz)|(?:la)|(?:lb)|(?:lc)|(?:li)|(?:lk)|(?:lr)|(?:ls)|(?:lt)|(?:lu)|(?:lv)|(?:ly)|(?:ma)|(?:mc)|(?:md)|(?:me)|(?:mg)|(?:mh)|(?:mk)|(?:ml)|(?:mm)|(?:mn)|(?:mo)|(?:mp)|(?:mq)|(?:mr)|(?:ms)|(?:mt)|(?:mu)|(?:mv)|(?:mw)|(?:mx)|(?:my)|(?:mz)|(?:na)|(?:nc)|(?:ne)|(?:nf)|(?:ng)|(?:ni)|(?:nl)|(?:no)|(?:np)|(?:nr)|(?:nu)|(?:nz)|(?:om)|(?:pa)|(?:pe)|(?:pf)|(?:pg)|(?:ph)|(?:pk)|(?:pl)|(?:pm)|(?:pn)|(?:pr)|(?:ps)|(?:pt)|(?:pw)|(?:py)|(?:qa)|(?:re)|(?:ro)|(?:rs)|(?:ru)|(?:rw)|(?:sa)|(?:sb)|(?:sc)|(?:sd)|(?:se)|(?:sg)|(?:sh)|(?:si)|(?:sj)|(?:sk)|(?:sl)|(?:sm)|(?:sn)|(?:so)|(?:sr)|(?:st)|(?:su)|(?:sv)|(?:sx)|(?:sy)|(?:sz)|(?:tc)|(?:td)|(?:tf)|(?:tg)|(?:th)|(?:tj)|(?:tk)|(?:tl)|(?:tm)|(?:tn)|(?:to)|(?:tp)|(?:tr)|(?:tt)|(?:tv)|(?:tw)|(?:tz)|(?:ua)|(?:ug)|(?:uk)|(?:us)|(?:uy)|(?:uz)|(?:va)|(?:vc)|(?:ve)|(?:vg)|(?:vi)|(?:vn)|(?:vu)|(?:wf)|(?:ws)|(?:ye)|(?:yt)|(?:za)|(?:zm)|(?:zw))(?:/[^\s()<>]+[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019])?)',
            re.IGNORECASE)
        self.email = re.compile(
            u"([a-zA-Z0-9!#$%&'*+\/=?^_`{|.}~-]+@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)",
            re.IGNORECASE)
        self.ip = re.compile(
            u'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)',
            re.IGNORECASE)
        self.ipv6 = re.compile(
            u'\s*(?!.*::.*::)(?:(?!:)|:(?=:))(?:[0-9a-f]{0,4}(?:(?<=::)|(?<!::):)){6}(?:[0-9a-f]{0,4}(?:(?<=::)|(?<!::):)[0-9a-f]{0,4}(?:(?<=::)|(?<!:)|(?<=:)(?<!::):)|(?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)){3})\s*',
            re.VERBOSE | re.IGNORECASE | re.DOTALL)
        #        self.money = re.compile(u'[$]\s?[+-]?[0-9]{1,3}(?:(?:,?[0-9]{3}))*(?:\.[0-9]{1,2})?')
        self.credit_card = re.compile(r'\b((?:(?:\\d{4}[- ]?){3}\\d{4}|\\d{15,16}))(?![\\d])\b')
        self.person = re.compile(r'[A-Z][\w-]*\'?\w+[,\.]?(?:[\. ]*[A-Z][\w-]*\'?[\w-]*)*', re.UNICODE)
        self.btc_address = re.compile(
            u'(?<![a-km-zA-HJ-NP-Z0-9])[13][a-km-zA-HJ-NP-Z0-9]{26,33}(?![a-km-zA-HJ-NP-Z0-9])')
        self.street_address = re.compile(
            r'(\d{1,4})?[\w\s]{1,20}\b(?:street|st|avenue|ave|road|rd|highway|hwy|square|sq|trail|trl|drive|dr|court|ct|park|parkway|pkwy|circle|cir|boulevard|blvd)\b\W?(?=\s|$)',
            re.IGNORECASE)
        self.number = re.compile(r'\b[0-9,\.]+\b')
        self.zip_code = re.compile(r'\b([0-9A-Z-]+)\b')
        self.po_box = re.compile(r'P\.? ?O\.? Box \d+', re.IGNORECASE)
        self.social_security_nbr = re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')
        self.year = re.compile(r'\b' + re_year_4 + '\b')
        self.title = re.compile(r'\b(' + '|'.join(self.titles) + r')\b\.?', re.UNICODE | re.IGNORECASE)
        self.string = re.compile(r'\b[\w,\' \/()-]+')
        self.paragraph = re.compile(r'.*')
        self.code = re.compile(r'\b[A-Z0-9]*(?=[A-Z0-9]{4,10})(?=[A-Z0-9]*\d)(?=[A-Z0-9]*)[A-Z0-9-]*\b')
        self.code_isin = re.compile(r'\b([A-Z]{2})([A-Z0-9]{9})([0-9]{1})\b')

        self.filename = re.compile(r'\b([A-Za-z0-9\(\)\. _,-])+(\.)(docx|docx?|xlsx?|pdf|png|jpg|pptx?|rtf|csv|txt)\b')
        self.quarter = re.compile(r'\bQ[1-4]\s*(19|20)\d{2}\b')
        self.duration1 = re.compile(
            r"\d+[\.,]?\d*\s*(?:\w+)?\s*(days?|hours?|minutes?)\s*(\d+[?.]?\d*\s*(days?|hours?|minutes?))?",
            re.IGNORECASE)
        self.duration = re.compile(
            r'\b((\d+)|(half|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety| ))+\s+(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b',
            re.IGNORECASE)
        self.time_point = re.compile(r'\b(today|tomorrow|tonight|yesterday)\b|\bnext\s(day|week|month|year)\b',
                                     re.IGNORECASE)
        self.time_frequecy = re.compile(
            r'\b(annualy|daily|forthnightly|hourly|monthly|nighthly|quarterly|weekly|yearly|bi-?weekly|Bi Weekly|every two weeks|every 2 weeks)\b')

        self.decimal=re.compile(r'\d+[,\.]\d')
        self.titleword=re.compile(r'\b[A-Z]\w+')
        self.rating=re.compile(r'\b(AAA|AA|A|BBB|BB|B)[+-]?')
        self.percentage=re.compile(r'-?[0-9]{1,3}[\.,][0-9]{1,3}\%?')
        self.filename=re.compile(r'([A-Za-z0-9\(\)\. _,-])+(\.)(docx|doc|xlsx|xls|pdf|png|jpg|pptx|ppt)')

    def get_regex_pattern(self, regex_name):
        pattern = getattr(self, regex_name, None)
        return pattern.pattern

    def read_regex_form_file(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()
            for l in lines:
                values=l.split(" = ")
                name=values[0]
                value=values[1]
                setattr(self, name, re.compile(r''+value))

if __name__ == '__main__':
    reg=Regex()
    reg.read_regex_form_file("/Users/mohamedmentis/Desktop/regex.py")
    print(reg.percentage)
