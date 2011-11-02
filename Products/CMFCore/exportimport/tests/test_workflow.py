##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Workflow tool xml adapter and setup handler unit tests. """

import unittest
import Testing

from OFS.Folder import Folder
from zope.interface import implements

from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from Products.CMFCore.interfaces import IConfigurableWorkflowTool
from Products.CMFCore.testing import DummyWorkflow
from Products.CMFCore.testing import ExportImportZCMLLayer

_WORKFLOWTOOL_BODY = """\
<?xml version="1.0"?>
<object name="portal_workflow" meta_type="CMF Workflow Tool">
 <property name="title"></property>
 <object name="foo_workflow" meta_type="Dummy Workflow"/>
 <bindings>
  <default>
   <bound-workflow workflow_id="foo_workflow"/>
  </default>
  <type type_id="Foo Type"/>
 </bindings>
</object>
"""

_EMPTY_TOOL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_workflow" meta_type="Dummy Workflow Tool">
 <property name="title"></property>
 <bindings>
  <default/>
 </bindings>
</object>
"""

_BINDINGS_TOOL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_workflow" meta_type="Dummy Workflow Tool">
 <bindings>
  <default>
   <bound-workflow workflow_id="non_dcworkflow_0"/>
   <bound-workflow workflow_id="non_dcworkflow_1"/>
  </default>
  <type type_id="sometype">
   <bound-workflow workflow_id="non_dcworkflow_2"/>
  </type>
  <type type_id="anothertype">
   <bound-workflow workflow_id="non_dcworkflow_3"/>
  </type>
 </bindings>
</object>
"""

_NORMAL_TOOL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_workflow" meta_type="Dummy Workflow Tool">
 <property name="title"></property>
 <object name="Non-DCWorkflow" meta_type="Dummy Workflow"/>
 <bindings>
  <default/>
 </bindings>
</object>
"""

_FRAGMENT_IMPORT = """\
<?xml version="1.0"?>
<object name="portal_workflow">
 <bindings>
  <type type_id="sometype" remove=""/>
 </bindings>
