"""CookieCrumbler provides cookie based authenticaion

$Id$

"""

from zope.interface import Interface, Attribute

class ICookieCrumbler(Interface):

    """Reads cookies during traversal and simulates the HTTP auth headers.
    """
    
    auth_cookie = Attribute("""The key of the authorisation cookie""")
    name_cookie = Attribute("""They key of the authorised user cookie""")
    pw_cookie = Attribute("""The key of the password cookie""")
    persist_cookie = Attribute("""The key of the persistent cookie""")
    local_cookie_path = Attribute("""If True, the cookie tied to the local path?""")
    cache_header_value = Attribute("""If present, the login page will not be cached""")
    log_username = Attribute("""If True, the username will in appear in Zope's log""")
    
    def delRequestVar(req, name):
         """No errors of any sort may propagate, and we don't care *what*
          they are, even to log them."""

    def getCookiePath():
        """Get the path for the cookie
        the parent URL if local_cookie_path is True otherwise /"""
        return path

    def getCookieMethod(name, default=None):
        """ Allow overridable cookie set/expiration methods."""
        return getattr(name, default)

    def defaultSetAuthCookie(resp, cookie_name, cookie_value):
        """Set the authorisation cookie"""

    def defaultExpireAuthCookie(resp, cookie_name):
        """Expire the cookie"""

    def _setAuthHeader(ac, request, response):
        """Set the auth headers for both the Zope and Medusa http request
        objects.
        """

    def modifyRequest(req, resp):
        """Copies cookie-supplied credentials to the basic auth fields.

        Returns a flag indicating what the user is trying to do with
        cookies: ATTEMPT_NONE, ATTEMPT_LOGIN, or ATTEMPT_RESUME.  If
        cookie login is disabled for this request, raises
        CookieCrumblerDisabled.
        """

    def __call__(container, req):
        """The __before_publishing_traverse__ hook."""

    def credentialsChanged(user, name, pw):
        """# XXX: this method violates the rules for tools/utilities:
        # it depends on self.REQUEST """

    def _cleanupResponse():
        """# XXX: this method violates the rules for tools/utilities:
        # it depends on self.REQUEST"""

    def unauthorized():
        """Remove authentication cookies and redirect to standard unauthorized"""

    def _unauthorized():
        """Remove authentication cookies and redirect to standard _unauthorized"""

    def getUnauthorizedURL():
        """
        Redirects to the login page.
        """

    def logout():
        """
        Logs out the user and redirects to the logout page.
        """

    def propertyLabel(id):
        """Return a label for the given property id
        """