# -*- coding: utf-8 -*-

from .metadata import guess_value, Parameter
from .dataset import CompositeDataset
from .arraydataset import ArrayDataset, Column
from .tabledataset import TableDataset
from .serializable import Serializable

import itertools
from collections import OrderedDict, UserDict
import datetime
import array

import logging
# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


def check_input(arg, serializable=True):
    """ Raise exception if needed when arg is not simple type or Serializable.
    """
    cls = arg.__class__
    nm = cls.__name__
    if issubclass(cls, (int, float, str, bool, bytes, complex,
                        list, dict, array.array, UserDict,
                        datetime.datetime, type(None))):
        return arg

    if serializable:
        if issubclass(cls, tuple) or not issubclass(cls, Serializable):
            raise TypeError(
                'History parameter "%s" not found to be serializable by `json.dump()` or a subclass of `Serializable`.' % nm)
    return arg


class History(TableDataset):
    """ Public interface to the history dataset. Contains the
    main methods for retrieving a script and copying the history.
    """

    def __init__(self, **kwds):
        """

        Implemented as a `TableDataset`. Argument and context information
        are stored as metadata key-variable pairs in the metadata.
        Input data are in the table where name is the column name and
        references in the first cell of columns.

        mh: The copy constructor is better not be implemented. Use copy()
        instead. Remember: not only copies the datasets,
        but also changes the history ID in the metadata and
        relevant table entries to indicate that this a new
        independent product of which the history may change.

        Parameters
        ----------

        Returns
        -------

        """
        super(History, self).__init__(**kwds)
        self['name'] = Column([], '')
        self['reference'] = Column([], '')
        self.description = 'Named positional and keyword arguments, relevant context, and input data to the pipeline or task that generated this product.'
        self.builtin_keys = list(self._meta.keys())

    def accept(self, visitor):
        """ Hook for adding functionality to meta data object
        through visitor pattern.

        Parameters
        ----------

        Returns
        -------

        """
        visitor.visit(self)

    def getScript(self):
        """ Creates a script from the history.

        Parameters
        ----------

        Returns
        -------

        """

        return self._meta['command_line'].value()

    def getTaskHistory(self, format='graph', node=None, use_name=True, verbose=False):
        """ Returns a human readable formatted history tree.

        Parameters
        ----------
        format : str
            Output format: `graph' (default) for `networkx.DiGraph`; 'ascii" for dump; 'png', 'svg', 'jpg' for graphic formats.
        node : str
            A name that uniquely identifies the parent product.

        Returns
        -------
        `networkx.DiGraph`:
            A graph of input data names and references.
        """
        from ..pal.urn import is_urn
        from ..pal.productref import ProductRef
        import networkx
        if node is None:
            node = 'root'
        new_g = networkx.DiGraph()
        h = None
        dt = self._data
        if verbose:
            print('History graph for %s has %d inputs: %s.' %
                  (node, len(dt['name']), str(list(dt['name']))))
        # __import__('pdb').set_trace()

        for name, ref in zip(dt['name'], dt['reference']):
            # pydot wants no unquoted :
            refq = f'"{ref}"'
            if use_name:
                ref_node = (name, {'product_reference': refq})
            else:
                ref_node = (refq, {'product_name': name})
            if verbose:
                print(f"Node {ref_node}")
            new_g.add_nodes_from([ref_node])
            new_g.add_edge(name if use_name else refq, node)
            if is_urn(ref):
                inp = ProductRef(ref).getProduct()
                if verbose:
                    print(f'Load product {inp.description}:{id(inp)}.')
                # get a graph with a node named with ref
                h = inp.history.getTaskHistory(
                    node=name if use_name else refq,
                    use_name=use_name, verbose=verbose)
                # Merge
                new_g = networkx.compose(new_g, h)
                if verbose:
                    print(
                        f'Returning history graph {h.adj} for {node}==>{new_g.adj}')
        if format == 'graph':
            return new_g
        if format == 'ascii':
            try:
                import pydot
            except ImportError:
                pass
            else:
                return networkx.drawing.nx_pydot.to_pydot(new_g).to_string()
            return str(new_g.succ)
        if format == 'aaasvg':
            pass
        if format in ('svg', 'png', 'jpg'):
            try:
                import pydot
            except ImportError:
                pass
            else:
                im = networkx.drawing.nx_pydot.to_pydot(
                    new_g).create(format=format)
                return im
            return newg_g

    def graph(self, format='png', **kwds):
        """ calling getTaskHistory with simplified parameters format, default to png."""

        return self.getTaskHistory(format=format, **kwds)

    def add_input(self, args=None, info=None, refs=None, **kwds):
        """Add an entry to History records.

        A general product history is made of a series of records, each added by a
        processing step, usually called a pipeline. The record can be
        added by this method to this `History` object..

        Parameters
        ----------
        args : dict
            A mapping of  argument names and their
            values. Can be `vars(ArgParse())`. Values must be serializablee.
        info : dict
            keywords and values in string.
        refs : dict
            A mapping of name and reference string pairs. The Reference string is the URN, file name, OSS address, URL, or other kind of pointer. The name is for human to identify the data, the reference for recursive retrieving inputs to the data.
        **kwds : dict
            appended to `info` by default.
        Returns
        -------
            result

        """
        if args or info or kwds:
            for name, var in itertools.chain(args.items(), info.items(), kwds.items()):
                cvar = check_input(var)
                # append the parameter name and value
                self._meta[name] = Parameter(value=cvar)

        if not refs:
            refs = {}
        for name, ref in refs.items():
            # append the name and input data reference
            if name in self.builtin_keys:
                name = name + '___'
            self._data['name']._data.append(name)
            self._data['reference']._data.append(ref)
            self._data['name'].updateShape()
            self._data['reference'].updateShape()
            self.updateShape()

    def get_args_info(self):
        """Get arguments and context information as a dictionary.

        Returns
        -------
        dict

        """

        return dict((n[:-3] if n.endswith('___') else n, v.value) for n, v in self._meta._data.items() if n not in self.builtin_keys)

    def xx__getstate__(self):
        """ Can be encoded with serializableEncoder

        Parameters
        ----------

        Returns
        -------

        """
        return OrderedDict(
            _ATTR_meta=self._meta,
            **self.data)
