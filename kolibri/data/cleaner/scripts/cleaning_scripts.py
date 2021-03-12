import re, csv
#from kolibri.data.cleaner.scripts.email2text import EmailMessage
import string




def case_sensitive_replace(string, old, new):
    """ replace occurrences of old with new, within string
        replacements will match the case of the text it replaces
    """
    def repl(match):
        current = match.group()
        result = ''
        all_upper=True
        for i,c in enumerate(current):
            if i >= len(new):
                break
            if c.isupper():
                result += new[i].upper()
            else:
                result += new[i].lower()
                all_upper=False
        #append any remaining characters from new
        if all_upper:
            result += new[i+1:].upper()
        else:
            result += new[i+1:].lower()
        return result

    old_re = r"\b{}\b".format(old)
    old_p_re = r"\b{}\b\.".format(old)
    regex = re.compile(old_re, re.I)
    regex_p = re.compile(old_p_re, re.I)

    #print(f"[{repl}][{string}]")

    string=regex_p.sub(repl, string)
    return regex.sub(repl, string)

def clean_email_all(text):
    if text is None:
        return ""

    text = fix_contractions(text)
    text = clean(text)
    text = abstract_email(text)
    return text.lower()

# def clean_email_all_parse(text):
#     if text is None:
#         return ""
#     text = parse_email(text)
#     text = clean_email_all(text)
#     return text

# def parse_email(email):
#     # remove URL's
#     text=str(email)
#     if text is None or text=='nan':
#         return text
#
#     text = re.sub(r'[*-\.=_>]{6,}', '', text)
#     text= text.replace('\\r', '\n')
#     text = re.sub(u'\*\*\*Confidential - For Company Internal Use Only\*\*\*', '', text)
#     text = re.sub(u'\*\*\*\s*Highly Confidential - For Company Internal Use by Authorized Personnel Only\s*\*\*\*',
#                       '', text)
#     text = re.sub("Sent from Gmail Mobile", '', text)
#     text = re.sub("Short description:", '', text)
#     text = re.sub(
#             "\*\*\*ATTENTION: Employee could not select a manager,therefore this e-mail has been forwarded to the SYSTEMADMINISTRATOR. Please forward e-mail to Payroll\*\*\*",
#             '', text)
#     text=re.sub(r'Sent\s:.*\s*Received\s:.*\s*Reply to\s:.*\s* Attachments\s:.*\s', '', text)
#     text=re.sub('"From:', 'From:', text)
#     if '\n' in text:
#         s=[line.strip() for line in text.split('\n') if line.strip() != '']
# #        s=[x if x[-1:] in ['.', '!',',', '?', ':', ';'] else x + '.' for x in s]
#
#         text = '\n'.join(s)
#
#     email = EmailMessage(text).read()
#     text = '\n'.join([fg.body.strip() for fg in email.fragments])
#     emails=[]
#     mail={}
#     for f in email.fragments:
#         emails.append({'salutation': f.salutation, 'body':f.body, 'signature': f.signature, 'disclaimer': f.disclaimer})
#
#     text = re.sub(u"##- Please type your reply above this line -##", '', text)
#     text = re.sub(u'(Information )?Classification:\s*(Highly Confidential|Internal|Public|Confidential|(ll\s?)?Limited Access)', '', text)
#
#     #    return emails
#     return text

def fix_contractions(email):

    return email


def fix_formating(text):

    text = text.replace(u'\\xa333', u' ')
    text = text.replace(u'\\u2019', u'\'')

    text = text.replace(u'\\xb4', u'\'')
    text = text.replace(u'\\xa0', u' ')
    text = text.replace(u'\\xa0', u' ')
    text = text.replace(u'f\\xfcr', u'\'s')
    text = text.replace(u'\\xa', u' x')
    text = text.replace(u'x000D', u'\n')
    text = text.replace(u'.à', u' a')
    text = text.replace(u' ', u'')
    text = text.replace('...', '.')
    text = text.replace('..', '.')
    text = text.replace(' .', '. ')
    text = text.replace('\r\n', '\n')
    text = text.replace('\xa0', ' ').replace('：', ': ').replace('\u200b', '').replace('\u2026', '...').replace('’', "'")

    return text

def clean(text):
        text = str(text)
        # remove URL's
        # fix puntuations

        text = text.replace('\xa0', ' ').replace('：', ': ').replace('\u200b', '').replace('\u2026', '...').replace('’', "'")
        text = text.replace(u'\\xa333', u' ')
        text = text.replace(u'\\u2019', u'\'')
        text = text.replace(u'\\xb4', u'\'')
        text = text.replace(u'\\xa0', u' ')
        text = text.replace(u'\\u2013', '-')
        text = text.replace(u'\\xa0', u' ')
        text = text.replace(u'\\u1427', '')
        text = text.replace("x000D", '\\n')  ## added to take into account newlines
        text = text.replace(u'f\\xfcr', u'\'s')
        text = text.replace(u'\\xa', u' x')
