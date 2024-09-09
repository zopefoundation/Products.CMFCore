Products.CMFCore Changelog
==========================

3.6 (unreleased)
----------------

- Drop support for Python 3.7.
- Fix reindexObjectSecurity to avoid a full reindex of affected objects


3.5 (2024-03-23)
----------------

- Use the new ``resources`` keyword of ``registerClass`` if available.
  This avoids a deprecation warning for using a non callable constructor in Zope higher than 5.9.
  (`#1202 <https://github.com/zopefoundation/Zope/issues/1202>`_)


3.4 (2024-04-12)
----------------

- Add i18n translation support.
  (`#135 <https://github.com/zopefoundation/Products.CMFCore/issues/135>`_)


3.3 (2024-01-23)
----------------

- Add support for Python 3.12.

- ZMI: added limit of folderish objects for customizing and
  handling SVG files as FSImage showing a preview.
  (`#130 <https://github.com/zopefoundation/Products.CMFCore/pull/130>`_)


3.2 (2023-07-03)
----------------

- Improve handling of PortalFolder filter input.


3.1 (2023-06-01)
----------------

- Provide a way to not publish items that are acquired.


3.0 (2023-04-25)
----------------

- SkinsTool: fix Find form with Zope ZMI
  (`#127 <https://github.com/zopefoundation/Products.CMFCore/pull/127>`_).

- Drop support for Python 2.7, 3.5, 3.6.

- Drop support for ``Zope 4.x``.

- Make tests compatible with ``Zope >= 5.7.1``.


2.7.0 (2022-12-16)
------------------

- Fix insidious buildout configuration bug for tests against Zope 4.

- Add support for Python 3.11.


2.6.0 (2022-07-13)
------------------

- Fix cookie test failure
  (`#120 <https://github.com/zopefoundation/Products.CMFCore/pull/120>`_).

- Add support for Python 3.10.


2.5.4 (2021-07-29)
------------------

- Fix code and tests when running on ``Products.GenericSetup >= 2.1.2``, thus
  requiring at least that version.


2.5.3 (2021-06-30)
------------------

- Do not break at startup when ``subscribers.zcml`` is included but no
  ``portal_catalog`` object is in the database, e. g. when starting for the
  first time.
  (`#115 <https://github.com/zopefoundation/Products.CMFCore/pull/115>`_)


2.5.2 (2021-06-24)
------------------

- Avoid DeprecationWarning for changed import location for ``rfc1123_date``

- Fix several DeprecationWarnings during unit tests
  (`#112 <https://github.com/zopefoundation/Products.CMFCore/issues/112>`_)

- Set Cache-Control header in '304 Not Modified' response case as well.
  (`#111 <https://github.com/zopefoundation/Products.CMFCore/issues/111>`_)


2.5.1 (2021-03-12)
------------------

- Make sure ``getSkinNameFromRequest`` only returns sane values
  (`#109 <https://github.com/zopefoundation/Products.CMFCore/issues/109>`_)

- Fix Python 3 incompatibility in ``CookieCrumbler.credentialsChanged``


2.5.0 (2021-02-09)
------------------

- Update configuration for version 5 of ``isort``.

- Fix deprecation warnings occurring on Zope 5.

- Added support for Python 3.9.


2.4.8 (2020-07-03)
------------------

- Fix an issue with the indexing queue where an UNINDEX followed by REINDEX was
  wrongly optimized to UNINDEX instead of REINDEX.
  (`#96 <https://github.com/zopefoundation/Products.CMFCore/pull/96>`_)


2.4.7 (2020-06-24)
------------------

- Change the default value of uid to None on CMFCatalogAware's reindexObject method (`#87 <https://github.com/zopefoundation/Products.CMFCore/issues/87>`_)


2.4.6 (2020-04-14)
------------------

- Redid most filesystem content type ZMI Customize views.


2.4.5 (2020-03-27)
------------------

- Fix tests to be able to run on Zope 4.3.

- Fix not declared dependency on ``Products.DCWorkflow`` in `subscribers.zcml`.


2.4.4 (2020-01-29)
------------------

- Remove Zope Help System fossils so this products is compatible with Zope 5


2.4.3 (2020-01-10)
------------------

- Fix encoding detection for XML files.
  (`#85 <https://github.com/zopefoundation/Products.CMFCore/issues/85>`_)


