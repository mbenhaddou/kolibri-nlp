# -*- coding: utf-8 -*-
#!/usr/bin/env python

import re
from kolibri.settings import resources_path
import collections
from kolibri.data.cleaner.scripts.cleaning_scripts import fix_formating
from langdetect import detect
from kolibri.data.ressources import Ressources
import os
#import pycld2 as cld2
from math import sqrt
import gcld3

resources=Ressources()

filename_job_functions = resources.get('gazetteers/default/Job_Functions.txt').path
filename_disclaimer = resources.get('gazetteers/default/disclaimers.txt').path
filename_salutation=resources.get('gazetteers/default/salutations.txt').path
filename_email_closing=resources.get('gazetteers/default/email_closing.txt').path
language='en'
functions=open(filename_job_functions).readlines()
disclaimers=open(filename_disclaimer).readlines()
disclaimers=[d for d in disclaimers if d.strip()]
disclaimer_openings=[d.strip() for d in disclaimers]
salutation_opening_statements=[s.strip() for s in open(filename_salutation).readlines() if s.strip()!=""]
pattern_disclaimer = r"[\s*]*(?P<disclaimer_text>(" + "|".join(disclaimer_openings)+ ")(\s*\w*))"
pattern_salutation = r'(?P<salutation>(^(- |\s)*\b((' + r'|'.join(
    salutation_opening_statements) + r'))\b)( [A-Z][a-z]+){0,4},?)'

function_re = ''
for funct in functions:
    function_re += funct.strip('\n') + '|'

function_re = function_re[:-1]

function_re = r'(?P<signature>(([A-Z][a-z]+\s?)+)?(\s?[\|,]\s?)?({})(.+)?)'.format(function_re)


catch_all=r"[0-9A-Za-z一-龠ぁ-ゔァ-ヴー ÑÓżÉÇÃÁªçã$łÄÅäýñàźåüöóąèûìíśćłńé«»°êùáÀèôú⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎 \/@\.:,;\&\?\(\)'´s_\"\*[\]\%+<>#\/\+\s\t_=-]+"
catch_all_oneLine=catch_all.replace('\s', '')[:-1]
catch_all_oneLine=catch_all_oneLine[:1]+'\|'+catch_all_oneLine[1:]
lang_detector = gcld3.NNetLanguageIdentifier(min_num_bytes=0,
                                        max_num_bytes=1000)

regex_headers=[

    r"(From|To|De|Da|V[ao]n|发件人|Från)\s*:"+catch_all+"(((Subject|Objet|Oggetto|Asunto|Onderwerp|Betreff|主题|Ämne|Ass?unto|Tema)\s*:\s?)(?P<subject>("+catch_all_oneLine+"))|((Sent\sat|Enviado\sa|Enviada à\(s\)|Sent)\s*:"+catch_all_oneLine+"))",
    r"On\s+(\d{2}|Mon(day)?|Tue(sday)?|Wed(nesday)?|Thu(rsday)?|Friday|Sat(urday)?|Sun(day)?)"+catch_all+"(wrote):",
    r"\s{0, 10}(\d{1,2})?\s?(Jan|Feb|Mar|Apr|Mai|Jun|Jul|Aug|Sep|Nov|Oct|Dec)\s?(\d{1,2})?,\s+\d{2}:\d{2}\s+UTC$"

]
class EmailMessage(object):
    """
    An email message represents a parsed email body.
    """

    def __init__(self, language='en', split_pattern=None):
        self.fragments = []
        self.fragment = None
        self.found_visible = False
        self.language=language
        self.salutations=[s.strip() for s in open(filename_salutation).readlines() if s.strip()!=""]

        self.split_pattern=split_pattern
        self.closings=[c.strip() for c in open(filename_email_closing).readlines()  if c.strip()!=""]
        self.regex_header = r"|".join(regex_headers)
    def read(self, body_text, title_text=None):
        """ Creates new fragment for each line
            and labels as a signature, quote, or hidden.
            Returns EmailMessage instance
        """
        self.fragments=[]

        self.text = fix_formating(str(body_text))
        self.title=title_text
