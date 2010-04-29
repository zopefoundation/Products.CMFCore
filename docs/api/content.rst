Content API Reference
=====================


.. _core_content:

Core Content
------------

This interface defines the contract for any content object within the CMF.

.. autointerface::  Products.CMFCore.interfaces.IDynamicType
   :members:


.. _searchable_content:

Searchable Content
------------------

These interfaces define the contract for content objects which can be
searched using the :ref:`catalog_tool`.

.. autointerface::  Products.CMFCore.interfaces.IContentish
   :members:

.. autointerface::  Products.CMFCore.interfaces.ICatalogAware
   :members:


.. _dublin_core_metadata:

Dublin Core Metadata
--------------------

These interfaces define the contracts for content objects which provide
standard Dublin Core metadata.  See also :ref:`metadata_tool`.

.. autointerface::  Products.CMFCore.interfaces.IMinimalDublinCore
   :members:

.. autointerface::  Products.CMFCore.interfaces.IDublinCore
   :members:

.. autointerface::  Products.CMFCore.interfaces.ICatalogableDublinCore
   :members:

.. autointerface::  Products.CMFCore.interfaces.IMutableMinimalDublinCore
   :members:

.. autointerface::  Products.CMFCore.interfaces.IMutableDublinCore
   :members:


.. _discussable_content:

Discussable Content
-------------------

These interfaces define the contracts / framework for content object whose
discussion can be managed by the :ref:`discussion_tool`.

.. autointerface::  Products.CMFCore.interfaces.IDiscussionResponse
   :members:

.. autointerface::  Products.CMFCore.interfaces.IOldstyleDiscussable
   :members:

.. autointerface::  Products.CMFCore.interfaces.IDiscussable
   :members:


.. _content_workflow:

Content Workflow
----------------

This interface defines the contract for content objects which can participate
in the workflow framework provided by the :ref:`workflow_tool`.

.. autointerface::  Products.CMFCore.interfaces.IWorkflowAware
   :members:


.. _content_containers:

Content Containers
-------------------

This interface defines the contract for content objects which can contain
other content as "normal" sub-items.

.. autointerface::  Products.CMFCore.interfaces.IFolderish
   :members:


Opaque Items
------------

These interfaces define the framework for content objects which can contain
other content as "opaque" sub-items.

.. autointerface::  Products.CMFCore.interfaces.ICallableOpaqueItem
   :members:

.. autointerface::  Products.CMFCore.interfaces.ICallableOpaqueItemEvents
   :members:

.. autointerface::  Products.CMFCore.interfaces.IOpaqueItemManager
   :members:


.. _content_syndication:

Content Syndication
-------------------

This interface defines the contract for content objects which can participate
in the syndication framework provided by the :ref:`syndication_tool`.

.. autointerface::  Products.CMFCore.interfaces.ISyndicatable
   :members:
