from kolibri.tools.keywords import KeywordProcessor
from kolibri.tokenizer.structured_tokenizer import StructuredTokenizer
from kolibri.entities.entity import Entity
from kolibri.entities.dictionaryExtractor import DictionaryExtractor
import re, os
from kolibri.settings import resources_path

PACKAGE = 'corpora'
DATA_DIR = resources_path
GAZ_DIR = os.path.join(DATA_DIR, PACKAGE)

person_file_name = os.path.join(GAZ_DIR, 'gazetteers/first_name.txt')


class PersonExtractor(DictionaryExtractor):
    def __init__(self, case_sensitive=False):
        DictionaryExtractor.__init__(self, person_file_name, 'Person', case_sensitive=case_sensitive)
        self.tokenizer = StructuredTokenizer(component_config={}, generate_candidates=True)

    def get_entities(self, text):
        #    print(d)
        tokens = self.tokenizer.tokenize(text)

        persons = self.keywords.extract_keywords(text, True)

        # print(persons)

        FinalPersonns = []
        j = 0
        for person in persons:
            start = person[1]
            for i in range(j, len(tokens)):
                if start >= tokens[i].start and start < tokens[i].end:
                    if tokens[i].get('type') in ['CANDIDATE', 'ACRONYM']:
                        FinalPersonns.append(Entity(self.type, tokens[i].text, tokens[i].start, tokens[i].end))
                    elif i < len(tokens) - 1 and tokens[i + 1].get('type') in ['CANDIDATE', 'ACRONYM']:
                        FinalPersonns.append(
                            Entity(self.type, tokens[i].text + ' ' + tokens[i + 1].text, tokens[i].start,
                                   tokens[i + 1].end))
                    j = i + 1
        employeeids = []

        for person in FinalPersonns:
            person.value = re.sub(r"^(Hi|Hello|Dear|However|If|Employees?)\s", '', person.value)
            person.start = person.end - len(person.value)
            person.value = re.sub(r"'s$", '', person.value)
            person.end = person.start + len(person.value)
            pattern = re.escape(
                person.value) + r"[\s\(\[#]*(?P<EmployeeId>e?\d{4,8}\b)|\b(?P<EmployeeId2>e?\d{4,8}\b)[\s\)\]#]*" + re.escape(
                person.value)
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                for group, index in zip(match.groups(), range(0, len(match.group()))):
                    if group is not None:
                        employeeids.append(
                            Entity("EmployeeId", group, match.start(index + 1), match.end(index + 1)))

                # print(match.groups())
                # for groupidx in range(0, len(match.group())):
                #     if match.group(groupidx) is not None:
                #         employeeids.append(Entity("EmployeeId", match.group(groupidx), match.start(groupidx), match.end(groupidx)))

        FinalPersonns.extend(employeeids)
        return FinalPersonns


if __name__ == '__main__':
    text = """I'm trying to update my Workday profile and it's unclear how to accurately enter in past companies I've worked for. It won't recognize Takeda or Astellas. I get an error message and there's no directory."""
    pe = PersonExtractor(False)

    entities = pe.get_entities(text)

    for e in entities:
        print(e.tojson())