#        regex_header = r"(From|To)\s*:[0-9A-Za-zöóìśćłńéáú⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎\s\/@\.:,;\&\?\\\(\)'\"\*[\]<>#\/\+_-]+?((Subj(ect)?)|Sent at)\s?:|From\s*:[\w @\.:,;\&\(\)'\"\*[\]<>#\/\+-]+?(Sent|Date)\s?:(\s*\d+(\s|\/)(\w+|\d+)(\s|\/)\d+(\s|\/)?(\d+:\d+)?)?|From\s*:[\w @\.:,;\&\(\)'\"\*[\]<>#\/\+-]+?(Sent\s+at)\s?:(\s*\d+\s\w+\s\d+\s?\d+:\d+)?|From\s*:[\w @\.:,;\&\?\\\(\)'\"\*[\]<>#\/\+-]+?(CC)\s?:|From\s*:[\w @\.:,;\&\?\\\(\)'\"\*[\]<>#\/\+-]+?(To)\s?:|(De|Da)\s*:[0-9ÀA-Za-zéàçèêù\s\/@\.:,;\&\?\\\(\)'\"\*[\]<>#\/\+-]+(Objet|Oggetto)\s?:"
        if self.split_pattern:
            self.regex_header=r""+self.split_pattern
        starts = [m.start(0) for m in re.finditer(self.regex_header, self.text, re.MULTILINE | re.UNICODE)]

        if len(starts) < 1:
            starts = [m.start(0) for m in re.finditer(pattern_salutation, self.text, re.MULTILINE | re.IGNORECASE)]
            starts=[s for s in starts if s>150]
        if len(starts)<1:
            self.fragments.append(Fragment(self.text, self.salutations, self.closings, self.regex_header))

        else:
            if starts[0] > 0:
                starts.insert(0, 0)
            lines = [self.text[i:j] for i, j in zip(starts, starts[1:] + [None])]

            for line in lines:
                if self.split_pattern:
                    line=re.sub(self.split_pattern, '', line)
                if line.strip()!='':
                    self.fragments.append(Fragment(line, self.salutations, self.closings, self.regex_header))

        return self

    def get_languges(self):
        langs=[l.language for l in self.fragments]
        languages = collections.Counter()
        for d in langs:
            languages.update(d)
        if not languages:
            try:
                lang = lang_detector.FindTopNMostFreqLangs(self.title, num_langs=2)

            except:
                try:
                    lang = lang_detector.FindTopNMostFreqLangs(self.text, num_langs=2)
                except:
                    languages['und']=0.90

                    return languages

            for l in lang:
                    languages[l.language] = l.probability


        return max(languages, key=languages.get)


class Fragment(object):
    """ A Fragment is a part of
        an Email Message, labeling each part.
    """

    def __init__(self, email_text, salutations, closings, regex_header):


        self.salutations = salutations
        self.closings = closings
        self.body = email_text.strip()
        self.regex_header=regex_header
        self.is_forwarded_message = self._get_forwarded()
        self.title=None
        self.headers = self._get_header()
        self.caution=self._get_caution()
        if self.title is None:
            self.title=self._get_title()
        self.attachement = self._get_attachement()
        self.salutation = self._get_salutation()
        self.disclaimer = self._get_disclaimer()
        self.signature = self._get_signature()

        self._content = email_text

    def _get_title(self):
        patterns=[
            "(R[Ee]|F[Ww])\s?:\s?.+",
            ".*\s+(?=(Hi|Hello|Dear))"
            ]

        pattern = r'(?P<title>(' + '|'.join(patterns) + '))'
        groups = re.match(pattern, self.body)
        title = ""
        if groups is not None:
            if "title" in groups.groupdict().keys():
                title = groups.groupdict()["title"]
                self.body = self.body[len(title):].strip()
        return title
    def _get_caution(self):
        patterns=[
            "This message\scontains?\s[A-Z ]*.*\s+(Sensitivity: [\w ]+)?",
#            "\*-+\s+Sent\s+:.*\s+Received\s+:.*\s+Reply to\s:.*\s+Attachments\s+:.*\s+\*-*",
            "^##-\s+Please type your reply above this line\s+-##",
            "\[EXTERNAL EMAIL\].*",
            "\[EXTERNAL\].*",
            r"CAUTION\s.*",
            "Classified Personnel Information.*",
            "Please forward suspicious emails as attachments to .*",
            "For Internal Use Only.*",
            "(Importance|Importancia):\s+([\w+ ]+)",
            "Information Classification\s*:\s+([\w+ ]+)",
            "THIS\s+IS\s+A\s+MASS\s+COMM\s+UNICATION.+",
            "This is a secure, encrypted message.",
            "This message was sent securely using TLS.",
            "Verified Sender"
        ]
        pattern=r'(?P<caution>^\s*('+r'|'.join(patterns)+'))'

        matches = re.finditer(pattern, self.body, re.MULTILINE)
        cautions=[]
        for matchNum, match in enumerate(matches, start=1):
            caution=match.group()
            self.body=self.body.replace(caution, '')
            cautions.append(caution)

        # groups = re.match(pattern, self.body, re.MULTILINE)
        # caution=""
        # if groups is not None:
        #     if "caution" in groups.groupdict().keys():
        #         caution = groups.groupdict()["caution"]
        #         self.body = self.body[len(caution):].strip()
        return '\n'.join(cautions)

    def _get_attachement(self):
        pattern = r'(?P<attachement>(^\s*[a-zA-Z0-9_,\. -]+\.(png|jpeg|docx|doc|xlsx|xls|pdf|pptx|ppt))|Attachments\s?:\s?([a-zA-Z0-9_,\. -]+\.(png|jpeg|docx|doc|xlsx|xls|pdf|pptx|ppt)))'
        groups = re.match(pattern, self.body, re.IGNORECASE)
        attachement = ''
        if not groups is None:
            if "attachement" in groups.groupdict().keys():
                attachement = groups.groupdict()["attachement"]
                self.body=self.body[len(attachement):].strip()
        return attachement

    def _get_salutation(self):
        # Notes on regex:
        # Max of 5 words succeeding first Hi/To etc, otherwise is probably an entire sentence


        groups = re.match(pattern_salutation, self.body, re.IGNORECASE)
        salutation = ''
        if groups is not None:
            if "salutation" in groups.groupdict().keys():
                salutation = groups.groupdict()["salutation"]
                self.body = self.body[len(salutation):].strip()
        return salutation
    @property
    def language(self):
        return_val = {}
        regx = "\*?-+\s+Sent\s+:.*\s+Received\s+:.*\s+Reply to\s:.*\s+Attachments\s+:.*\s+\*?-*|Dear Sender, thank you for your e-mail. I'll be out of office until.*|NO BODY.*|[^\w.,:\s]"
        text=self.body
        text=re.sub(regx, ' ', text.strip())

        if len(text.strip()) >0:
            try:
                lang = lang_detector.FindTopNMostFreqLangs(text=text, num_langs=2)
                for l in lang:
                    return_val[l.language]=l.probability*sqrt(len(text))
            except:
                pass
            try:
                lx, v, lang_cld=cld2.detect(text)
                langs=set(['zh' if 'zh-' in l[1] else l[1] for l in lang_cld])

                if {'ko', 'zh-cn'}.intersection(set(return_val.keys())) or { 'ko', 'zh'}.intersection(langs):
                    return_val={}
                    for l in lang_cld:
                        return_val[l[1]]=(l[2]/100)*sqrt(len(text))
            except:
                pass

        return return_val

    def _get_header(self):
