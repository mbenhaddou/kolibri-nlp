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
from kolibri.data.vocabulary import Vocabulary
from kolibri.data.fields import SequenceLabelField
logger = logging.getLogger(__name__)


class Dataset(Iterable):
    """
    A batch of Instances. In addition to containing the instances themselves,
    it contains helper functions for converting the data into tensors.
    """

    def __init__(self, instances: Iterable[Document]) -> None:
        """
        A Batch just takes an iterable of instances in its constructor and hangs onto them
        in a list.
        """
        super().__init__()

        self.instances: List[Document] = ensure_list(instances)
        self._check_types()

    def _check_types(self) -> None:
        """
        Check that all the instances have the same types.
        """
        all_instance_fields_and_types: List[Dict[str, str]] = [
            {k: v.__class__.__name__ for k, v in x.fields.items()} for x in self.instances
        ]
        # Check all the field names and Field types are the same for every instance.
        if not all([all_instance_fields_and_types[0] == x for x in all_instance_fields_and_types]):
            raise Exception("You cannot construct a Batch with non-homogeneous Instances.")

    def get_padding_lengths(self) -> Dict[str, Dict[str, int]]:
        """
        Gets the maximum padding lengths from all ``Instances`` in this batch.  Each ``Instance``
        has multiple ``Fields``, and each ``Field`` could have multiple things that need padding.
        """
        padding_lengths: Dict[str, Dict[str, int]] = defaultdict(dict)
        all_instance_lengths: List[Dict[str, Dict[str, int]]] = [
            instance.get_padding_lengths() for instance in self.instances
        ]
        if not all_instance_lengths:
            return {**padding_lengths}
        all_field_lengths: Dict[str, List[Dict[str, int]]] = defaultdict(list)
        for instance_lengths in all_instance_lengths:
            for field_name, instance_field_lengths in instance_lengths.items():
                all_field_lengths[field_name].append(instance_field_lengths)
        for field_name, field_lengths in all_field_lengths.items():
            max_value = max(field_lengths)
            padding_lengths[field_name] = max_value
        return {**padding_lengths}

    def __add__(self, o):
        if o:
            return (Dataset(self.instances + o.instances))
        else:
            return self


    def get_recommended_padding_lengths(self):

        padding_lengths: Dict[str, Dict[str, int]] = defaultdict(dict)
        all_instance_lengths: List[Dict[str, Dict[str, int]]] = [
            instance.get_padding_lengths() for instance in self.instances
        ]
        if not all_instance_lengths:
            return {**padding_lengths}
        all_field_lengths: Dict[str, List[Dict[str, int]]] = defaultdict(list)
        for instance_lengths in all_instance_lengths:
            for field_name, instance_field_lengths in instance_lengths.items():
                all_field_lengths[field_name].append(instance_field_lengths)

        for field_name, field_lengths in all_field_lengths.items():
            padding_lengths[field_name] = sorted(field_lengths)[int(0.95 * len(field_lengths))]
        return {**padding_lengths}

    def get_data(self, namespace_x="tokens", namespace_y="label"):
        x_data=[]
        y_data=[]
        for d in self.instances:
            x_data.append([t.text for t in d.fields[namespace_x]])
            if isinstance(d.fields[namespace_y], SequenceLabelField):
                y_data.append([t for t in d.fields[namespace_y]])
            else:
                y_data.append(d.fields[namespace_y].label)
        return x_data, y_data

    def __iter__(self) -> Iterator[Document]:
        return iter(self.instances)

    def index_instances(self, vocab: Vocabulary) -> None:
        for instance in self.instances:
            instance.index_fields(vocab)

    def print_statistics(self) -> None:
        # Make sure if has been indexed first
        sequence_field_lengths: Dict[str, List] = defaultdict(list)
        for instance in self.instances:
            if not instance.indexed:
                raise Exception(
                    "Instances must be indexed with vocabulary "
                    "before asking to print dataset statistics."
                )
            for field, field_padding_lengths in instance.get_padding_lengths().items():
                for key, value in field_padding_lengths.items():
                    sequence_field_lengths[f"{field}.{key}"].append(value)

        print("\n\n----Dataset Statistics----\n")
        for name, lengths in sequence_field_lengths.items():
            print(f"Statistics for {name}:")
            print(
                f"\tLengths: Mean: {numpy.mean(lengths)}, Standard Dev: {numpy.std(lengths)}, "
                f"Max: {numpy.max(lengths)}, Min: {numpy.min(lengths)}"
            )

        print("\n10 Random instances: ")
        for i in list(numpy.random.randint(len(self.instances), size=10)):
            print(f"Instance {i}:")
            print(f"\t{self.instances[i]}")
