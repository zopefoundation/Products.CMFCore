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
""" Cookie Crumbler: Enable cookies for non-cookie user folders.
"""

import base64
from urllib.parse import quote
from urllib.parse import unquote

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.special_dtml import HTMLFile
from DateTime.DateTime import DateTime
from OFS.interfaces import IObjectWillBeMovedEvent
from OFS.PropertyManager import PropertyManager
from OFS.SimpleItem import SimpleItem
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.lifecycleevent.interfaces import IObjectMovedEvent
from ZPublisher import BeforeTraverse
from ZPublisher.HTTPRequest import HTTPRequest

from .interfaces import IActionsTool
from .interfaces import ICookieCrumbler
from .utils import UniqueObject
from .utils import registerToolInterface


# Constants.
ATTEMPT_NONE = 0       # No attempt at authentication
ATTEMPT_LOGIN = 1      # Attempt to log in
ATTEMPT_RESUME = 2     # Attempt to resume session

ModifyCookieCrumblers = 'Modify Cookie Crumblers'
ViewManagementScreens = view_management_screens


class CookieCrumblerDisabled(Exception):

    """Cookie crumbler should not be used for a certain request.
    """


@implementer(ICookieCrumbler)
class CookieCrumbler(UniqueObject, PropertyManager, SimpleItem):

    """Reads cookies during traversal and simulates the HTTP auth headers.
    """

    id = 'cookie_authentication'

    manage_options = (
        PropertyManager.manage_options +
        SimpleItem.manage_options)

    meta_type = 'Cookie Crumbler'
    zmi_icon = 'fa fa-cookie-bite'

    security = ClassSecurityInfo()
    security.declareProtected(ModifyCookieCrumblers,  # NOQA: flake8: D001
                              'manage_editProperties')
    security.declareProtected(ModifyCookieCrumblers,  # NOQA: flake8: D001
                              'manage_changeProperties')
    security.declareProtected(ViewManagementScreens,  # NOQA: flake8: D001
                              'manage_propertiesForm')

    # By default, anonymous users can view login/logout pages.
    _View_Permission = ('Anonymous',)

    _properties = ({'id': 'title', 'type': 'string', 'mode': 'w',
                    'label': 'Title'},
                   {'id': 'auth_cookie', 'type': 'string', 'mode': 'w',
                    'label': 'Authentication cookie name'},
                   {'id': 'name_cookie', 'type': 'string', 'mode': 'w',
                    'label': 'User name form variable'},
                   {'id': 'pw_cookie', 'type': 'string', 'mode': 'w',
                    'label': 'User password form variable'},
                   {'id': 'persist_cookie', 'type': 'string', 'mode': 'w',
                    'label': 'User name persistence form variable'},
                   {'id': 'local_cookie_path', 'type': 'boolean', 'mode': 'w',
                    'label': 'Use cookie paths to limit scope'},
                   {'id': 'cache_header_value', 'type': 'string', 'mode': 'w',
                    'label': 'Cache-Control header value'},
                   {'id': 'log_username', 'type': 'boolean', 'mode': 'w',
                    'label': 'Log cookie auth username to access log'},
                   )

    auth_cookie = '__ac'
    name_cookie = '__ac_name'
    pw_cookie = '__ac_password'  # not used as cookie, just as request key
    persist_cookie = '__ac_persistent'
    local_cookie_path = False
    cache_header_value = 'private'
    log_username = True

    @security.private
    def delRequestVar(self, req, name):
        # No errors of any sort may propagate, and we don't care *what*
        # they are, even to log them.
        try:
            del req.other[name]
        except Exception:
            pass
        try:
            del req.form[name]
        except Exception:
            pass
        try:
            del req.cookies[name]
        except Exception:
            pass
        try:
            del req.environ[name]
        except Exception:
            pass

    @security.public
    def getCookiePath(self):
        if not self.local_cookie_path:
            return '/'
        parent = aq_parent(aq_inner(self))
        if parent is not None:
            return '/' + parent.absolute_url(1)
        else:
            return '/'

    # Allow overridable cookie set/expiration methods.
    @security.private
    def getCookieMethod(self, name, default=None):
        return getattr(self, name, default)

    @security.private
    def defaultSetAuthCookie(self, resp, cookie_name, cookie_value):
        kw = {}
        req = getRequest()
        if req is not None and req.get('SERVER_URL', '').startswith('https:'):
            # Ask the client to send back the cookie only in SSL mode
            kw['secure'] = 'y'
        resp.setCookie(cookie_name, cookie_value,
                       path=self.getCookiePath(), **kw)

    @security.private
    def defaultExpireAuthCookie(self, resp, cookie_name):
        resp.expireCookie(cookie_name, path=self.getCookiePath())

    def _setAuthHeader(self, ac, request, response):
        """Set the auth headers for both the Zope and Medusa http request
        objects.
        """
        request._auth = 'Basic %s' % ac
        response._auth = 1
        if self.log_username:
            # Set the authorization header in the medusa http request
            # so that the username can be logged to the Z2.log
            try:
                # Put the full-arm latex glove on now...
                medusa_headers = response.stdout._request._header_cache
            except AttributeError:
                pass
            else:
                medusa_headers['authorization'] = request._auth

    @security.private
    def modifyRequest(self, req, resp):
        """Copies cookie-supplied credentials to the basic auth fields.

        Returns a flag indicating what the user is trying to do with
        cookies: ATTEMPT_NONE, ATTEMPT_LOGIN, or ATTEMPT_RESUME.  If
        cookie login is disabled for this request, raises
        CookieCrumblerDisabled.
        """
        if not isinstance(req, HTTPRequest) or  \
           req['REQUEST_METHOD'] not in ('HEAD', 'GET', 'PUT', 'POST') or \
           'WEBDAV_SOURCE_PORT' in req.environ:
            raise CookieCrumblerDisabled

        # attempt may contain information about an earlier attempt to
        # authenticate using a higher-up cookie crumbler within the
        # same request.
        attempt = getattr(req, '_cookie_auth', ATTEMPT_NONE)

        if attempt == ATTEMPT_NONE:
            if req._auth:
                # An auth header was provided and no cookie crumbler
                # created it.  The user must be using basic auth.
                raise CookieCrumblerDisabled

            if self.pw_cookie in req and self.name_cookie in req:
                # Attempt to log in and set cookies.
                attempt = ATTEMPT_LOGIN
                name = req[self.name_cookie]
                pw = req[self.pw_cookie]
                ac = base64.encodebytes(
                    (f'{name}:{pw}').encode()).rstrip().decode()
                self._setAuthHeader(ac, req, resp)
                if req.get(self.persist_cookie, 0):
                    # Persist the user name (but not the pw or session)
                    expires = (DateTime() + 365).toZone('GMT').rfc822()
                    resp.setCookie(self.name_cookie, name,
                                   path=self.getCookiePath(),
                                   expires=expires)
                else:
                    # Expire the user name
                    resp.expireCookie(self.name_cookie,
                                      path=self.getCookiePath())
                method = self.getCookieMethod('setAuthCookie',
                                              self.defaultSetAuthCookie)
                method(resp, self.auth_cookie, quote(ac))
                self.delRequestVar(req, self.name_cookie)
                self.delRequestVar(req, self.pw_cookie)

            elif self.auth_cookie in req:
                # Attempt to resume a session if the cookie is valid.
                # Copy __ac to the auth header.
                ac = unquote(req[self.auth_cookie])
                if ac and ac != 'deleted':
                    try:
                        base64.decodebytes(ac.encode())
                    except Exception:
                        # Not a valid auth header.
                        pass
                    else:
                        attempt = ATTEMPT_RESUME
                        self._setAuthHeader(ac, req, resp)
                        self.delRequestVar(req, self.auth_cookie)
                        method = self.getCookieMethod(
                            'twiddleAuthCookie', None)
                        if method is not None:
                            method(resp, self.auth_cookie, quote(ac))

        req._cookie_auth = attempt
        return attempt

    def __call__(self, container, req):
        """The __before_publishing_traverse__ hook."""
        resp = req['RESPONSE']
        try:
            attempt = self.modifyRequest(req, resp)
        except CookieCrumblerDisabled:
            return
        if attempt != ATTEMPT_NONE:
            # Trying to log in or resume a session
            if self.cache_header_value:
                # we don't want caches to cache the resulting page
                resp.setHeader('Cache-Control', self.cache_header_value)
                # demystify this in the response.
                resp.setHeader('X-Cache-Control-Hdr-Modified-By',
                               'CookieCrumbler')
            phys_path = self.getPhysicalPath()
            # Cookies are in use.
            # Provide a logout page.
            req._logout_path = phys_path + ('logout',)

    @security.public
    def credentialsChanged(self, user, name, pw, request=None):
        """
        Updates cookie credentials if user details are changed.
        """
        if request is None:
            request = getRequest()  # BBB for Membershiptool
        reponse = request['RESPONSE']
        ac = base64.encodebytes(
            (f'{name}:{pw}').encode()).rstrip().decode()
        method = self.getCookieMethod('setAuthCookie',
                                      self.defaultSetAuthCookie)
        method(reponse, self.auth_cookie, quote(ac))

    @security.public
    def logout(self, response=None):
        """
        Logs out the user
        """
        target = None
        if response is None:
            response = getRequest()['RESPONSE']  # BBB for App.Management
            atool = getUtility(IActionsTool)
            target = atool.getActionInfo('user/logout')['url']
        method = self.getCookieMethod('expireAuthCookie',
                                      self.defaultExpireAuthCookie)
        method(response, cookie_name=self.auth_cookie)
        # BBB for App.Management
        if target is not None:
            response.redirect(target)

    @security.public
    def propertyLabel(self, id):
        """Return a label for the given property id
        """
        for p in self._properties:
            if p['id'] == id:
                return p.get('label', id)
        return id