#        regex = r"From\s*:[\w @\.:,;\&\?\\\(\)'\"\*[\]<>#\/\+-]+?(Subj(ect)?)\s?:|From\s*:[\w @\.:,;\&\(\)'\"\*[\]<>#\/\+-]+?(Sent|Date)\s?:(\s*\d+(\s|\/)(\w+|\d+)(\s|\/)\d+(\s|\/)?(\d+:\d+)?)?|From\s*:[\w @\.:,;\&\(\)'\"\*[\]<>#\/\+-]+?(Sent\s+at)\s?:(\s*\d+\s\w+\s\d+\s?\d+:\d+)?|From\s*:[\w @\.:,;\&\?\\\(\)'\"\*[\]<>#\/\+-]+?(CC)\s?:|From\s*:[\w @\.:,;\&\?\\\(\)'\"\*[\]<>#\/\+-]+?(To)\s?:"

        pattern = r"(?P<header_text>("+self.regex_header+"))"

        groups = re.search(pattern, self.body)
        header_text = None
        if groups is not None:
            if "header_text" in groups.groupdict().keys():
                header_text = groups.groupdict()["header_text"]
                self.body=self.body[len(header_text):].strip()
            if 'subject' in groups.groupdict().keys():
                self.title = groups.groupdict()["subject"]
        return header_text

    def _get_disclaimer(self):


        groups = re.search(pattern_disclaimer, self.body, re.MULTILINE+re.DOTALL)
        disclaimer_text = None
        if groups is not None:
            if "disclaimer_text" in groups.groupdict().keys():
                found = groups.groupdict()["disclaimer_text"]
                disclaimer_text = self.body[self.body.find(found):]
                self.body = self.body[:self.body.find(disclaimer_text)].strip()

        return disclaimer_text

    def _get_signature(self):
        # note - these openinged statements *must* be in lower case for
        # sig within sig searching to work later in this func

        # TODO DRY
        self.signature=''
        sig_opening_statements = self.closings

        pattern = r'(?P<signature>(^|\.\s)\s*\b(' + '|'.join(sig_opening_statements ) + r')(,|.)?\s)'

        groups = re.search(pattern, self.body, re.IGNORECASE | re.MULTILINE)
        signature = None
        if groups:
            if "signature" in groups.groupdict().keys():
                signature1 = groups.groupdict()["signature"]
                # search for a sig within current sig to lessen chance of accidentally stealing words from body
                sig_span=groups.span()
                signature = self.body[sig_span[0]:]
                self.body=self.body[:sig_span[0]]
                groups = re.search(pattern, signature[len(signature1):], re.IGNORECASE)
                if groups:
                    signature2 = groups.groupdict()["signature"]
                    sig_span=groups.span()
                    self.body = self.body+'\n'+signature[:len(signature1)+sig_span[0]]
                    signature=signature[sig_span[0]]
        return signature

    def _get_forwarded(self):

        pattern = '(?P<forward_text>([- ]* Forwarded Message [- ]*|[- ]* Forwarded By [- ]*|[- ]*Original Message[- ]*))'
        groups = re.search(pattern, self.body, re.DOTALL)
        forward = None
        if groups is not None:
            if "forward_text" in groups.groupdict().keys():
                forward = groups.groupdict()["forward_text"]

        if forward is not None:
            self.body = self.body.replace(forward, '')

        return forward is not None

    @property
    def content(self):
        return self._content.strip()




