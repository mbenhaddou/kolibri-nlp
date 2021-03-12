from kolibri.tokenizer.sentence_splitter import split_single
import pandas as pd
from kolibri.tools.commonReg import Regex
import re
from kolibri.entities.templated_extractor import TemplatedEntityExtractor
from kolibri.entities.person_extractor import PersonExtractor
from kolibri.entities.regex_extractor import RegexExtractor
from kolibri.entities.dictionaryExtractor import DictionaryExtractor
from kolibri.entities.common_reg_extractor import CommonRegexExtractor
import csv, json, operator
import ast

reg = Regex()

#all_data = pd.read_excel('/Users/mbenhaddou/Documents/Mentis/Developement/Python/EntityExtractor/AUGUST COMPILATION ALL_samples_1to16Aug.xlsx   ', sheet_name='validated')
intent_ids = ['2050', '2162', '2079', '2084', '2090', '2103', '2113', '2149', '2174', '2185']

template_extractor = TemplatedEntityExtractor('../../data/nga/ressources/entities_Descriptions.csv')
person_extractor = PersonExtractor()
# leave_types = DictionaryExtractor('leaveType', 'LeaveType')
# company_name = DictionaryExtractor('companyNames.csv', 'Company')

dictionary_extractors = []

dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/leaveType', 'LeaveType', case_sensitive=False))
dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/bonus', 'BonusType', case_sensitive=False))

dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/companyNames.csv', 'Company'))
dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/countries', 'Country'))
dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/cities', 'City'))
dictionary_extractors.append(DictionaryExtractor('../../data/corpora/gazetteers/Job_Functions.txt', 'JobFunction', case_sensitive=False))
dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/allowances', 'Allowance', case_sensitive=False))
dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/changerequests', entity_type=None))
dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/payelements', 'PayElement', case_sensitive=False))
dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/payforms', 'payForm', case_sensitive=False))
dictionary_extractors.append(DictionaryExtractor('../../data/nga/ressources/ReportNames', 'ReportName', case_sensitive=False))
common_extractor = CommonRegexExtractor()

regex_extractors = []

regex_extractors.append(RegexExtractor(regexes=[r'\((?:UPI\s*)?(?P<EmployeeId>\d{6,8})\)', r'(?P<EmployeeId>\be\d+\b)',
                                                r'pern # (?P<EmployeeId>\b\d+\b)',
                                                r'empl(?:oyee)?(?:\sID#?)?\s+(?P<EmployeeId>\be?\d+\b)',
                                                r'(?P<EmployeeId>\b\d{8}\b)']))

regex_extractors.append(
    RegexExtractor(regexes=[r'(?P<WageType>\bWT\s*[A-Z0-9]{2,4}\b)', r'salary\s+(of\s)?(?P<Salary>([\.,\d]+))'],
                   case_sensitive=False))

regex_extractors.append(RegexExtractor(regexes=[r'(?P<PositionId>P\d{6})']))

regex_extractors.append(RegexExtractor(regexes=[
    r'(?:(?P<OriginalShift>IN(?:FT)?SHFT\d)(?:.*)\s*(?P<NewShift>IN(?:FT)?SHFT\d)(?:.*)|(?P<Shift>IN(?:FT)?SHFT\d))']))

regex_extractors.append(RegexExtractor(
    regexes=[r'wage\s+type[\s:](?P<PayElementType>\d+)', r'job title\s*:\s+(?P<JobTitle>(?:\w+\s){1,4})']))

regex_extractors.append(RegexExtractor(regexes=[
    r'Job\s+grade\s?(?:_|:|-|is|from|\s+)\s*(?P<OldPayGrade>\b[\d \/\(\)-]+)to\s(?P<NewPayGrade>[\d \/\(\)-]+)',
    r'Job\s+(?:code|title|code\/title)\s?(?:_|:|-|is|from|\s+)\s*(?P<OldJobCode>\b[\d \/\(\)-]+)to\s(?P<NewJobCode>[\d \/\(\)-]+)',
    r'Job\s+(?:code|grade|title|code\/title)\s?(?:_|:|-|is|to|\s+)\s*(?P<JobCode>\b[\d \/\(\)-]+\b)',
    r'Job\s+grade\s?(?:_|:|-|is|\s+)\s*(?P<PayGrade>\b[\d \/\(\)-]+\b)']))