InitializeClass(CookieCrumbler)
registerToolInterface('cookie_authentication', ICookieCrumbler)


def handleCookieCrumblerEvent(ob, event):
    """ Event subscriber for (un)registering a CC as a before traverse hook.
    """
    if not ICookieCrumbler.providedBy(ob):
        return

    if IObjectMovedEvent.providedBy(event):
        if event.newParent is not None:
            # register before traverse hook
            handle = ob.meta_type + '/' + ob.getId()
            nc = BeforeTraverse.NameCaller(ob.getId())
            BeforeTraverse.registerBeforeTraverse(event.newParent, nc, handle)
    elif IObjectWillBeMovedEvent.providedBy(event):
        if event.oldParent is not None:
            # unregister before traverse hook
            handle = ob.meta_type + '/' + ob.getId()
            BeforeTraverse.unregisterBeforeTraverse(event.oldParent, handle)


manage_addCCForm = HTMLFile('dtml/addCC', globals())
manage_addCCForm.__name__ = 'addCC'


def manage_addCC(dispatcher, id, title='', REQUEST=None):
    """ """
    ob = CookieCrumbler()
    ob.id = id
    ob.title = title
    dispatcher._setObject(ob.getId(), ob)
    ob = getattr(dispatcher.this(), ob.getId())
    if REQUEST is not None:
        return dispatcher.manage_main(dispatcher, REQUEST)
