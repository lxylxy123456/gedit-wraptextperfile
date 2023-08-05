#   Wrap Text Per File - Allow different text wrapping configurations per file
#   Copyright (C) 2023  lxylxy123456
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Many logic are from gedit/gedit-window.c, see:
	https://gitlab.gnome.org/GNOME/gedit/-/compare/d7e6d63e...bcd35bfb
"""

from gi.repository import GObject, Gedit, Gtk, Gio, GLib

MENU_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="line-col-menu">
    <section>
      <item>
        <attribute name="label" translatable="yes">Automatic Indentation</attribute>
        <attribute name="action">win.auto-indent</attribute>
      </item>
    </section>
    <section>
      <item>
        <attribute name="label" translatable="yes">Display line numbers</attribute>
        <attribute name="action">win.show-line-numbers</attribute>
      </item>
      <item>
        <attribute name="label" translatable="yes">Display right margin</attribute>
        <attribute name="action">win.display-right-margin</attribute>
      </item>
      <item>
        <attribute name="label" translatable="yes">Highlight current line</attribute>
        <attribute name="action">win.highlight-current-line</attribute>
      </item>
      <item>
        <attribute name="label" translatable="yes">Text wrapping</attribute>
        <attribute name="action">win.wrap-mode</attribute>
      </item>
    </section>
  </menu>
</interface>
"""

class ExamplePyPlugin(GObject.Object, Gedit.WindowActivatable):
	__gtype_name__ = "ExamplePyPlugin"

	window = GObject.property(type=Gedit.Window)

	def __init__(self):
		GObject.Object.__init__(self)
		self.statusbar = None
		self.menu_button = None

	def do_activate(self):
		self.print('activate', self.window)
		assert self.statusbar is None
		assert self.menu_button is None

		# Add menu button to status bar
		self.statusbar = self.window.get_statusbar()
		# afterwards: a.get_child().get_children()[0].get_label() == 'Tab ...'
		a = self.statusbar.get_children()[-3]
		# afterwards: b.get_child().get_children()[0].get_label() == 'Plain ...'
		b = self.statusbar.get_children()[-4]
		assert a.__class__.__name__ == 'GeditStatusMenuButton'
		assert b.__class__.__name__ == 'GeditStatusMenuButton'
		self.menu_button = type(a)()
		self.statusbar.pack_end(self.menu_button, False, False, 0)
		#assert self.menu_button == self.statusbar.get_children()[-5]
		self.menu_button.get_child().get_children()[0].set_label('569')

		# Setup menu model
		builder = Gtk.Builder.new_from_string(MENU_XML, -1)
		menu = builder.get_object("line-col-menu")
		self.menu_button.set_menu_model(menu)

		self.sync_current_tab_actions()

	def do_deactivate(self):
		self.print('deactivate', self.window)
		assert self.statusbar is not None
		assert self.menu_button is not None
		Gtk.Container.remove(self.statusbar, self.menu_button)
		self.sync_current_tab_actions()

	def do_update_state(self):
		self.print('update', self.window)
		assert self.statusbar is not None
		assert self.menu_button is not None
		assert len(self.window.get_views()) == len(self.window.get_documents())
		if self.window.get_documents():
			self.menu_button.show()
		else:
			self.menu_button.hide()
		self.sync_current_tab_actions()

	def print(self, *args, **kwargs):
		"""
		To debug, remove the comment to print function call.
		"""
		#print(*args, **kwargs)

	def add_actions(self, view):
		"""
		From Gedit C function sync_current_tab_actions().
		"""
		self.print('add_actions', view)
		action = Gio.PropertyAction.new('auto-indent', view, 'auto-indent')
		self.window.add_action(action)
		action = Gio.PropertyAction.new('show-line-numbers', view,
										'show-line-numbers')
		self.window.add_action(action)
		action = Gio.PropertyAction.new('display-right-margin', view,
										'show-right-margin')
		self.window.add_action(action)
		action = Gio.PropertyAction.new('highlight-current-line', view,
										'highlight-current-line')
		self.window.add_action(action)

		text_wrapping_entrie = [['wrap-mode', None, None, 'false',
								 self._text_wrapping_change_state]]
		self.window.add_action_entries(text_wrapping_entrie)
		self.update_statusbar_wrap_mode_checkbox_from_view(view)

	def remove_actions(self):
		"""
		From Gedit C function remove_actions().
		"""
		self.print('remove_actions')
		self.window.remove_action('auto-indent')
		self.window.remove_action('show-line-numbers')
		self.window.remove_action('display-right-margin')
		self.window.remove_action('highlight-current-line')
		self.window.remove_action('wrap-mode')

	def sync_current_tab_actions(self):
		"""
		From Gedit C function sync_current_tab_actions().
		"""
		view = self.window.get_active_view()
		if view is not None:
			self.add_actions(view)
		else:
			self.remove_actions()

	def update_statusbar_wrap_mode_checkbox_from_view(self, view):
		"""
		From Gedit C function update_statusbar_wrap_mode_checkbox_from_view().
		"""
		wrap_mode = self.window.get_active_view().get_wrap_mode()
		simple_action = Gio.ActionMap.lookup_action(self.window, 'wrap-mode')
		value = (wrap_mode != Gtk.WrapMode.NONE)
		simple_action.set_state(GLib.Variant.new_boolean(value))

	def _text_wrapping_change_state(self, action, value, user_data):
		"""
		From Gedit C function _gedit_window_text_wrapping_change_state().
		Note: not all logics are copied, because window.priv is private.
		e.g. GTK_WRAP_WORD is hard-coded.
		"""
		self.print('_text_wrapping_change_state', action, value, user_data)
		action.set_state(value)
		if value:
			self.window.get_active_view().set_wrap_mode(Gtk.WrapMode.WORD)
		else:
			self.window.get_active_view().set_wrap_mode(Gtk.WrapMode.NONE)

