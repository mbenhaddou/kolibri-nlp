from kolibri.tools.keywords import KeywordProcessor
from kolibri.entities.entity import Entity
from kolibri.utils.downloader import Downloader
from kolibri.settings import resources_path
import os




class DictionaryExtractor():
    def __init__(self, ressource, entity_type, resource_type='file', case_sensitive=True):

        self.case_sensitive=case_sensitive
        self.keywords = KeywordProcessor(case_sensitive=case_sensitive)
        self.type=entity_type
        if resource_type== 'dict':
            self.keywords.add_keywords_from_dict(ressource)
        elif resource_type=='list':
            self.keywords.add_keywords_from_list()
        else:
            self.keywords.add_keyword_from_file(ressource)




    def get_entities(self, text):

        results=self.keywords.extract_keywords(text, True)

        if self.type is None:
            return [Entity(result[0], text[result[1]:result[2]], result[1], result[2]) for result in results]

        return [Entity(self.type, result[0], result[1], result[2]) for result in results]


if __name__=='__main__':
    dict_extctr=DictionaryExtractor()