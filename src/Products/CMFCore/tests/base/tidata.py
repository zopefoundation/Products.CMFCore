ModifyPortalContent = 'Modify portal content'
View = 'View'

FTIDATA_ACTIONS = (
      {'id': 'Action Tests',
       'meta_type': 'Dummy',
       'aliases': {},
       'actions': ({'id': 'view',
                    'title': 'View',
                    'action': 'string:',
                    'permissions': ('View',),
                    'category': 'object',
                    'visible': 1},
                   {'id': 'edit',
                    'title': 'Edit',
                    'action': 'string:${object_url}/foo_edit',
                    'permissions': ('Modify',),
                    'category': 'object',
                    'visible': 1},
                   {'id': 'objectproperties',
                    'title': 'Object Properties',
                    'action': 'string:foo_properties',
                    'permissions': ('Modify',),
                    'category': 'object',
                    'visible': 1},
                   {'id': 'slot',
                    'title': 'Slot',
                    'action': 'string:foo_slot',
                    'category': 'object',
                    'visible': 0})},)

FTIDATA_DUMMY = (
      {'id': 'Dummy Content',
       'title': 'Dummy Content Title',
       'meta_type': 'Dummy',
       'product': 'FooProduct',
       'factory': 'addFoo',
       'aliases': {},
       'actions': ({'id': 'view',
                    'title': 'View',
                    'action': 'string:view',
                    'permissions': ('View',)},
                   {'id': 'view2',
                    'title': 'View2',
                    'action': 'string:view2',
                    'permissions': ('View',)},
                   {'id': 'edit',
                    'title': 'Edit',
                    'action': 'string:edit',
                    'permissions': ('forbidden permission',)})},)

FTIDATA_CMF15 = (
      {'id': 'Dummy Content 15',
       'meta_type': 'Dummy',
       'description': 'Dummy Content.',
       'icon': 'dummy_icon.gif',
       'product': 'FooProduct',
       'factory': 'addFoo',
       'immediate_view': 'metadata.html',
       'aliases': {'(Default)': 'dummy_view',
                   'view': 'dummy_view',
                   'view.html': 'dummy_view',
                   'edit.html': 'dummy_edit_form',
                   'metadata.html': 'metadata_edit_form',
                   'gethtml': 'source_html'},
       'actions': ({'id': 'view',
                    'title': 'View',
                    'action': 'string:${object_url}/view.html',
                    'permissions': (View,)},
                   {'id': 'edit',
                    'title': 'Edit',
                    'action': 'string:${object_url}/edit.html',
                    'permissions': (ModifyPortalContent,)},
                   {'id': 'metadata',
                    'title': 'Metadata',
                    'action': 'string:${object_url}/metadata.html',
                    'permissions': (ModifyPortalContent,)})},)

FTIDATA_CMF = (
      {'id': 'Dummy Content 15',
       'meta_type': 'Dummy',
       'description': 'Dummy Content.',
       'icon_expr': 'string:${portal_url}/dummy_icon.gif',
       'product': 'FooProduct',
       'factory': 'addFoo',
       'immediate_view': 'properties',
       'aliases': {'(Default)': 'dummy_view',
                   'view': 'dummy_view',
                   'edit': 'dummy_edit_form',
                   'properties': 'metadata_edit_form',
                   'gethtml': 'source_html'},
       'actions': ({'id': 'view',
                    'title': 'View',
                    'action': 'string:${object_url}',
                    'permissions': (View,)},
                   {'id': 'edit',
                    'title': 'Edit',
                    'action': 'string:${object_url}/edit',
                    'permissions': (ModifyPortalContent,)},
                   {'id': 'metadata',
                    'title': 'Metadata',
                    'action': 'string:${object_url}/properties',
                    'permissions': (ModifyPortalContent,)})},)

STI_SCRIPT = """\
## Script (Python) "addBaz"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=folder, id
##title=
##
product = folder.manage_addProduct['FooProduct']
product.addFoo(id)
item = getattr(folder, id)
return item
"""