2.4.2 (2019-11-28)
------------------

- Resolve ``docutils`` dependency conflict with ``Zope``.
  (`#83 <https://github.com/zopefoundation/Products.CMFCore/issues/83>`_)


2.4.1 (2019-11-27)
------------------

- Make sure ``FSFile.__str__`` returns correct native strings under Python 3.
  (`#76 <https://github.com/zopefoundation/Products.CMFCore/issues/76>`_)

- Add a ``__bytes__`` method to ``FSFile``.

- Add more files types to the FSFile registrations.


2.4.0 (2019-05-10)
------------------

- Set default encoding values on FSDTMLMethods.


2.4.0b8 (2019-04-30)
--------------------

- Fix up all ZMI forms to work better with the Zope 4 ZMI.
  (`#73 <https://github.com/zopefoundation/Products.CMFCore/issues/73>`_)

- Ensure Content Type Registries don't use a ZMI add dialog in the Zope 4 ZMI.
  (`#72 <https://github.com/zopefoundation/Products.CMFCore/issues/72>`_)


2.4.0b7 (2019-04-08)
--------------------

- Expose the Cookie Crumbler title property.
  (`#70 <https://github.com/zopefoundation/Products.CMFCore/issues/70>`_)

- Clean up test and linting configurations.

- Add ``project_urls`` with relevant links in ``setup.py``.

- Specify supported Python versions using ``python_requires`` in setup.py.

- Added support for Python 3.8.

- Deprecated unused method ``PortalCatalogProcessor.get_dispatcher``.
  (`#57 <https://github.com/zopefoundation/Products.CMFCore/issues/57>`_)

- Backport plone/collective.indexing#16 to use the catalog queue
  also when reindexing the object security.
  (`#58 <https://github.com/zopefoundation/Products.CMFCore/issues/58>`_)

- Code cleanup: avoid to call the ``keys`` method on dictionary
  when not needed.
  [ale-rt]


2.4.0b6 (2018-12-14)
--------------------

- Change `im_self` to `__self__` for Python 3 compatibility.
  (`#54 <https://github.com/zopefoundation/Products.CMFCore/pull/54>`_)
  [ale-rt, vangheem]

- Remove support for testing using ``'python setup.py test``.
  (`#51 <https://github.com/zopefoundation/Products.CMFCore/issues/51>`_)

- Add more ZMI icons for the Zope 4 ZMI.
  (`#47 <https://github.com/zopefoundation/Products.CMFCore/issues/47>`_)

- Prevent warnings on Zope start about permissions for not existing methods.
  This requires `Zope >= 4.0b8`.
  (`#53 <https://github.com/zopefoundation/Products.CMFCore/pull/53>`_)

- Fix deprecation warnings occurring during test runs.

- Update tests to `Products.GenericSetup >= 2.0b5`.


2.4.0b5 (2018-11-07)
--------------------

- Fix ``notifyModified`` called on a wrong object.
  [mamico]

- Add support for Python 3.7.

- Add support for `Zope >= 4.0b6`, thus requiring at least this version.


2.4.0b4 (2018-05-17)
--------------------

- Add support for Python 3.5 and 3.6.
  [ale-rt]

- `sortKey` for a DataManager must be text to be sortable.
  [pbauer]


2.4.0b3 (2018-03-16)
--------------------

- Remove dependency on ``five.globalrequest``, its functionality
  is provided by ``zope.globalrequest``.

- Do not autogenerate `string:${portal_url}/`, when no input for
  `content_icon` was provided.
  [pgrunewald]

- Avoid writing MemberData to the member data tool until
  properties are actually set.
  [davisagli]

- Python 2 / 3 compatible imports.
  [rudaporto]

- Update Products.MailHost dependency to 4.0
  [dataflake]

- Add icons for Bootstrap ZMI.
  [icemac, dwt]


2.4.0b2 (2017-05-05)
--------------------

- Factored support for FSZSQL methods out into a setup extra.
  If you need support for Filesystem ZSQL methods, install the
  egg specifying the ``zsql`` extra.
  [dataflake]

- Use ``zope.interface.implementer`` decorator instead of
  ``zope.interface.implements``
  [dataflake]

- Use security declaration decorator notation where possible.
  [dataflake]

