##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for ActionProviderBase module.
"""
import warnings

from zope.component import getSiteManager
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp

#   We have to import these here to make the "ugly sharing" test case go.
from ..ActionInformation import ActionInformation
from ..ActionProviderBase import ActionProviderBase
from ..interfaces import IMembershipTool
from ..interfaces import IURLTool
from .base.dummy import DummySite
from .base.dummy import DummyTool
from .base.testcase import SecurityTest


class DummyProvider(ActionProviderBase, DummyTool):

    _actions = (ActionInformation(id='an_id',
                                  title='A Title',
                                  action='',
                                  condition='',
                                  permissions=(),
                                  category='',
                                  visible=False),)


class DummyAction:

    def __init__(self, value):
        self.value = value

    def clone(self):
        return self.__class__(self.value)

    def __eq__(self, other):
        return (
            type(self) == type(other) and
            self.__class__ == other.__class__ and
            self.value == other.value
        )


class ActionProviderBaseTests(SecurityTest):

    def setUp(self):
        SecurityTest.setUp(self)
        self.site = DummySite('site').__of__(self.app)
        sm = getSiteManager()
        sm.registerUtility(DummyTool(), IMembershipTool)
        sm.registerUtility(DummyTool().__of__(self.site), IURLTool)

    def tearDown(self):
        cleanUp()
        SecurityTest.tearDown(self)

    def _makeProvider(self, dummy=0):

        klass = dummy and DummyProvider or ActionProviderBase
        return klass()

    def test_interfaces(self):
        from ..interfaces import IActionProvider

        verifyClass(IActionProvider, ActionProviderBase)

    def test_addAction(self):
        apb = self._makeProvider()
        self.assertFalse(apb._actions)
        old_actions = apb._actions
        apb.addAction(id='foo',
                      name='foo_action',
                      action='',
                      condition='',
                      permission='',
                      category='')
        self.assertTrue(apb._actions)
        self.assertFalse(apb._actions is old_actions)

    def test_addActionBlankPermission(self):
        # make sure a blank permission gets stored as an empty tuple
        # '' and () and ('',) should mean no permission.

        apb = self._makeProvider()
        apb.addAction(id='foo',
                      name='foo_action',
                      action='',
                      condition='',
                      permission='',
                      category='',
                      )
        self.assertEqual(apb._actions[0].permissions, ())

        apb.addAction(id='foo',
                      name='foo_action',
                      action='',
                      condition='',
                      permission=('',),
                      category='',
                      )
        self.assertEqual(apb._actions[1].permissions, ())

        apb.addAction(id='foo',
                      name='foo_action',
                      action='',
                      condition='',
                      permission=(),
                      category='',
                      )
        self.assertEqual(apb._actions[2].permissions, ())

    def test_extractActionBlankPermission(self):
        # make sure a blank permission gets stored as an empty tuple
        # both () and ('',) should mean no permission.

        apb = self._makeProvider()

        index = 5
        properties = {
            'id_5': 'foo',
            'name_5': 'foo_action',
            'permission_5': (),
            }
        action = apb._extractAction(properties, index)
        self.assertEqual(action.permissions, ())

        index = 2
        properties = {
            'id_2': 'foo',
            'name_2': 'foo_action',
            'permission_2': ('',),
            }
        action = apb._extractAction(properties, index)
        self.assertEqual(action.permissions, ())

    def test_changeActions(self):
        apb = DummyTool()
        old_actions = list(apb._actions)

        keys = [('id_%d', None),
                ('name_%d', None),
                ('action_%d', ''),
                ('condition_%d', ''),
                ('permission_%d', None),
                ('category_%d', None),
                ('visible_%d', 0)]

        properties = {}
        for i in range(len(old_actions)):
            for key, value in keys:
                token = key % i
                if value is None:
                    value = token
                properties[token] = value

        apb.changeActions(properties=properties)

        marker = []
        for i in range(len(apb._actions)):

            for key, value in keys:
                attr = key[:-3]

                if value is None:
                    value = key % i

                if attr == 'name':    # WAAAA
                    attr = 'title'

                if attr == 'permission':    # WAAAA
                    attr = 'permissions'
                    value = (value,)

                attr_value = getattr(apb._actions[i], attr, marker)
                self.assertEqual(attr_value, value, '%s, %s != %s, %s'
                                 % (attr, attr_value, key, value))
        self.assertFalse(apb._actions is old_actions)

    def test_deleteActions(self):

        apb = self._makeProvider()
        apb._actions = tuple(map(DummyAction, ['0', '1', '2']))
        highander_action = apb._actions[1]  # There can be only one
        apb.deleteActions(selections=(0, 2))
        self.assertEqual(len(apb._actions), 1)
        self.assertTrue(highander_action in apb._actions)

    def test_DietersNastySharingBug(self):

        one = self._makeProvider(dummy=1)
        another = self._makeProvider(dummy=1)

        def idify(x):
            return id(x)

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            old_ids = one_ids = list(map(idify, one.listActions()))
            another_ids = list(map(idify, another.listActions()))

            self.assertEqual(one_ids, another_ids)

            one.changeActions({'id_0': 'different_id',
                               'name_0': 'A Different Title',
                               'action_0': 'arise_shine',
                               'condition_0': 'always',
                               'permissions_0': 'granted',
                               'category_0': 'quality',
                               'visible_0': 1})

            one_ids = list(map(idify, one.listActions()))
            another_ids = list(map(idify, another.listActions()))
        self.assertFalse(one_ids == another_ids)
        self.assertEqual(old_ids, another_ids)

    def test_listActionInfos(self):
        wanted = [{'id': 'an_id', 'title': 'A Title', 'description': '',
                   'url': '', 'category': 'object', 'visible': False,
                   'available': True, 'allowed': True, 'link_target': None,
                   'icon': ''}]

        apb = self.site._setObject('portal_apb', self._makeProvider(1))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            rval = apb.listActionInfos()
            self.assertEqual(rval, [])
            rval = apb.listActionInfos(check_visibility=0)
            self.assertEqual(rval, wanted)
            rval = apb.listActionInfos('foo/another_id', check_visibility=0)
            self.assertEqual(rval, [])

    def test_getActionObject(self):
        apb = self.site._setObject('portal_apb', self._makeProvider(1))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            rval = apb.getActionObject('object/an_id')
            self.assertEqual(rval, apb._actions[0])
            rval = apb.getActionObject('object/not_existing_id')
            self.assertEqual(rval, None)
            self.assertRaises(ValueError, apb.getActionObject, 'wrong_format')

    def test_getActionInfo(self):
        wanted = {'id': 'an_id', 'title': 'A Title', 'description': '',
                  'url': '', 'category': 'object', 'visible': False,
                  'available': True, 'allowed': True, 'link_target': None,
                  'icon': ''}

        apb = self.site._setObject('portal_apb', self._makeProvider(1))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            rval = apb.getActionInfo(('object/an_id',))
            self.assertEqual(rval, wanted)
            rval = apb.getActionInfo('object/an_id')
            self.assertEqual(rval, wanted)
            self.assertRaises(ValueError, apb.getActionInfo, 'object/an_id',
                              check_visibility=1)

            # The following is nasty, but I want to make sure the ValueError
            # carries some useful information
            INVALID_ID = 'invalid_id'
            try:
                rval = apb.getActionInfo('object/%s' % INVALID_ID)
            except ValueError as e:
                message = e.args[0]
                detail = f'"{message}" does not offer action "{INVALID_ID}"'
                self.assertTrue(message.find(INVALID_ID) != -1, detail)
