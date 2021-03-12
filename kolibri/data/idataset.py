"""
A :class:`~Batch` represents a collection of ``Instance`` s to be fed
through a model.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Union, Iterator, Iterable

import numpy

from kolibri.utils import ensure_list
from kolibri.data.document import Document
from itertools import chain
from kolibri.data.fields import SequenceLabelField
from kolibri.utils import ReusableGenerator
logger = logging.getLogger(__name__)



class IDataset():
    """
    A generator of Instances. In addition to containing the instances themselves,
    it contains helper functions for converting the data into tensors.
    """

    def __init__(self, instances: Iterable[Document]) -> None:
        """
        A Batch just takes an iterable of instances in its constructor and hangs onto them
        in a list.
        """
        super().__init__()

        self.instances=instances


    def __add__(self, o):
        if o:
            return (IDataset(chain(self.instances , o.instances)))
        else:
            return self

    def get_data(self, namespace_x="tokens", namespace_y="label"):

        for d in self.instances:
            data=[]
            x_data=[t.text for t in d.fields[namespace_x]]
            if isinstance(d.fields[namespace_y], SequenceLabelField):
                y_data=[t for t in d.fields[namespace_y]]
            else:
                y_data=d.fields[namespace_y].label
            data.append((x_data, y_data))
            yield data


    def __iter__(self):
        return self.instances