- Improve the new indexing object wrapping for unindexing by using a
  module-level wrapper class based on zope.proxy instead of a class
  at method level.
  Some discussion available at GitHub PR #15.
  [dataflake]

- Queue and process indexing operations (index, reindex, unindex) at
  transaction boundaries. This allows to reduce redundant operations
  and thus improving performance.
  Operations are processed just at transaction boundaries or whenever
  a catalog search is performed.
  Part of PLIP 1343: https://github.com/plone/Products.CMFPlone/issues/1343
  [gforcada]

- Provide a ``CATALOG_OPTIMIZATION_DISABLED`` environment variable to
  disable any catalog optimization. This is mostly meant to be used so that
  tests which may need some adaptation do not break after updating to
  this version. Set it to ``true``, i.e.
  ``export CATALOG_OPTIMIZATION_DISABLED=true`` before running tests.
  Part of PLIP 1343: https://github.com/plone/Products.CMFPlone/issues/1343
  [gforcada]


2.4.0b1 (2017-05-04)
--------------------

- Target use with Zope 4:  no longer support 2.13.x.

- Make sure RegistrationTool.addMember is not published
  [vangheem]

- Don't fail on catalog inconsistency when doing `reindexObjectSecurity`
  [tomgross]

2.3.0 (2015-02-20)
------------------

- Fall back to DAV aware marshaller when importing or exporting folderish
  content, so types now retain their metadata when being round-tripped.
  [MatthewWilkes]

- IndexableObjectWrapper: Made sure portal_type doesn't return None.
  Products.ZCatalog 3 indexes can no longer handle None values.

- interfaces: Fixed dotted names by setting __module__ explicitly.

- Skinnable: The skins tool is now looked up as utility.
  'getSkinsFolderName' is no longer supported, that method was removed.

- permissions: Fixed some issues in permissions.zcml.