#        text = text.replace(u'//', '.')
        text = text.replace(' / ', ' - ')
#        text = text.replace('...', '.')
#        text = text.replace('..', '.')
        text = text.replace('\\n', '. ')
        text = text.replace('\\r', '. ')
        text = text.replace(' .', '. ')
        text = re.sub(r'\b(FW|RE|Fwd|AW)\s*:', '', text, flags=re.I)

        if len(text.strip()) == 0:
            return text.strip()
        PUNCTUATION = string.punctuation
        PUNCTUATION += ' '
        while text[0] in PUNCTUATION:
            text = text[1:]
            if len(text.strip()) == 0:
                return text.strip()

        while text[-1] in PUNCTUATION:
            text = text[:-1]
            if len(text.strip()) == 0:
                return text.strip()
#        text = re.sub(r'\!+|#+|"+|\*+', '.', text)
        return text.strip() + '.'

# def clean_email(email):
#     return clean(fix_formating(parse_email(fix_contractions(email))))

# def clean_all(emails):
#     cleaned_emails=[]
#     for email in emails:
#         cleaned_emails.append(clean_email(email))
#     return cleaned_emails


def abstract_email(email):
    text = email
    # remove URL's
    text = re.sub(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", '<WEBURL>', text)
    text = re.sub(r"([\w\!\#$\%\&\'\*\+\-\/\=\?\^\`{\|\}\~]+\.)*[\w\!\#$\%\&\'\*\+\-\/\=\?\^\`{\|\}\~]+@((((([a-z0-9]{1}[a-z0-9\-]{0,62}[a-z0-9]{1})|[a-z])\.)+[a-z]{2,6})|(\d{1,3}\.){3}\d{1,3}(\:\d{1,5})?)",
        '<EMAIL>', text)
    text = re.sub(r"\b(1(\s|-)?)?\(?[0-9]{3}\)?\s*[\.-]?[0-9]{3,4}[\.\s\-][0-9]{4}(\sext\.\s*\d+)?\b", ' <PHONENUMBER>', text)
    text = re.sub(r"(\+91)\s\(?\d{2,3}\)?\s*[\.-]?[0-9]{3,4}[\.\s\-]?[0-9]{4}(\sext\.\s*\d+)?\b", ' <PHONENUMBER>', text)
    text = re.sub(r"(?:[0123]?[0-9][-\./]\w+[-\./][12][0-9][0-9][0-9])(\s?\d{2}[:]\s?\d{2}[:]\s?\d{2})?(\sAE(S|D)T)?",  ' <DATE>', text)
    text = re.sub(r'FY\d{2,4}\b', '<FISCALTEAR>', text)
    text = re.sub(r'\b(weeks?|wks?)\s*\d{1,2}(\s*\&\s*\d{1,2})?\d', '<FISCALTEAR>', text)
    text = re.sub(r'\b(weeks?|wks?)\s*\d{1,2}(\s*\&\s*\d{1,2})?\b', '<WEEK>', text, flags=re.I)

    #someheaders are still there
    text=re.sub(r'(file name:|file|\-)(.*)(\.(xlsx?|docx?|xlsm|pdf|txt|csv))', '\g<1> <FILE>', text, flags=re.I)
    text=re.sub(r'(file|\-)(.*)(successfully)', '\g<1> <FILE> \g<3>', text, flags=re.I)
#    text=re.sub(r'\b[a-zA-Z0-9._-]+.xls\b', '<FILE>', text)
    text = re.sub(r'\bhrc\d+\b', '<HR_CASE_NUMBER>', text, flags=re.I)
    text = re.sub(r'To:\.*<<EMAIL>>', '', text)
    text = re.sub(r'\bHA-\d{6}-([0-9A-Z-]+)\b', '<REQUESTID>', text)
    text = re.sub(r'\b((Req(uest)?\s+(ID|number)\s*[.:])|request)\s*\w{2}(\d{3,}-?)+\b', '<REQUESTID>', text, flags=re.I)
    text = re.sub(r'(\[\s*)?ref:[a-z0-9_\.:]+(\s*\])?', '<REFERENCE_NUMBER>', text, flags=re.I)
    text = re.sub(r'(EmployeeID\s?=\s?)(\d{5,8})', 'EmployeeID = <EMPLOYEEID>', text)
    text=re.sub(r'(£|€|\$|¥|CHF|Rs|=(\.|\s?:)?)\s*-?([0-9,\.]+)\b', '<MONEY>', text)

    text = re.sub(r"\b\d{5}([ \-]\d{4})?\b", '<ZIPCODE>', text)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '<SOCIALSECURITYNUMBER>', text)
    text = re.sub(r'((ticket(id)?)|TICKETID)\s?[#:]?\s?\d{7}', 'ticket <TICKETID>', text)

    text = re.sub(r'pay is\s+:?\s?(\d+([\.,])?)+', 'pay is <MONEY>', text)
    text = re.sub(r'allowances of\s+:?\s?(\d+([\.,])?)+', 'pay is <MONEY>', text)
    text = re.sub(r'([0-9\.,]+)\s?(dollars?|USD|INR|rs)\b', '<MONEY>', text, flags=re.I)
    text = re.sub(r'\b\d+%\s', '<PERCENT> ', text)
    text = re.sub(r'\b\d+([\.,]\d+)?\s*\.?(h(ou)?rs?|days?|w(ee)?ks?)\b', '<DURATION>', text)
    text = re.sub(r'\b401k|403b|457b\b', '<RETIREMENT_PLAN>', text, flags=re.I)
    text = re.sub(r'\b\d+k\b', '<MONEY>', text, flags=re.I)
    text = re.sub(r'\bp45|p60|p11d\b', '<PAYE_FORM>', text, flags=re.I)
    text = re.sub(r'\bir56a\b', '<TAX_FORM>', text, flags=re.I)
    text = re.sub(r'\bir56f\b', '<TERMINATION LETTER>', text, flags=re.I)

    text= re.sub(r'\b((\d+)|(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety| ))\s+(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b', '<DURATION>', text)
    text = re.sub(r'\b(e|perner\.?)?\d{5,8}\b','<EMPLOYEEID>', text, flags=re.I)
    text = re.sub(r'\b(?<!-)\d{7,9}\b\b(?!-)', '<EMPLOYEEID>', text)
    text = re.sub(r'\b(\d{1,2})(\s|-)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s\d{1},?(\s\d{2,4})?\b', '<DATE>', text, flags=re.I)

    text = re.sub(r'\b((1st|2nd|\d{1,2}rd)|(\d{1,2})(th|st)?)(\s|-)?(J(?:an(uary)?|u(?:ne?|ly?))|Feb(ruary)?|Ma(?:r(ch)?|y)|A(?:pr(il)?|J|ug(ust)?)|(?:(?:(?:Sept?|Nov|Dec)(em)?)|Octo?)(ber)?),?(\s|-|\')?\d{2,4}(\s\d{2}:\d{2}(\s?(AM|PM))?)?\b', ' <DATE>', text, flags=re.I)
    text = re.sub(r'\b((1st|2nd|\d{1,2}rd)|(\d{1,2})(th|st)?)(\s|-)?(J(?:an(uary)?|u(?:ne?|ly?))|Feb(ruary)?|Ma(?:r(ch)?|y)|A(?:pr(il)?|J|ug(ust)?)|(?:(?:(?:Sept?|Nov|Dec)(em)?)|Octo?)(ber)?)\b', ' <DATE>', text, flags=re.I)
    text=re.sub(r'\b(((Mon|Tues?|Wed(nes)?|Thu(rs)?|Fri|Sat(ur)?|Sun))(day)?,?\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+((1st|2nd|\d{1,2}rd)|(\d{1,2})(th)?)\b', '<DATE>', text, flags=re.I)
    text = re.sub(
        r'((\d{2})\s)?(J(?:anuary|u(?:ne|ly))|February|Ma(?:rch|y)|A(?:pril|ugust)|(?:(?:(?:Sept|Nov|Dec)em)|Octo)ber),?(\s(1st|2nd|\d{1,2}(th|st)?,?))?(\s\d{4})?(\s*\d{2}:\d{2})?\b', ' <DATE> ', text)
    text = re.sub(r'((Mon|Tues?|Wed(nes)?|Thu(rs)?|Fri|Sat(ur)?|Sun))(day)?\s*\d{1,2}(st|th)?([\.\\-]\d{1,2})?(\s*(a|p)\.?m\.?)?', '<DATE>', text)
    text = re.sub(r'\b(J(?:an(uary)?|u(?:ne?|ly?))|Feb(ruary)?|Ma(?:r(ch)?|y)|A(?:pr(il)?|J|ug(ust)?)|(?:(?:(?:Sept?|Nov|Dec)(em)?)|Octo?)(ber)?)(,|\s*-)?(\s*(1st|2nd|\d{1,2}(th)?,?))?(\s\d{4})?(\s*\d{2}:\d{2})?\b', '<DATE>', text, flags=re.I  )
    text = re.sub(r'\b(J(?:anuary|u(?:ne|ly))|February|Ma(?:rch|y)|A(?:pril|ugust)|(?:(?:(?:Sept|Nov|Dec)em)|Octo)ber)(\s?\d{2,4})\b',
        ' <DATE> ', text, flags=re.I)

    text=re.sub(r'\b\d{1,2}(:\d{2})?\s*(a|p)\.?m\.?\b', '<HOUR>', text, flags=re.I)

    text = re.sub(r"\b\d{1,2}(\.|/|-)\d{1,2}(\.|/|-)\d{2,4}\b", ' <DATE> ', text)


    text = re.sub(r"\b201[0-9]\b", '<YEAR>', text)
    text = re.sub(r'\bon \d{8}', 'on <DATE>', text)


    text = re.sub(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\. ', '<MONTH>', text)


 #   text = re.sub(r'\b([0-9-]+[A-Z-]+)+\b', '<CODE>', text)
    text = re.sub(r'\b(([A-Z]{1,})([0-9]{1,})([A-Z]+)?){3,}\b', '<CODE>', text)
    text = re.sub(r'#\s+?\d+', '<NUMBER>', text)


    text = re.sub(r'\b\d+(,)\d{3}(.)\d{2}\b', '<MONEY>', text)
    text = re.sub(r'\b\d+\.\d{3}(,)\d{2}(\s*€|\b)?', '<MONEY>', text)
    text=re.sub(r'\b(\d{1,2}(/|-)\d{2,4})|(\d{4}(-|/)\d{2})\b', '<DATE>', text)
    text=re.sub(r'\b[0-3][0-9][0-1][0-9]20[1-2][0-9]\b', '<DATE>', text)
    text = re.sub(r'\b([-+]?\d*[\.,]\d{2,}|\d{2,})\b', '<CARDINAL>', text)

    return text.strip()


def fix_sentence(sentence):

    sentence=sentence.strip()
    sentence = re.sub(r'(\s+Hi (\w+),)', '. Hi \g<2>', sentence, flags=re.I)
    sentence = re.sub(r'^(Hi)\s+(All|Team|NGA)(?!,)', '\g<1> \g<2>,', sentence, flags=re.I)
    sentence = re.sub(r'^(Hi)\s(?!(All|Team|NGA),)', 'Hi,', sentence, flags=re.I)
    sentence = re.sub(r'^(Hi),\s(All|Team|NGA)', '\g<1> \g<2>,', sentence, flags=re.I)
    sentence=sentence.replace('.Kindly', '. Kindly')

    sentence = re.sub(r'^(Hello)(?!,)', 'Hello,', sentence, flags=re.I)

    sentence = re.sub(r'\bI navigated\b', 'Agent navigated', sentence)
    sentence = re.sub(r'\.Informed\b', '. Informed', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r' / ', ' and ', sentence)
    sentence = re.sub(r'Navigated the Employee ', 'Agent navigated the employee', sentence, flags=re.I)
    sentence = re.sub(r'(\bam\s+I\b)', ' the employee is ', sentence)
    sentence = re.sub(r'(^I am | am )', ' employee is ', sentence)
    sentence = re.sub(r'\bI\b', 'Employee', sentence)
    sentence = re.sub(r'\bhe\b', 'employee', sentence)
    sentence = re.sub(r'\b(m|M)y\b', 'Employee\'s', sentence)
    sentence = re.sub(r'^Provided', 'Agent provided', sentence)
    sentence = re.sub(r'Explained', 'Agent explained', sentence)
    sentence = re.sub(r' called in saying that (he|she) ', ' ', sentence)
    sentence = re.sub(r' called in to know ', ' wanted ', sentence)
    sentence = re.sub(r'employee claims he ', 'emplpyee ', sentence, flags=re.I)
    sentence = re.sub(r'called to find out ', 'wants to know ', sentence, flags=re.I)
    sentence = re.sub(r'\bI advised\b', 'Agent advised', sentence)
    sentence = re.sub(r'\badvised\b', 'Agent advised', sentence, flags=re.I)
    sentence = re.sub(r'\bID\b', 'Id', sentence)

    return sentence


if __name__ == '__main__':
    mail="To access HireRight's secure website, please click the following link and use the case-sensitive, individualized login information provided below: https://ows01.hireright.com/ac2.html?key=4A1B8DAA62EB35613E66EF0FDFA8BDF3&referrer=email "
    print(abstract_email(mail))
