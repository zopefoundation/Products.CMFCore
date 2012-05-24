##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""CookieCrumbler tests. """

import unittest
import Testing

from zope.component import eventtesting
from zope.interface.verify import verifyClass
from zope.testing.cleanup import cleanUp


def makerequest(root, stdout, stdin=None):
    # Customized version of Testing.makerequest.makerequest()
    from cStringIO import StringIO
    from ZPublisher.HTTPRequest import HTTPRequest
    from ZPublisher.HTTPResponse import HTTPResponse

    resp = HTTPResponse(stdout=stdout)
    environ = {}
    environ['SERVER_NAME'] = 'example.com'
    environ['SERVER_PORT'] = '80'
    environ['REQUEST_METHOD'] = 'GET'
    if stdin is None:
        stdin = StringIO('')  # Empty input
    req = HTTPRequest(stdin, environ, resp)
    req['PARENTS'] = [root]
    return req


class CookieCrumblerTests(unittest.TestCase):

    _CC_ID = 'cookie_authentication'

    def _getTargetClass(self):
        from Products.CMFCore.CookieCrumbler  import CookieCrumbler
        return CookieCrumbler

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def setUp(self):
        from zope.component import provideHandler
        from zope.component.interfaces import IObjectEvent
        from Products.CMFCore.interfaces import ICookieCrumbler
        from Products.CMFCore.CookieCrumbler import handleCookieCrumblerEvent

        self._finally = None

        eventtesting.setUp()
        provideHandler(handleCookieCrumblerEvent,
                       adapts=(ICookieCrumbler, IObjectEvent))

    def tearDown(self):
        from AccessControl.SecurityManagement import noSecurityManager

        if self._finally is not None:
            self._finally()

        noSecurityManager()
        cleanUp()

    def _makeSite(self):
        import base64
        from cStringIO import StringIO
        import urllib

        try:
            from OFS.userfolder import UserFolder
        except ImportError:
            # BBB for Zope < 2.13
            from AccessControl.User import UserFolder
        
        from OFS.Folder import Folder
        from OFS.DTMLMethod import DTMLMethod

        root = Folder()
        root.isTopLevelPrincipiaApplicationObject = 1  # User folder needs this
        root.getPhysicalPath = lambda: ()  # hack
        root._View_Permission = ('Anonymous',)

        users = UserFolder()
        users._setId('acl_users')
        users._doAddUser('abraham', 'pass-w', ('Patriarch',), ())
        users._doAddUser('isaac', 'pass-w', ('Son',), ())
        root._setObject(users.id, users)

        cc = self._makeOne()
        cc.id = self._CC_ID
        root._setObject(cc.id, cc)

        index = DTMLMethod()
        index.munge('This is the default view')
        index._setId('index_html')
        root._setObject(index.getId(), index)

        login = DTMLMethod()
        login.munge('Please log in first.')
        login._setId('login_form')
        root._setObject(login.getId(), login)

        protected = DTMLMethod()
        protected._View_Permission = ('Manager',)
        protected.munge('This is the protected view')
        protected._setId('protected')
        root._setObject(protected.getId(), protected)

        req = makerequest(root, StringIO())
        self._finally = req.close

        credentials = urllib.quote(
            base64.encodestring('abraham:pass-w').rstrip())

        return root, cc, req, credentials

    def test_interfaces(self):
        from Products.CMFCore.interfaces import ICookieCrumbler

        verifyClass(ICookieCrumbler, self._getTargetClass())

    def testNoCookies(self):
        # verify the cookie crumbler doesn't break when no cookies are given
        root, cc, req, credentials = self._makeSite()
        req.traverse('/')
        self.assertEqual(req['AUTHENTICATED_USER'].getUserName(),
                         'Anonymous User')

    def testCookieLogin(self):
        # verify the user and auth cookie get set
        root, cc, req, credentials = self._makeSite()

        req.cookies['__ac_name'] = 'abraham'
        req.cookies['__ac_password'] = 'pass-w'
        req.traverse('/')

        self.assertTrue(req.has_key('AUTHENTICATED_USER'))
        self.assertEqual(req['AUTHENTICATED_USER'].getUserName(),
                         'abraham')
        resp = req.response
        self.assertTrue(resp.cookies.has_key('__ac'))
        self.assertEqual(resp.cookies['__ac']['value'],
                         credentials)
        self.assertEqual(resp.cookies['__ac']['path'], '/')

    def testCookieResume(self):
        # verify the cookie crumbler continues the session
        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac'] = credentials
        req.traverse('/')
        self.assertTrue(req.has_key('AUTHENTICATED_USER'))
        self.assertEqual(req['AUTHENTICATED_USER'].getUserName(),
                         'abraham')

    def testPasswordShredding(self):
        # verify the password is shredded before the app gets the request
        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac_name'] = 'abraham'
        req.cookies['__ac_password'] = 'pass-w'
        self.assertTrue(req.has_key('__ac_password'))
        req.traverse('/')
        self.assertFalse( req.has_key('__ac_password'))
        self.assertFalse( req.has_key('__ac'))

    def testCredentialsNotRevealed(self):
        # verify the credentials are shredded before the app gets the request
        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac'] = credentials
        self.assertTrue(req.has_key('__ac'))
        req.traverse('/')
        self.assertFalse( req.has_key('__ac'))

    def testAutoLoginRedirection(self):
        # Redirect unauthorized anonymous users to the login page
        from Products.CMFCore.CookieCrumbler  import Redirect

        root, cc, req, credentials = self._makeSite()
        self.assertRaises(Redirect, req.traverse, '/protected')

    def testDisabledAutoLoginRedirection(self):
        # When disable_cookie_login__ is set, don't redirect.
        from zExceptions.unauthorized import Unauthorized

        root, cc, req, credentials = self._makeSite()
        req['disable_cookie_login__'] = 1
        self.assertRaises(Unauthorized, req.traverse, '/protected')


    def testNoRedirectAfterAuthenticated(self):
        # Don't redirect already-authenticated users to the login page,
        # even when they try to access things they can't get.
        from zExceptions.unauthorized import Unauthorized

        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac'] = credentials
        self.assertRaises(Unauthorized, req.traverse, '/protected')

    def testRetryLogin(self):
        # After a failed login, CookieCrumbler should give the user an
        # opportunity to try to log in again.
        from Products.CMFCore.CookieCrumbler  import Redirect

        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac_name'] = 'israel'
        req.cookies['__ac_password'] = 'pass-w'
        try:
            req.traverse('/protected')
        except Redirect, s:
            # Test passed
            if hasattr(s, 'args'):
                s = s.args[0]
            self.assertTrue(s.find('came_from=') >= 0)
            self.assertTrue(s.find('retry=1') >= 0)
            self.assertTrue(s.find('disable_cookie_login__=1') >= 0)
        else:
            self.fail('Did not redirect')


    def testLoginRestoresQueryString(self):
        # When redirecting for login, the came_from form field should
        # include the submitted URL as well as the query string.
        import urllib
        from Products.CMFCore.CookieCrumbler  import Redirect

        root, cc, req, credentials = self._makeSite()
        req['PATH_INFO'] = '/protected'
        req['QUERY_STRING'] = 'a:int=1&x:string=y'
        try:
            req.traverse('/protected')
        except Redirect, s:
            if hasattr(s, 'args'):
                s = s.args[0]
            to_find = urllib.quote('/protected?' + req['QUERY_STRING'])
            self.assertTrue(s.find(to_find) >= 0, s)
        else:
            self.fail('Did not redirect')

    def testCacheHeaderAnonymous(self):
        # Should not set cache-control
        root, cc, req, credentials = self._makeSite()
        req.traverse('/')
        self.assertEqual(
            req.response.headers.get('cache-control', ''), '')

    def testCacheHeaderLoggingIn(self):
        # Should set cache-control
        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac_name'] = 'abraham'
        req.cookies['__ac_password'] = 'pass-w'
        req.traverse('/')
        self.assertEqual(
            req.response.headers.get('cache-control', ''), 'private')

    def testCacheHeaderAuthenticated(self):
        # Should set cache-control
        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac'] = credentials
        req.traverse('/')
        self.assertEqual(
            req.response.headers.get('cache-control', ''), 'private')

    def testCacheHeaderDisabled(self):
        # Should not set cache-control
        root, cc, req, credentials = self._makeSite()
        cc.cache_header_value = ''
        req.cookies['__ac'] = credentials
        req.traverse('/')
        self.assertEqual(
            req.response.headers.get('cache-control', ''), '')

    def testDisableLoginDoesNotPreventPasswordShredding(self):
        # Even if disable_cookie_login__ is set, read the cookies
        # anyway to avoid revealing the password to the app.
        # (disable_cookie_login__ does not mean disable cookie
        # authentication, it only means disable the automatic redirect
        # to the login page.)
        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac_name'] = 'abraham'
        req.cookies['__ac_password'] = 'pass-w'
        req['disable_cookie_login__'] = 1
        req.traverse('/')
        self.assertEqual(req['AUTHENTICATED_USER'].getUserName(),
                         'abraham')
        # Here is the real test: the password should have been shredded.
        self.assertFalse( req.has_key('__ac_password'))

    def testDisableLoginDoesNotPreventPasswordShredding2(self):
        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac'] = credentials
        req['disable_cookie_login__'] = 1
        req.traverse('/')
        self.assertEqual(req['AUTHENTICATED_USER'].getUserName(),
                         'abraham')
        self.assertFalse( req.has_key('__ac'))

    def testMidApplicationAutoLoginRedirection(self):
        # Redirect anonymous users to login page if Unauthorized
        # occurs in the middle of the app
        from zExceptions.unauthorized import Unauthorized

        root, cc, req, credentials = self._makeSite()
        req.traverse('/')
        try:
            raise Unauthorized
        except:
            req.response.exception()
            self.assertEqual(req.response.status, 302)

    def testMidApplicationAuthenticationButUnauthorized(self):
        # Don't redirect already-authenticated users to the login page,
        # even when Unauthorized happens in the middle of the app.
        from zExceptions.unauthorized import Unauthorized

        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac'] = credentials
        req.traverse('/')
        try:
            raise Unauthorized
        except:
            req.response.exception()
            self.assertEqual(req.response.status, 401)

    def testRedirectOnUnauthorized(self):
        # Redirect already-authenticated users to the unauthorized
        # handler page if that's what the sysadmin really wants.
        from Products.CMFCore.CookieCrumbler  import Redirect

        root, cc, req, credentials = self._makeSite()
        cc.unauth_page = 'login_form'
        req.cookies['__ac'] = credentials
        self.assertRaises(Redirect, req.traverse, '/protected')

    def testLoginRatherThanResume(self):
        # When the user presents both a session resume and new
        # credentials, choose the new credentials (so that it's
        # possible to log in without logging out)
        root, cc, req, credentials = self._makeSite()
        req.cookies['__ac_name'] = 'isaac'
        req.cookies['__ac_password'] = 'pass-w'
        req.cookies['__ac'] = credentials
        req.traverse('/')

        self.assertTrue(req.has_key('AUTHENTICATED_USER'))
        self.assertEqual(req['AUTHENTICATED_USER'].getUserName(),
                         'isaac')

    def testCreateForms(self):
        # Verify the factory creates the login forms.
        from Products.CMFCore.CookieCrumbler  import manage_addCC

        if 'CMFCore' in self._getTargetClass().__module__:
            # This test is disabled in CMFCore.
            return

        root, cc, req, credentials = self._makeSite()
        root._delObject('cookie_authentication')
        manage_addCC(root, 'login', create_forms=1)
        ids = root.login.objectIds()
        ids.sort()
        self.assertEqual(tuple(ids), (
            'index_html', 'logged_in', 'logged_out', 'login_form',
            'standard_login_footer', 'standard_login_header'))

    def test_before_traverse_hooks(self):
        from OFS.Folder import Folder
        container = Folder()
        cc = self._makeOne()
        cc._setId(self._CC_ID)

        marker = []
        bt_before = getattr(container, '__before_traverse__', marker)
        self.assertTrue(bt_before is marker)

        container._setObject(self._CC_ID, cc)

        bt_added = getattr(container, '__before_traverse__')
        self.assertEqual(len(bt_added.items()), 1)
        k, v = bt_added.items()[0]
        self.assertTrue(k[1].startswith(self._getTargetClass().meta_type))
        self.assertEqual(v.name, self._CC_ID)

        container._delObject(self._CC_ID)

        bt_removed = getattr(container, '__before_traverse__')
        self.assertEqual(len(bt_removed.items()), 0)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(CookieCrumblerTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