- support unset portal_skins request variables in HTTP headers
  (see https://dev.plone.org/ticket/10071) [fRiSi]

2.3.0-beta2 (2012-03-31)
------------------------

- added fixes for migrating CMF 2.2 sites.


2.3.0-beta (2012-03-21)
------------------------

- DynamicType: Modified 'icon' method.
  The specified icon might be registered for a ZTK layer that is not available
  in the ZMI. If the icon can't be found, an empty string is returned.

- exportimport.tests.test_mailhost:  Accomodate 'smtp_queue' and
  'smtp_queue_directory' exports (newly added in GenericSetup).

- tools: Converted all tools into local utilities.
  The registration is not done here, see CMFDefault_ as an example of a
  registration via GenericSetup.

- MemberDataTool: Changed property modes to 'w' and added 'fullname' property.

- setup handlers: Improved content type registry handler.
  The 'insert-before' and 'insert-after' directives are now supported.

- Optimize `SkinnableObjectManager.__getattr__` to short circuit view (`@`) and
  traverser (`+`) lookup in addition to `_` and `aq_`.

- Avoid a shallow dependency on `Products.ZReST`.

- Fixed types tool test to only test creation for type infos.

- utils: Fixed '_OldCacheHeaders' and '_FSCacheHeaders' methods.
  DateTimeErrors caused by invalid HTTP headers were not caught.

- setup handlers: Added export/import support for member data tool settings.

- MemberDataTool: Fixed tool initialization.
  The default boolean and date property values were not set correctly.

- MemberDataTool: Modified 'setProperties' method.
  It now can be used by user managers as well.

- MembershipTool: Added 'isMemberAccessAllowed' method.
  If you don't have the 'Manage users' permission for the membership tool, you
  shouldn't have write access to other members.

- MemberDataTool: Removed obsolete MemberData factory lookup.
  This feature was added in CMF 2.2, but now the MemberAdapter should be
  overridden instead.

- MemberDataTool: Split up MemberData class.
  The old MemberData API is now provided by the new MemberAdapter. The
  persistent MemberData objects are just used for storing member data.

- interfaces: Added 'IMember' interface.

- permissions: Marked 'setDefaultRoles' as deprecated.

- DirectoryView: Added 'bobobase_modification_time' method to FSObject.
  The "Contents" tab in the ZMI now shows useful 'Last Modified' values.

- DirectoryView: Changed debug mode behavior.
  No additional subdirs are registered in debug mode. If you add new subdirs,
  you have to restart your instance.
  (https://bugs.launchpad.net/zope-cmf/+bug/271027)

- DirectoryView: Improved debug mode speed on NTFS partitions.
  The much faster non-Windows implementation is now used on Windows as well if
  non-FAT32 time stamps are detected. In rare cases that heuristic approach
  might fail to detected NTFS partitions.

- DirectoryView: Modernized debug mode lookup.
  Now getConfiguration().debug_mode is used instead of Globals.DevelopmentMode.

- Fix content exportimport when Title or Description are unicode (merge from
  2.2 branch).

- tests base: Tightened security for anonymous test user.

- Load permissions.zcml from Products.Five in the test to fix tests
  with Zope 2.12.

- notifyWorkflowCreated only to IWorkflowAware, possibly following adaption on
  IObjectAddedEvent.

- Adapterize workflow storage lookups.

- utils: Added FakeExecutableObject.
  It can be used to set proxy roles in trusted code.

- tests base: Removed obsolete test utils.

- testing: Removed broken run function.
  Unit test modules are no longer directly executable.

- CookieCrumbler: Removed redirect support.
  The Unauthorized handling and redirects are now part of CMFDefault.

- Added a permissions.zcml file defining our own permissions. This was
  formerly done in Zope 2's Products.Five.

- Removed zope.app.testing dependency.

- Import BeforeTraverseEvent from new location if available.

- Skinnable and MembershipTool: Removed support for missing REQUEST argument.
  'changeSkin', 'setupCurrentSkin' and 'credentialsChanged' will no longer
  try to acquire the request if it is not passed in explicitly.

- Tools and PortalFolder: Removed support for deprecated marker attributes.
  '_isDirectoryView', '_isPortalRoot', '_isTypeInformation' and '_isAWorkflow'
  are no longer supported.

- utils: Removed deprecated functions.
  'getToolByInterfaceName', 'initializeBasesPhase1', 'initializeBasesPhase2',
  'expandpath' and 'minimalpath' are no longer available.

- DirectoryView: Removed support for deprecated old API.

- Require at least Zope 2.13.12.

.. _CMFDefault : https://github.com/zopefoundation/Products.CMFDefault/blob/master/Products/CMFDefault/profiles/default/componentregistry.xml

2.2.5 (2011-11-01)
------------------

- Added two missing explicit InitializeClass calls.


2.2.4 (2011-04-02)
------------------

- Fix content exportimport when Title or Description are unicode.


2.2.3 (2010-10-31)
------------------

- Make the error raised when trying to rename an instance of ImmutableId
  indicate the id of the object.

- DateTime 2.12.5 does away with a special case representing
  DateTime values for midnight (00:00:00) without their time and
  time zone values. So DateTimes formerly rendered as
  ``2010/01/01`` in the UTC timezone now render as
  ``2010/01/01 00:00:00 UTC``. Several unit tests that relied on
  the old-style representation had to be fixed.

- Get most tests working under Zope 2.13.0a2.

- Added dependency on the new ``Products.ZSQLMethods`` distribution and updated
  Zope2 requirement accordingly.


2.2.2 (2010-07-04)
------------------

- Backport test setup fixes for Zope 2.13 compatibility.

- Use the standard libraries doctest module.

- Updated setDefaultRoles to use the addPermission API if available.

- Updated test to work with zope.contenttype >= 3.4.3.


2.2.1 (2010-04-07)
------------------

- Actions and TypeInformation: Clear the compiled NNN_expr_object
  property when the NNN_expr property is cleared.

- Actions: Return None if 'link_target' is an empty string.
  This helps to avoid invalid empty 'target' attributes in HTML output.


2.2.0 (2010-01-04)
------------------

- Changed GenericSetup import handlers to fail silently if they
  are called in a context that does not contain the items they
  import.


2.2.0-beta (2009-12-06)
-----------------------

- TypesTool: Made it an ordered container.
  This allows to control the order of the add actions.

- TypeInformation: Removed redundant 'content_icon' property.
  For backwards compatibility old settings containing 'content_icon' instead
  of 'icon_expr' are converted on import. CMFDefault provides the necessary
  upgrade steps for migrating existing sites.

- DynamicType: Added 'getIconURL' method.
  This replaces the now deprecated 'getIcon' method.

- TypeInformation: Added 'getIconExprObject' method.
  This replaces the now deprecated 'getIcon' method.


2.2.0-alpha (2009-11-13)
------------------------

- Got rid of redundant icon related type info properties.
  (https://bugs.launchpad.net/zope-cmf/+bug/397795)

- PortalFolder: Ensure that pasting an object into a folder takes
  workflow instance creation conditions into account.
  (https://bugs.launchpad.net/zope-cmf/+bug/308947)

- Made calls to reindexObjectSecurity in the membership tool conditional
  after the CMFCatalogAware refactoring.

- PortalFolder: Removed unused ICatalogAware and IWorkflowAware methods.

- CMFCatalogAware: Split up CMFCatalogAware mixin.
  CatalogAware, WorkflowAware and OpaqueItemManager are now separate mixins.

- Changed testing.py to directly load zope.traversing's ZCML instead of going
  via the Five traversing.zcml BBB shim.

- moved the Zope dependency to version 2.12.0b3dev

- PortalFolder: Modified allowedContentTypes method to check
  isConstructionAllowed only for allowed types, not for all content types.

- Fixed typo in the acquisition wrapping of the found utility in
  getToolByName.

- Actions: Add a link_target attribute to store a value for the
  final rendered link tag's "target" attribute
  (https://bugs.launchpad.net/zope-cmf/+bug/376951)

- MemberData tool: Make it easier to override the default
  MemberData implementation by trying to look up a named
  factory utility named "MemberData" before falling back on the
  default MemberData class.
  (https://bugs.launchpad.net/zope-cmf/+bug/377208)

- FSPageTemplate: Change the charset/encoding detection to consider
  charset specifications in the content type, and replace the
  hardcoded Latin-15 fallback with the mechanism used by the
  Products.PageTemplate code, which can be influenced by setting
  the environment variable "ZPT_PREFERRED_ENCODING"
  (https://bugs.launchpad.net/zope-cmf/+bug/322263)

- Expose the ZMI manage view of the "_components" object manager as
  a new "Components Folder" tab in the ZMI.

- ActionsTool: The "Action Providers" tab in the ZMI did not render
  actions from the WorkflowTool correctly since those are not
  'new-style' actions.
  (https://bugs.launchpad.net/zope-cmf/+bug/322300)

- FSPageTemplate: Prevent reading the underlying file without doing
  anything with the data in some cases.

- FSObject: Ensure that ZCache invalidations only happens if the
  filesystem modification time differs from the internally stored
  previous modification time.
  (https://bugs.launchpad.net/zope-cmf/+bug/325246)

- TypeInformation: DCWorkflow instances define a method and a guard
  for vetoing object creation, but it was never used. Now
  TypeInformation objects will consult these guard conditions during
  object creation.
  (https://bugs.launchpad.net/zope-cmf/+bug/308947)

- PortalCatalog: Changed to use a multi-adaptor to allow a pluggable
  IndexableObjectWrapper class.  Objects that implement IIndexableObject
  are not wrapped.  The change will assist in integrating with
  other indexing strategies from third-party packages.

- Events: Changed 'handleContentishEvent' behavior for IObjectCopiedEvent.
  'WorkflowTool.notifyCreated' no longer resets the workflow state, so the
  the event subscriber clears the workflow history instead.

- WorkflowTool: 'notifyCreated' no longer overrides assigned workflow states.

- No longer catch a `NotImplemented` string exception in the MembershipTool
  in deleteMembers.

- Cleaned up / normalized imports:

  o Don't import from Globals;  instead, use real locations.

  o Make other imports use the actual source module, rather than an
    intermediate (e.g., prefer importing 'ClassSecurityInfo' from
    'AccessControl.SecurityInfo' rather than from 'AccessControl').

  o Avoid relative imports, which will break in later versions of Python.

- Added `icon_expr` as a new property to type information. This allows you
  to specify the `content_icon` as an expression and store it. This avoids
  creating the expression on the fly at rendering time.

- Removed superGetAttr fallback from SkinnableObjectManager. None of its base
  classes have a `__getattr__` method anymore.

- PortalObject: Removed backwards compatibility code in getSiteManager.
  Please use CMFDefault's upgrade steps for upgrading old CMF sites.

- Fixed compatibility with non-string exceptions on Zope trunk.

- Added remove support to GenericSetup types tool exportimport handler.

- FiveActionsTool: Removed the tool and all functionality for bridging
  between Zope 3-style menu items and CMF actions. The CMF has been going
  a different route for a long time and the code is unused and
  unmaintained.

- Actions: Added deprecation warnings to the ZMI actions tab and
  most listActions methods where old-style actions are found
  asking developers to move to new-style actions instead. These
  warnings allow us to remove old-style actions code by version 2.4.

- Discussion tool: Removed the listActions method that would return
  a hardcoded Reply action. This action has been handled by the
  Actions tool itself for a while now, and the Discussions tool was
  not set as an action provider anymore.

- actions tool export/import: The actions tool export/import mechanism
  is no longer attempting to handle actions stored on tools other than
  itself. Other tools are themselves responsible for their actions.
  The importer has been fixed to add all action providers to the actions
  tool, not just a select list of providers we know about.
  (https://bugs.launchpad.net/zope-cmf/+bug/177675)

- tool interfaces: Replace non-existing IMember interface with the
  correct IMemberData.

- CatalogTool: If proxy roles are set on a script that uses the catalog
  and those proxy roles have been unset using the ZMI, which results
  in an empty tuple as proxy roles, then the catalog would not correctly
  determine what the current user is allowed to see.
  (https://bugs.launchpad.net/zope-cmf/+bug/161729)

- Properties export/import: Get the string encoding for property
  imports from the import context and fall back to UTF-8, which
  mirrors the behavior for exports. This fixes property export/import
  round tripping.
  (https://bugs.launchpad.net/zope-cmf/+bug/248853)

- traversal: Added ++add++ namespace for add views.

- Skinstool import: Fix imports that manipulate existing skins.
  (https://bugs.launchpad.net/zope-cmf/+bug/161732)

- ActionInformation: extend the ActionInformation and ActionInfo classes
  to support a icon URL just like the newer Action class already does

- WorkflowTool: Passing the "magic" chain name "(Default)" to the
  setChainForPortalTypes method did not set the chain to the default
  chain value as expected.
  (https://bugs.launchpad.net/zope-cmf/+bug/161702)

- ZMI: Prevent users from creating content through the ZMI by hiding the
  entry for "CMFCore Content".

- utils: Add a new optional argument to ContentInit that allows hiding
  a content item's ZMI add list entry. The default is to leave the item
  visible, which reflects the previous behavior.

- FSMetadata: Remove handling of .security and .properties metadata
  files which was supposed to have been removed in CMF 2.0 already.

- SkinsTool: Added the ability to do a diff comparison between items
  found using the portal_skins "Find" ZMI tab.
  (https://bugs.launchpad.net/zope-cmf/+bug/238489)

- TypeInformation and TypesTool: Added support for add view actions.
  Type infos now have a new 'add_view_expr' property and implement IAction.
  'listActions' of the types tool includes type infos as 'add' actions.

- interfaces: Fixed some docstrings.
  There is no IActionInformation. ActionInformation is an old action class
  that implements IAction, non-persistent IActionInfo objects adapt action
  objects to a given context.

- FSSTXMethod: Fixed Zope 2.12 compatibility.
  zope.structuredtext is now used instead of StructuredText.

- removed the five.localsitemanager svn:external and its import hack
  in favor of stating the dependency for separate installation in
  DEPENDENCIES.txt and automatic installation in setup.py.

- TypesTool: Refactored content creation.
  Moved addCreator call to IObjectCreatedEvent handler and moved
  notifyWorkflowCreated and indexObject calls to IObjectAddedEvent handler.
  Please make sure all oldstyle content factory methods use _setObject with
  suppress_events=True. CMF factory methods don't finish object creation,
  so they should not send the IObjectAddedEvent.

- interfaces: Added new interfaces for CMFCatalogAware methods.
  In the long run ICatalogAware, IWorkflowAware and IOpaqueItemManager will
  become deprecated. Don't expect that CMF content always implements them.

- setup handlers: All import and export steps are now registered globally.

- MembershipTool: Removed ancient LoginManager compatibility code and
  deprecated the no longer needed __getPUS method.

- interfaces: Removed deprecated oldstyle interfaces.


2.1.2 (2008-09-13)
------------------

- fiveactionstool: fix typo in a method name that isn't even used in the CMF
  or Plone.
  (https://bugs.launchpad.net/zope-cmf/+bug/257259)

2.1.2-beta (2008-08-26)
-----------------------

- completed devolution from monolithic CMF package into its component
  products that are distributed as eggs from PyPI.


2.1.1 (2008-01-06)
------------------

- exportimport.content: Add simple guard against import failures when
  the ".objects" file contains empty lines.
  (https://bugs.launchpad.net/zope-cmf/+bug/176328)


2.1.1-beta (2007-12-29)
-----------------------

- Testing: Derive test layers from ZopeLite layer if available.

- Updated to the 0.3 release of five.localsitemanager.

- Events: Fixed some handleContentishEvent issues.
  Moved _clearLocalRolesAfterClone code to separate handler that is
  triggered before indexing and also for folders. Made sure notifyModified
  is not called if objects are just moved.

- PortalObject: Added setSite to getSiteManager for old instances. This
  fixes migrations from Plone 2.1 to 3.0.

- FSImage: Supply class-level defaults for 'alt', 'height', and 'width',
  to avoid acquiring objects with the same names.
  (http://www.zope.org/Collectors/CMF/507)

- Testing: Derive test layers from ZopeLite layer if available.

- PortalObject: Fixed a bug in the site manager creation code, which would
  assign the __parent__ pointer to the Aq-wrapper and not the actual
  object.


2.1.0 (2007-08-08)
------------------

- Fixed all componentregistry.xml files to use plain object paths and strip
  and slashes. GenericSetup does only support registering objects which are
  in the site root.

- PortalFolder: Enabled 'Components' ZMI tab.
  This GenericSetup tab allows to inspect and edit component registrations.

- First egg release.  For changes up through this release, please see
  the overall "CMF changelog",
  http://svn.zope.org/CMF/tags/2.1.0/CHANGES.txt?rev=78713&view=markup


2.1.0-beta2 (2007-07-12)
------------------------

- moved the Zope dependency to version 2.10.4

- Remove antique usage of marker attributes in favor of interfaces,
  leaving BBB behind for places potentially affecting third-party code.
  (http://www.zope.org/Collectors/CMF/440)

- Add POST-only protections to security critical methods.
  http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2007-0240)

- exportimport.skins: Added the ability to remove whole skin selections using a
  GS profile.
  (http://www.zope.org/Collectors/CMF/479)

- UndoTool: Fixed 'listUndoableTransactionsFor'.
  The required 'object' argument is now respected. This doesn't change the
  behavior as long as 'object' is the site root object.

- TypesTool: Corrected method signature of all_meta_types to have
  an interface keyword argument, as per the underlying OFS.ObjectManager
  interface declaration.

- SkinnableObjectManager: Changed the way skins are set up.
  Acquisition wrapping no longer triggers 'setupCurrentSkin'. This is now
  done on publishing traversal after the BeforeTraverseEvent triggers
  'setSite'. This fix replaces a temporary hack introduced in 2.1.0-beta,
  making sure ISkinsTool is looked up after setting the site.

- CMFBTreeFolder: CMFBTreeFolders could not be used as the
  toplevel /Members container.
  (http://www.zope.org/Collectors/CMF/441)

- TypesTool: Pass 'object' through to TypeInformation objects'
  'listActions'.
  (http://www.zope.org/Collectors/CMF/482)

- Removed extraneous "Cache" tab from FS-based skin objects.
  (http://www.zope.org/Collectors/CMF/343)

- WorkflowTool: Using the '(Default)' keyword for a type's
  workflow chain will now reset any custom workflow chains for the type.
  (http://www.zope.org/Collectors/CMF/475)

- SkinsTool: Use the property API to get the member specific skin,
  because direct attribute access won't work with PAS based membership.
  (http://dev.plone.org/plone/ticket/5904)

- Allow customization from DirectoryViews to be redirected into
  alternate folders, and use manually-built clones.
  (http://www.zope.org/Collectors/CMF/382)


2.1.0-beta (2007-03-09)
-----------------------

- moved the Zope dependency to verson 2.10.2

- Tool lookup and registration is now done "the Zope 3 way" as utilities, see
  http://svn.zope.org/CMF/branches/2.1/docs/ToolsAreUtilities.stx?view=auto

- DirectoryView: Added 'registerDirectory' ZCML directive.
  Using the old registerDirectory method in __init__.py is now deprecated.
  See zcml.IRegisterDirectoryDirective for details.

- DirectoryView: Added support for non-product packages.
  This introduces new registry keys. Old registry keys stored in
  persistent DirectoryView objects are updated on the fly.
  (http://www.zope.org/Collectors/CMF/467)

- setup handlers: Improved properties handler.
  It now works with properties using a default_charset other than UTF-8.

- MembershipTool: Fixed inconsistent behavior where member lookup
  would take all user folders up to the Zope root into account whereas
  member area creation would not.

- MembershipTool: when using an object without a __nonzero__ but with a
  __len__ (ala CMFBTreeFolder) as a member folder, the createMemberArea
  method would believe there was no members folder if the folder was
  empty, and so would fail (change "not membersfolder" to
  "membersfolder is not None") .

- DynamicType: Fixed behaviour regarding default view.
  DynamicType was making it impossible to use a Zope3-style
  default view for CMF content types.
  (http://www.zope.org/Collectors/CMF/459)

- utils: Marked 'minimalpath' and 'expandpath' as deprecated.

- Merged patches from Martin Aspeli to enable generating events before
  and after DCWorkflow transitions, and in the 'notify' methods of the
  workflow tool (http://www.zope.org/Collectors/CMF/461).


2.1.0-alpha2 (2006-11-23)
-------------------------

- moved the Zope dependency to version 2.10.1

- Fixed test breakage induced by use of Z3 pagetemplates in Zope 2.10+.

- browser views: Added some zope.formlib based forms.

- testing: Added test layers for setting up ZCML.

- WorkflowTool: Added the IConfigurableWorkflowTool interface.
  This change includes the new 'getDefaultChain' and 'listChainOverrides'
  methods and an improved 'setChainForPortalTypes' method. The import
  handler now supports the 'remove' attribute for removing overrides.
  (http://www.zope.org/Collectors/CMF/457)

- CachingPolicyManager: Implemented the old OFS.Cache.CacheManager
  API. Now objects other than CMF content or CMF templates can have their
  caching headers set by the caching policy manager with the same
  fine-grained control.
  (http://www.zope.org/Collectors/CMF/408)

- Added CMFCore.FSRestMethod:  ReST equivalent of FSSTXMethod.

- FSSTXMethod:  Modernized, added tests, made customization
  possible (now renders via ZPT by default, using 'main_template').

- CachingPolicyManager: Prevent firing of caching policies
  for templates (DTML or ZPT) that are rendered in-line (without a
  separate request) while rendering the requested content item's view.
  (http://www.zope.org/Collectors/CMF/456)


2.1.0-alpha (2006-10-09)
------------------------

- skins: Changed encoding of translated portal_status_messages.
  Now getBrowserCharset is used to play nice with Five forms. Customized
  setRedirect and getMainGlobals scripts have to be updated.

- Profiles: All profiles are now registered by ZCML.

- ZClasses: Removed unmaintained support for ZClasses.
  Marked the 'initializeBases*' methods as deprecated.

- Content: Added IFactory utilities for all content classes.
  They are now used by default instead of the old constructor methods.

- Content: All content classes are now registered by ZCML.
  ContentInit is still used to register oldstyle constructors.

- setup handlers: Removed support for CMF 1.5 CMFSetup profiles.

- FactoryTypeInformation: Added support for Zope3 style factories.
  If the 'product' property of a type info instance is empty the 'factory'
  property is interpreted as an IFactory name.

- ActionInformation: don't use a fixed set of properties for
  ActionInformation. (http://www.zope.org/Collectors/CMF/232/)

- CatalogTool: Use current executable's proxy roles, if any,
  in place of user's roles when computing 'allowedRolesAndUsers' for
  a query. (http://www.zope.org/Collectors/CMF/380)

- FSFile: Added registration for 'txt' extension.

- CMFCatalogAware: Added 'handleObjectEvent' subscriber.
  This replaces the deprecated 'manage_afterAdd', 'manage_afterClone' and
  'manage_beforeDelete' hooks.


Earlier releases
----------------

For a complete list of changes before version 2.1.0-alpha, see the HISTORY.txt
file on the CMF-2.1 branch:
https://web.archive.org/web/20130123004606/http://svn.zope.org/CMF/branches/2.1/HISTORY.txt?view=auto
