import logging
import pathlib

import jsonpickle
import tqdm

from kolibri.data.document import Document
from kolibri.data.idataset import IDataset

logger = logging.getLogger(__name__)

class DatasetReader():
    """
    A ``DatasetReader`` turn a file containing a dataset into a collection
    of ``Document`` s.

    """

    def __init__(self, token_indexers) -> None:
        self._token_indexers=token_indexers

    def read(self, file_path: str):
        """
        Returns an ``Iterable`` containing all the instances
        in the specified dataset.
        """


        instances = self._read(file_path)

            # Then some validation.
        if not isinstance(instances, list):
            instances = [instance for instance in tqdm.tqdm(instances)]
        if not instances:
            raise Exception(
                    "No instances were read from the given filepath {}. "
                    "Is the path correct?".format(file_path)
                )

        return instances


    def get_dataset(self, file_path):
        return IDataset(self._read(file_path))


    def _read(self, file_path: str):
        """
        Reads the instances from the given file_path and returns them as an
        `Iterable`.
        """
        raise NotImplementedError


    def text_to_document(self, *inputs) -> Document:
        """
        Does whatever tokenization or processing is necessary to go from textual input to an
        ``Instance``.
        """
        raise NotImplementedError

    def serialize_instance(self, instance: Document) -> str:
        """
        Serializes an ``Instance`` to a string.
        """

        return jsonpickle.dumps(instance)

    def deserialize_instance(self, string: str) -> Document:
        """
        Deserializes an ``Instance`` from a string.  We use this when reading processed tokenizers from a
        cache.
        """

        return jsonpickle.loads(string)  # type: ignore
