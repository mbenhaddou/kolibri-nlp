import re
import gc
from kolibri.dataset.corpusreader import CorpusReader
from kolibri.data import find
TRY_ZIPFILE_FIRST = True

class LazyCorpusLoader(object):
    """
    lazy dataset loader from nltk.
    """

    def __init__(self, name, reader_cls, *args, **kwargs):

        assert issubclass(reader_cls, CorpusReader)
        self.__name = self.__name__ = name
        self.__reader_cls = reader_cls
        # If nltk_data_subdir is set explicitly
        if 'kolibri_data_dir' in kwargs:
            # Use the specified subdirectory path
            self.subdir = kwargs['kolibri_data_dir']
            # Pops the `nltk_data_subdir` argument, we don't need it anymore.
            kwargs.pop('kolibri_data_dir', None)
        else:  # Otherwise use 'data/corpora'
            self.subdir = 'data/corpora'
        self.__args = args
        self.__kwargs = kwargs

    def __load(self):
        # Find the dataset root directory.
        print(self.__name)
        zip_name = re.sub(r'(([^/]+)(/.*)?)', r'/\1/\2.zip', self.__name)
        if TRY_ZIPFILE_FIRST:
            try:
                root = find('{}/{}'.format(self.subdir, zip_name))
            except LookupError as e:
                try:
                    root = find('{}/{}'.format(self.subdir, self.__name))
                except LookupError:
                    raise e
        else:
            try:
                root = find('{}/{}'.format(self.subdir, self.__name))
            except LookupError as e:
                try:
                    root = find('{}/{}'.format(self.subdir, zip_name))
                except LookupError:
                    raise e

        # Load the dataset.
        corpus = self.__reader_cls(root, *self.__args, **self.__kwargs)

        # This is where the magic happens!  Transform ourselves into
        # the dataset by modifying our own __dict__ and __class__ to
        # match that of the dataset.

        args, kwargs = self.__args, self.__kwargs
        name, reader_cls = self.__name, self.__reader_cls

        self.__dict__ = corpus.__dict__
        self.__class__ = corpus.__class__

        # _unload support: assign __dict__ and __class__ back, then do GC.
        # after reassigning __dict__ there shouldn't be any references to
        # dataset data so the memory should be deallocated after gc.collect()
        def _unload(self):
            lazy_reader = LazyCorpusLoader(name, reader_cls, *args, **kwargs)
            self.__dict__ = lazy_reader.__dict__
            self.__class__ = lazy_reader.__class__
            gc.collect()

        self._unload = _make_bound_method(_unload, self)

    def __getattr__(self, attr):


        self.__load()
        # This looks circular, but its not, since __load() changes our
        # __class__ to something new:
        return getattr(self, attr)

    def __repr__(self):
        return '<%s in %r (not loaded yet)>' % (
            self.__reader_cls.__name__,
            '.../data/' + self.__name,
        )

    def _unload(self):
        # If an exception occures during dataset loading then
        # '_unload' method may be unattached, so __getattr__ can be called;
        # we shouldn't trigger dataset loading again in this case.
        pass




def _make_bound_method(func, self):
    """
    Magic for creating bound methods (used for _unload).
    """

    class Foo(object):
        def meth(self):
            pass

    f = Foo()
    bound_method = type(f.meth)

    try:
        return bound_method(func, self, self.__class__)
    except TypeError:  # python3
        return bound_method(func, self)