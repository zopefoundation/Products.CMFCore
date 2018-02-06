##############################################################################
#
# Copyright (c) 2018 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import App.interfaces
import cmf.icons
import zope.component


@zope.component.adapter(App.interfaces.IRenderZMIEvent)
def load_assets(event):
    """Load the CMS icons for the ZMI."""
    cmf.icons.cmf_icons.need()
