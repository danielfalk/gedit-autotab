# -*- coding: utf-8 -*-
#
# Auto Tab for gedit, automatically detect tab preferences for source files.
#
# Copyright (C) 2007 Kristoffer Lundén (kristoffer.lunden@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, 
# Boston, MA 02111-1307, USA.
#

# Man, is this the weirdest need-to-do ever...
from __future__ import division
import gedit
import gconf
from operator import itemgetter

class AutoTab(gedit.Plugin):

  # Run, plugin run!
  def activate(self, window):
  
    self.window = window
    self.spaces_instead_of_tabs = False
    self.tabs_width = 2
    
    # Prime the statusbar
    self.statusbar = window.get_statusbar()
    self.context_id = self.statusbar.get_context_id("AutoTab")
    self.message_id = None

    # Init defaults, set up callbacks to get notified of changes
    client = gconf.client_get_default() 
    self.new_tabs_size(client)
    self.new_insert_spaces(client)
    client.notify_add("/apps/gedit-2/preferences/editor/tabs/tabs_size", self.new_tabs_size)
    client.notify_add("/apps/gedit-2/preferences/editor/tabs/insert_spaces", self.new_insert_spaces)
  
  # If tab size changes behind our backs
  def new_tabs_size(self, client, id=None, entry=None, data=None):
    self.tabs_width = client.get_int("/apps/gedit-2/preferences/editor/tabs/tabs_size")
    self.update_tabs(self.tabs_width, self.spaces_instead_of_tabs)
  
  # If space/tabs changes behind our backs
  def new_insert_spaces(self, client, id=None, entry=None, data=None):
    self.spaces_instead_of_tabs = client.get_bool("/apps/gedit-2/preferences/editor/tabs/insert_spaces")
    self.update_tabs(self.tabs_width, self.spaces_instead_of_tabs)

  # Update the values and set a new statusbar message  
  def update_tabs(self, size, space):
    view = self.window.get_active_view()
    if view:
      view.set_tabs_width(size)
      view.set_insert_spaces_instead_of_tabs(space)
      message = "%s%i" % (space and 'S' or 'T', size)
      self.update_status(message)
      
  # Statusbar message
  def update_status(self, message):
    if self.message_id:
      self.statusbar.remove(self.context_id, self.message_id)
    self.message_id = self.statusbar.push(self.context_id, "Auto Tab: (%s)" % message)

  # And now we stop running...  
  def deactivate(self, window):
    if self.message_id:
      self.statusbar.remove(self.context_id, self.message_id)

  # Switched to new doc etc. Could probably be narrowed down.
  def update_ui(self, window):
    doc = window.get_active_document()
    if doc:
      start, end = doc.get_bounds()
      text = doc.get_text(start, end)

      # A little index is being built...
      indent_count = {'tabs':0, '12':0, '123':0, '1234':0, '12345678':0}
      
      for line in text.splitlines():
        if len(line) == 0: continue
        
        # Tab or space?
        if line[0] == "\t":
          indent_count['tabs'] += 1
        else:
          length = 0
          while line[0] == " ":
            length += 1
            line = line[1:]
            if len(line) == 0: break

          # Otherwise empty lines have often bogus indents
          if len(line) == 0: continue
          
          # No spaces there
          if length == 0: continue

          # Count the possible space variations from the common cases.          
          elif length % 8 == 0:
            indent_count['12345678'] += 1
            indent_count['1234'] += 1
            indent_count['12'] += 1
          elif length % 4 == 0:
            indent_count['1234'] += 1
            indent_count['12'] += 1
          elif length % 6 == 0:
            indent_count['123'] += 1
            indent_count['12'] += 1
          elif length % 3 == 0:
            indent_count['123'] += 1
          elif length == 2:
            indent_count['12'] += 1
      
      # Weird sort function. Also, a reverse would have been more logical,
      # but no array.shift() in python (though there are workarounds).      
      sorted_indent = sorted(indent_count.items(), key=itemgetter(1))
      if sorted_indent[-1][1] == 0:
        self.update_tabs(self.tabs_width, self.spaces_instead_of_tabs)
      elif sorted_indent[-1][0] == 'tabs':
        self.update_tabs(self.tabs_width, False)
      else:
        try:
          if sorted_indent[-1][1] == 2 and sorted_indent[-2][1] % 8 == 0:
            # If somethig needs tweaking, look at the 1.1 here.
            # It helps weight 2 spaces versus 4 and 8, and is found out via
            # a lot of tests. It may need to be slightly bigger.
            if sorted_indent[-1][1] / sorted_indent[-2][1] < 1.1:
              sorted_indent.pop()
        except ZeroDivisionError: pass
        
        self.update_tabs(len(sorted_indent[-1][0]), True)