</object>
"""


class DummyWorkflowTool(Folder):

    implements(IConfigurableWorkflowTool)

    meta_type = 'Dummy Workflow Tool'

    def __init__(self, id='portal_workflow'):
        Folder.__init__(self, id)
        self._default_chain = ()
        self._chains_by_type = {}

    def getWorkflowIds(self):
        return self.objectIds()

    def getWorkflowById(self, workflow_id):
        return self._getOb(workflow_id)

    def getDefaultChain(self):
        return self._default_chain

    def setDefaultChain(self, chain):
        chain = chain.replace(',', ' ')
        self._default_chain = tuple(chain.split())

    def listChainOverrides(self):
        return sorted(self._chains_by_type.items())

    def setChainForPortalTypes(self, pt_names, chain, verify=True):
        if chain is None:
            for pt_name in pt_names:
                if pt_name in self._chains_by_type:
                    del self._chains_by_type[pt_name]
            return

        chain = chain.replace(',', ' ')
        chain = tuple(chain.split())

        for pt_name in pt_names:
            self._chains_by_type[pt_name] = chain


class WorkflowToolXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from Products.CMFCore.exportimport.workflow \
                import WorkflowToolXMLAdapter

        return WorkflowToolXMLAdapter

    def _populate(self, obj):
        obj._setObject('foo_workflow', DummyWorkflow('foo_workflow'))
        obj.setDefaultChain('foo_workflow')
        obj.setChainForPortalTypes(('Foo Type',), '', verify=False)

    def setUp(self):
        from Products.CMFCore.WorkflowTool import WorkflowTool

        self._obj = WorkflowTool()
        self._BODY = _WORKFLOWTOOL_BODY


class _WorkflowSetup(BaseRegistryTests):

    def _initSite(self):
        self.root.site = Folder(id='site')
        site = self.root.site
        self.root.site.portal_workflow = DummyWorkflowTool()
        return site


class exportWorkflowToolTests(_WorkflowSetup):

    layer = ExportImportZCMLLayer

    def test_empty(self):
        from Products.CMFCore.exportimport.workflow import exportWorkflowTool

        site = self._initSite()
        context = DummyExportContext(site)
        exportWorkflowTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'workflows.xml')
        self._compareDOM(text, _EMPTY_TOOL_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_normal(self):
        from Products.CMFCore.exportimport.workflow import exportWorkflowTool

        WF_ID_NON = 'non_dcworkflow'
        WF_TITLE_NON = 'Non-DCWorkflow'

        site = self._initSite()
        wf_tool = site.portal_workflow
        nondcworkflow = DummyWorkflow(WF_TITLE_NON)
        nondcworkflow.title = WF_TITLE_NON
        wf_tool._setObject(WF_ID_NON, nondcworkflow)

        context = DummyExportContext(site)
        exportWorkflowTool(context)

        self.assertEqual(len(context._wrote), 2)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'workflows.xml')
        self._compareDOM(text, _NORMAL_TOOL_EXPORT)
        self.assertEqual(content_type, 'text/xml')


class importWorkflowToolTests(_WorkflowSetup):

    layer = ExportImportZCMLLayer

    _BINDINGS_TOOL_EXPORT = _BINDINGS_TOOL_EXPORT
    _EMPTY_TOOL_EXPORT = _EMPTY_TOOL_EXPORT
    _FRAGMENT_IMPORT = _FRAGMENT_IMPORT

    def test_empty_default_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site = self._initSite()
        wf_tool = site.portal_workflow

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site)
        context._files['workflows.xml'] = self._EMPTY_TOOL_EXPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 0)
        self.assertEqual(len(wf_tool._default_chain), 0)
        self.assertEqual(len(wf_tool._chains_by_type), 0)

    def test_empty_explicit_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site = self._initSite()
        wf_tool = site.portal_workflow

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site, True)
        context._files['workflows.xml'] = self._EMPTY_TOOL_EXPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 0)
        self.assertEqual(len(wf_tool._default_chain), 0)
        self.assertEqual(len(wf_tool._chains_by_type), 0)

    def test_empty_skip_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site = self._initSite()
        wf_tool = site.portal_workflow

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site, False)
        context._files['typestool.xml'] = self._EMPTY_TOOL_EXPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 4)
        self.assertEqual(len(wf_tool._default_chain), 1)
        self.assertEqual(wf_tool._default_chain[0], WF_ID_NON % 1)
        self.assertEqual(len(wf_tool._chains_by_type), 1)
        self.assertEqual(wf_tool._chains_by_type['sometype'],
                         (WF_ID_NON % 2,))

    def test_bindings_skip_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site = self._initSite()
        wf_tool = site.portal_workflow

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site, False)
        context._files['workflows.xml'] = self._BINDINGS_TOOL_EXPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 4)
        self.assertEqual(len(wf_tool._default_chain), 2)
        self.assertEqual(wf_tool._default_chain[0], WF_ID_NON % 0)
        self.assertEqual(wf_tool._default_chain[1], WF_ID_NON % 1)
        self.assertEqual(len(wf_tool._chains_by_type), 2)
        self.assertEqual(wf_tool._chains_by_type['sometype'],
                         (WF_ID_NON % 2,))
        self.assertEqual(wf_tool._chains_by_type['anothertype'],
                         (WF_ID_NON % 3,))

    def test_fragment_skip_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site = self._initSite()
        wf_tool = site.portal_workflow

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site, False)
        context._files['workflows.xml'] = self._FRAGMENT_IMPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 4)
        self.assertEqual(len(wf_tool._default_chain), 1)
        self.assertEqual(wf_tool._default_chain[0], WF_ID_NON % 1)
        self.assertEqual(len(wf_tool._chains_by_type), 0)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(WorkflowToolXMLAdapterTests),
        unittest.makeSuite(exportWorkflowToolTests),
        unittest.makeSuite(importWorkflowToolTests),
        ))

if __name__ == '__main__':
    from Products.CMFCore.testing import run
    run(test_suite())