regex_extractors.append(
    RegexExtractor(regexes=[r'ticket\s(?:\w+ ){0,7}\s?#?(?P<TicketID>\b\w*(?=\w*[0-9])(?=\w*\d)[A-Z0-9-]+\b)']))

regex_extractors.append(RegexExtractor(regexes=[
    r"(?P<Issue>(\w+ ){0,4}(stopped \w+ing|can't\sbe|still doesn't|I don't have|could not be|unable to|not able|issues? with|cannot|is not being|is not able|is not visible|not \w+ing|error message|doesn't seem to be|will not|problems? with|problems? \w+ing|issues? on)( \w+){0,6})"]))
sentence_breakers_starters = ['You are', 'Please']
regex_sentence_breakers = ".(?=" + "|".join(sentence_breakers_starters) + ")"

f = csv.re


def extra_cleaning(text):
    pattern = r"\*-*-+[\s\w+:\/\.,\(\)]+\*-+"
    text = re.sub(pattern, "", text, re.UNICODE)
    pattern = r'\*?-{2,}'
    text = re.sub(pattern, "", text, re.UNICODE)

    pattern = r'[.\]*Received\s*:[\w /:@\.-]*Attachments\s*:'
    return re.sub(pattern, "", text, re.UNICODE)


def split_string(text):
    sentences = []
    sentences_ = split_single(text)
    for sentence in sentences_:
        sentences.extend(re.split(regex_sentence_breakers, sentence))

    return sentences


def remove_overlap(entities):
    result = []
    current_start = -1
    current_stop = -1
    sorted_ents = [e for e in (sorted(entities, key=operator.attrgetter('start')))]

    for se in sorted_ents:
        if se.start > current_stop:
            # this segment starts after the last segment stops
            # just add a new segment
            result.append(se)
            current_start, current_stop = se.start, se.end
        else:
            current_entity = result[-1]

            if current_entity.type in ['City', 'Money', 'Person', 'Country']:
                result[-1] = se

            # current_start already guaranteed to be lower
            current_stop = max(current_stop, se.end)

    return result


def update_text_data(full_text, sents_ents):
    ents = []
    search_from = 0
    for se in sents_ents:
        start_index = se['sentence'][1]

        for entity in se['entities']:
            entity.start += start_index
            entity.end += start_index
            ents.append(entity)

    remove_overlap(ents)

    return {"text": full_text, "entities": ents}


def get_entities_for_sentence(sentence):
    entities = []
    #        print(sent)
    #        entities.extend(template_extractor.process(sent))
    #        print(sent)
    #        if len(entities) == 0:
    persons = person_extractor.get_entities(sentence[0])
    if len(persons) > 0:
        entities.extend(persons)
    for extractor in dictionary_extractors:
        entities.extend(extractor.get_entities(sentence[0]))
    entities.extend(common_extractor.process(sentence[0]))
    for extractor in regex_extractors:
        entities.extend(extractor.get_matches(sentence[0]))
    for entity in entities:
        entity.start+=sentence[1]
        entity.end+=sentence[1]
    return {"sentence": sentence, "entities": entities}

def get_entities_for_text(text):
    text = extra_cleaning(text)
    sentences = split_single(text)
    print('xxxxxxxxxxxxxxxxxxxxx')
    print(text)
    print('xxxxxxxxxxxxxxxxxxxxx')
    t_entities = template_extractor.process(text)

    sentences_entities = []
    for sent in sentences:
        sentences_entities.append(get_entities_for_sentence(sent))
    final = update_text_data(text, sentences_entities)

    final['entities'] = sorted(final['entities'], key=operator.attrgetter('start'))
    for en in final['entities']:
        t_entities.addEntity(en)
    t_entities.print()
    final['entities'] = t_entities.toJson()
    return final


text= """Information Classification: ll Limited Access\nTicket C6B-1025769\nGood morning,\nAs part of the Employee Relations team I am approving employee Michelle Murphy's (567391) request for a personal LOA per the above referenced ticket.\nI did not see the request form attached to the ticket.\nEmployee referenced it during our conversation.\nMichelle's LOA can be approved through Sept 2nd, with a return to work date of September 3, 2019.\nShe has indicated that she has exhausted her vacation time so this will be unpaid.\nPlease let me know if you have questions or need anything else from me.\n
"""
#text= re.sub(r'Reason for Leaving', 'HHHHHHHHHHHHHH', text, flags=re.IGNORECASE)
print(get_entities_for_text(text))
