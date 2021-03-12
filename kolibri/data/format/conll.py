import logging

logger = logging.getLogger(__name__)


class ConllReader():
    """Reads markdown training data and creates a TrainingData object."""

    def __init__(self):
        self.training_examples = []
        self.separator=' '

    def reads(self, s, **kwargs):
        """Read markdown string and create TrainingData object"""

        if "separator" in kwargs:
            self.separator= kwargs["separator"]

        if "content" in kwargs:
            self.content_col=kwargs["content"]

        if "target" in kwargs:
            self.target_col=kwargs["target"]
        with open(s, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        item=[]
        i=0
        for line in lines:
            row=line.split(self.separator)
            if row[0]=='-DOCSTART-':
                if i<2:
                    print(i, item)

                self._parse_item(i, item)
                i+=1
                item=[]
            else:

                item.append(row)

        return self.training_examples

    def _parse_item(self,idx,  row):
        """Parses an md list item line based on the current section type."""
        self.training_examples.append(self._parse_training_example(idx, row))

    def _parse_training_example(self, idx, example):
        """Extract entities and synonyms, and convert to plain text."""
        print('example')


if __name__ == "__main__":
    conll=ConllReader()
    conll.reads("/Users/mohamedmentis/Documents/Mentis/Development/Python/opensource/NN/NeuroNER-master/neuroner/data/conll2003/en/conll2003_en.txt")