if __name__ =="__main__":
    import pandas as pd

    mail="""
    Yes she did return to work.
  
 From: GBClaims@thehartford.com <GBClaims@thehartford.com> 
 Sent: Monday, February 24, 2020 11:28 AM 
 To: Bundy, Kalman <Kalman.Bundy@bsci.com>; Hargraves, Brian <Brian.Hargraves@bsci.com>; HRConnectUSBenefits <HRConnectUSBenefits@bsci.com> 
 Subject: {External} LEAVE NOTIFICATION - Action Needed - Return to Work Verification Request for UFON, G. - Claim #: 25310794
  
 
 
 RETURN TO WORK VERIFICATION REQUEST NOTICE - Supervisor Action Required 
  
  Employee Information 
 Employee Name: GOODNEWS UFON 
 Employee ID: 1081409 
 Leave Reason: Employee's own health condition 
 
 You are receiving this notice as the manager for the above referenced employee. 
 
 Absence Detail 
 Date(s) of Absence: From 1/30/2020 through 2/19/2020 
 Return to Work Date: 2/20/2020 
 
 Supervisor Action Required 
 Our records indicate the mentioned employee returned to work full duty on 2/20/2020. Please respond to this email by 02/26/2020 to confirm this return to work date.
 
 
 
 - You must let The Hartford, the HR Business Partner, and the HR Service Center know by selecting the REPLY ALL. 
 - If the RTW is not confirmed with The Hartford it will affect Goodnews pay, training, and system access will be impacted 
  
 What happens next? 
 If Goodnews will use vacation time before returning to work:
 
 
 
 - For Salaried Exempt Employees:You will need to complete a Payroll Action Form (PAF) here:  http://myteam.bsci.com/sites/kronossupport/SitePages/Kronos%20Home.aspx and enter her vacation time into Kronos. 
 - For Hourly Non-Exempt employees - You will need to enter Goodnews's vacation time in Kronos. If you need help entering vacation time, please contact KronosTechSupTeam@bsci.com 
  You may contact me at 1-800-308-2386, extension2302180 if you have any questions regarding this message. 
 
 Thank you, 
 
 YVETTE DAVIS 
 SR ABILITY ANALYST 
 
 The Hartford® is The Hartford Financial Services Group, Inc. and its subsidiaries, including underwriting companies Hartford Life and Accident Insurance Company and Hartford Fire Insurance Company. Home Office is Hartford, CT. The Hartford is the administrator for certain group benefits business written by Aetna Life Insurance Company and Talcott Resolution Life Insurance Company (formerly known as Hartford Life Insurance Company).  The Hartford also provides administrative and claim services for employer leave of absence programs and self-funded disability benefit plans.
 
   
 
  ************************************************************ 
 This communication, including attachments, is for the exclusive use of addressee and may contain proprietary, confidential and/or privileged information.  If you are not the intended recipient, any use, copying, disclosure, dissemination or distribution is strictly prohibited.  If you are not the intended recipient, please notify the sender immediately by return e-mail, delete this communication and destroy all copies. 
 ************************************************************   
    """
    sd="Message from KM_C258"
    email = EmailMessage().read(mail, sd)
    print(email.get_languges())
    print('\n'.join([f.title+'\n'+f.body for f in email.fragments]))

    # mails=pd.read_excel("/Users/mohamedmentis/Downloads/TRY_ToBeDeleted_Week9_prediction_results.xlsx", "Sheet1", engine='openpyxl')
    # nb_rows=len(mails.index)
    #
    # for index, row in mails.iterrows():
    #     if index%1000==0:
    #         print(index/nb_rows)
    #
    #     email=EmailMessage().read(row['PRD Description'], row['PRD ShortDescription'])
    #     mails.at[index, 'Mentis_lang']= email.get_languges()
    #     mails.at[index, 'LAB_Desc']= '\n'.join([f.title+'\n'+f.body for f in email.fragments])
    #
    # mails.to_excel("/Users/mohamedmentis/Downloads/TRY_ToBeDeleted_Week9_prediction_results2.xlsx",
    #              sheet_name='Sheet_name_1', engine='openpyxl')
