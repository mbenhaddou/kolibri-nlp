from .utils import Dict
from .utils import ordered
from kolibri.utils import lazyproperty

class Document(Dict):
    def __init__(self, text="", data=None, output_properties=None, time=None):
        self.raw_text = text
        self.time = time
        if data:
            super(Dict, self).__init__(data)

        if output_properties:
            self.output_properties = output_properties
        else:
            self.output_properties = set()

    def set_output_property(self, prop):
            self.output_properties.add(prop)
    @property
    def text(self):
        if "clean" in self:
            return self["clean"]
        return self.raw_text
    def as_dict(self, only_output_properties=False):
        if only_output_properties:
            d = {key: value
                 for key, value in self.items()
                 if key in self.output_properties}
            return dict(d, text=self.text)
        else:
            d = self
        return dict(target=d.target, text=self.text)

    def __eq__(self, other):
        if not isinstance(other, Document):
            return False
        else:
            return ((other.text, ordered(other.data)) ==
                    (self.text, ordered(self.data)))

    def __hash__(self):
        return hash((self.text, str(ordered(self.data))))

    @classmethod
    def build(cls, text, aClass=None, entities=None):
        data = {}
        if aClass:
            data["target"] = aClass
        if entities:
            data["entities"] = entities
        return cls(text, data)
