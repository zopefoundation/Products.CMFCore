Tool API Reference
==================


.. _actions_tool:

Actions Tool
------------

These interfaces define the framework used to allow extensible menu actions
via the actions tool.

.. autointerface::  Products.CMFCore.interfaces.IActionProvider
   :members:

.. autointerface::  Products.CMFCore.interfaces.IActionCategory
   :members:

.. autointerface::  Products.CMFCore.interfaces.IAction
   :members:

.. autointerface::  Products.CMFCore.interfaces.IActionInfo
   :members:

.. autointerface::  Products.CMFCore.interfaces.IActionsTool
   :members:


.. _caching_policy_manager:

Caching Policy Manager
----------------------

These interfaces define the framework used by the cache policy manager tool
to set caching headers on content views.

.. autointerface::  Products.CMFCore.interfaces.ICachingPolicy
   :members:

.. autointerface::  Products.CMFCore.interfaces.ICachingPolicyManager
   :members:


.. _catalog_tool:

Catalog Tool
------------

These interfaces define the framework used by the catalog tool to index
and search content.  See also the interfaces for :ref:`searchable_content`.

.. autointerface::  Products.CMFCore.interfaces.IIndexableObject
   :members:

.. autointerface::  Products.CMFCore.interfaces.IIndexableObjectWrapper
   :members:

.. autointerface::  Products.CMFCore.interfaces.ICatalogTool
   :members:



.. _content_type_registry:

Content Type Registry
---------------------

These interfaces define the framework used by the content type registry tool
to determine what kind of content object to create based on a MIME type or
filename.  This lookup is done when adding new items to
:ref:`content_containers` via FTP or WebDAV.

.. autointerface::  Products.CMFCore.interfaces.IContentTypeRegistryPredicate
   :members:

.. autointerface::  Products.CMFCore.interfaces.IContentTypeRegistry
   :members:


.. _discussion_tool:

Discussion Tool
---------------

These interfaces define the framework used by the discussion tool to
determine whether discussion is allowed for particular content objects.
See also :ref:`discussable_content`.

.. autointerface::  Products.CMFCore.interfaces.IOldstyleDiscussionTool
   :members:

.. autointerface::  Products.CMFCore.interfaces.IDiscussionTool
   :members:


.. _memberdata_tool:

MemberData Tool
---------------

These interfaces define the framework used by the membedata tool for storing
and querying information about a registered member.

.. autointerface::  Products.CMFCore.interfaces.IMemberData
   :members:

.. autointerface::  Products.CMFCore.interfaces.IMemberDataTool
   :members:


.. _membership_tool:

Membership Tool
---------------

This interface defines the API provided by the membership tool for finding
site-wide information about a registered member.

.. autointerface::  Products.CMFCore.interfaces.IMembershipTool
   :members:


.. _metadata_tool:

Metadata Tool
-------------

This interface defines the API provided by the metadata tool for
managing / querying policies about content metadata.

.. autointerface::  Products.CMFCore.interfaces.IMetadataTool
   :members:


.. _properties_tool:

Properties Tool
---------------

This interface defines the API provided by the properties tool for
querying site-wide properties.

.. autointerface::  Products.CMFCore.interfaces.IPropertiesTool
   :members:


.. _registration_tool:

Registration Tool
-----------------

These interfaces define the framework used by the registration tool for
managing policies about how users join the site.

.. autointerface::  Products.CMFCore.interfaces.IRegistrationTool
   :members:


.. _skins_tool:

Skins Tool
----------

These interfaces define the framework used by the skins tool for
layering UI components to create "skins" for the site.

.. autointerface::  Products.CMFCore.interfaces.IDirectoryView
   :members:

.. autointerface::  Products.CMFCore.interfaces.ISkinsContainer
   :members:

.. autointerface::  Products.CMFCore.interfaces.ISkinsTool
   :members:


.. _syndication_tool:

Syndication Tool
----------------

These interfaces define the framework used by the syndication tool for
managing policies about syndicating content from a given folder or collection.
See also :ref:`content_syndication`.

.. autointerface::  Products.CMFCore.interfaces.ISyndicationTool
   :members:


.. _types_tool:

Types Tool
----------

These interfaces define the framework used by the skins type for defining
extensible content object types.

.. autointerface::  Products.CMFCore.interfaces.ITypeInformation
   :members:

.. autointerface::  Products.CMFCore.interfaces.ITypesTool
   :members:


.. _undo_tool:

Undo Tool
---------

This interface defines the API provided undo tool for undoing changes made
to the site.

.. autointerface::  Products.CMFCore.interfaces.IUndoTool
   :members:


.. _url_tool:

URL Tool
--------

This interfaces defines the API provided by the url tool for
generating and resolving URLs and paths relative to the site root.

.. autointerface::  Products.CMFCore.interfaces.IUndoTool
   :members:


.. _workflow_tool:

Workflow Tool
-------------

These interfaces define the framework used by the workflow type for defining
configurable workflows for content types.  See also :ref:`content_workflow`.

.. autointerface::  Products.CMFCore.interfaces.IWorkflowDefinition
   :members:

.. autointerface::  Products.CMFCore.interfaces.IWorkflowTool
   :members:

.. autointerface::  Products.CMFCore.interfaces.IConfigurableWorkflowTool
   :members:
