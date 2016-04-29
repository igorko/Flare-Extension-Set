#!/usr/bin/python
# -*- coding:utf-8 -*-
##########################################################################################################
#
#   Flare Quest Editor by Viktor S. Marton <msv@titok.info>
#
#   Copyright and License:
#       Flare Quest Editor is released under the GNU GPL version 3. Later versions are permitted.
#       Most of Flare is Copyright 2011 Clint Bellanger.
#       Contributors retain copyrights to their original contributions.
#       All of Flare's source code is released under the GNU GPL version 3. Later versions are permitted.
#       All of Flare's art and data files are released under CC-BY-SA 3.0. Later versions are permitted.
#
##########################################################################################################
#
#   Before you want to use the Flare Quest Editor, you have to install Flare:
#       $ sudo apt-get install flare
#
#   Type this command to run the editor application:
#       $ python flare_quest_edit.py
#
#   Or load it into geany and press F5.
#
#   Or set the executable flag of script (once) and run the script directly:
#       $ chmod -x flare_quest_edit.py
#       $ ./flare_quest_edit.py#
#
##########################################################################################################


__VERSION__ = "0.2.3"

__HELP__ = """
Flare Quest Editor usage

Buttons:
 New - Create new mod or/and new level (autosave actual)
 Save - Store actual level and stay editing.

Keys:
 F11 - Switch fullscreen.
 Arrows - Scroll drawing area.

Mouse buttons:
 Left - Put the selected elements into map. (Bg - as background, Obj - as object, Unit - as enemy)
 Middle or Ctrl+Left - Scroll this position into center of window.
 Right - Create/modify/delete quest event linked to the position. Or edit collision data of position. Or delete elements.

Checkboxes:
 OBJ - You can hide the object to see ground better with "obj" checkbox.
 POS - You can look at the coordinates of tile and collision value with "pos" checkbox.
  (Places of the mouse button press and button release are the corners of the groupped operations.)
 RND - You can select multiple tiles (with Ctrl or Shift) to put these into map. Check 'rnd' to randomized usage.

Enjoy!
"""

# Parameters
TITLE = "Flare Quest Editor 2012-2014 v%s (C)Viktor S. Marton <msv@titok.info> GPL" % __VERSION__
DEF_X_SIZE = 600
DEF_Y_SIZE = 500
TILE_WIDTH = 64
TILE_HEIGHT = 32
TEXT_COLOR = "#999"
TILE_COLOR = "#fff"
OBJECT_COLOR = "#cc0"
EVENT_COLOR = "#f1f"
SELECTION_COLOR = "#fff"
BACKGROUND_COLOR = "#888"
COLLISION_COLORS = ["#080","#800","#008","#444","#880"]
SHADOW_COLOR = "#111"
PRELOAD = True
SCROLL_SPEED = 2
MARKER_BORDER = 8

# Requested Python modules
import pygtk; pygtk.require( '2.0' )
import gtk, pango
import os, shutil
import random

# Environment
WORK_DIR = "./flare/" if os.path.isdir( "./flare/" ) else "./"
FLARE_DIR = "./"
print( "Looking for Flare data directories..." )
for testdir in [td.rstrip( "/" ) + "/flare/" for td in os.getenv( 'XDG_DATA_DIRS', "" ).split( ":" ) if td.strip()] + [
    "/usr/local/share/flare/",
    "/usr/local/share/games/flare/",
    "/usr/share/flare/",
    "/usr/share/games/flare/",
    "/usr/share/games/flare/flare-game/",
    "./flare/",
    "./"
]:
    print( " Check '%s' directory" % testdir )
    if os.path.isdir( testdir ):
        print( "Flare data found and use in '%s'" % testdir )
        FLARE_DIR = testdir
        break

def copytree( src, dst ):
    """
        Copy directory tree.

        @param src: source tree
        @param dst: destination
    """

    if not os.path.exists( dst ): os.makedirs( dst )
    for name in os.listdir( src ):
        srcname = os.path.join( src, name )
        dstname = os.path.join( dst, name )
        try:
            if os.path.isdir( srcname ): copytree( srcname, dstname )
            elif not os.path.exists( dstname ): shutil.copyfile( srcname, dstname )
        except Exception, E: print( "ERROR: Copy %s -> %s is not possible!" % ( srcname, dstname ) )


# Create missing directories and files
print( "Create missing directories and files..." )
if not os.path.exists( WORK_DIR + "mods" ): os.makedirs( WORK_DIR + "mods" )
if not os.path.exists( WORK_DIR + ".cache" ): os.makedirs( WORK_DIR + ".cache" )
copytree( FLARE_DIR + "mods", WORK_DIR + "mods" )
#if not os.path.exists( WORK_DIR + "mods/mods.txt" ): shutil.copyfile( FLARE_DIR + "mods/mods.txt", WORK_DIR + "mods/mods.txt" )

# Process parameters
if len( os.sys.argv ) > 1:
    if len( os.sys.argv ) == 2 and os.sys.argv[1] == "--help":
        print( __HELP__ )
        exit( 0 )
    if len( os.sys.argv ) == 2 and os.sys.argv[1] == "--prepare":
        exit( 0 )
    print( 'Usage: %s [--help | --prepare]' % os.sys.argv[0] )
    exit( 1 )


##########################################################################################################
#
#   Editor object
#

class FlareEdit:

    def area_expose( self, widget=None, event=None ):
        """
            Redraw editor main screen.

            @param widget: area pyGTK widget object
            @param event: redraw event object
        """

        # Show position
        def show_border( coll, xx, yy, txt, b ):
            self.area_buffer.draw_line( self.gc_event if txt == "" else self.gc_coll[coll], xx-TILE_WIDTH/2+b*2+2, yy-1, xx, yy-TILE_HEIGHT/2+b )   # Left top
            self.area_buffer.draw_line( self.gc_event if txt == "" else self.gc_coll[coll], xx, yy-TILE_HEIGHT/2+b, xx+TILE_WIDTH/2-b*2-2, yy-1 )   # Right top
            self.area_buffer.draw_line( self.gc_event if txt == "" else self.gc_coll[coll], xx-TILE_WIDTH/2+b*2+2, yy-1, xx, yy+TILE_HEIGHT/2-b-2 ) # Left bottom
            self.area_buffer.draw_line( self.gc_event if txt == "" else self.gc_coll[coll], xx, yy+TILE_HEIGHT/2-b-2, xx+TILE_WIDTH/2-b*2-2, yy-1 ) # Right bottom
            txt = self.window.create_pango_layout( txt )
            txt.set_font_description( pango.FontDescription( "sans 6" ) )
            size = txt.get_pixel_size()
            for x in range( -1, 2 ):
                for y in range( -1, 2 ):
                    self.area_buffer.draw_layout( self.gc_shadow if coll == -1 else self.gc_coll[coll], xx+x-size[0]/2, yy+y-6, txt, None, None )
            self.area_buffer.draw_layout( self.gc_event if coll == -1 else self.gc_tile, xx-size[0]/2, yy-6, txt, None, None )

        # Redraw background, if it is needed
        size = self.area.allocation
        if self.area_size != [size.width, size.height]:
            self.xslide += int( ( size.width - self.area_size[0] ) / TILE_WIDTH )
            self.yslide += int( ( size.height - self.area_size[1] ) / TILE_HEIGHT )
            self.area_size = [size.width, size.height]
            self.area_bg_buffer = gtk.gdk.Pixmap( self.window.window, size.width, size.height, depth=-1 )
            self.area_bg_buffer.draw_rectangle( self.area.get_style().black_gc, True, 0, 0, size.width, size.height )

        # Buffer for terrian
        if not self.gc:
            self.gc = gtk.gdk.GC( self.window.window ); self.gc.set_foreground( self.window.window.get_colormap().alloc_color( TEXT_COLOR ) )
            self.gc_tile = gtk.gdk.GC( self.window.window ); self.gc_tile.set_foreground( self.window.window.get_colormap().alloc_color( TILE_COLOR ) )
            self.gc_object = gtk.gdk.GC( self.window.window );  self.gc_object.set_foreground( self.window.window.get_colormap().alloc_color( OBJECT_COLOR ) )
            self.gc_event = gtk.gdk.GC( self.window.window ); self.gc_event.set_foreground( self.window.window.get_colormap().alloc_color( EVENT_COLOR ) )
            self.gc_shadow = gtk.gdk.GC( self.window.window ); self.gc_shadow.set_foreground( self.window.window.get_colormap().alloc_color( SHADOW_COLOR ) )
            self.gc_coll = []
            for x in range( len( COLLISION_COLORS ) ):
                self.gc_coll.append( gtk.gdk.GC( self.window.window ) )
                self.gc_coll[-1].set_foreground( self.window.window.get_colormap().alloc_color( COLLISION_COLORS[x] ) )
        self.area_buffer = gtk.gdk.Pixmap( self.window.window, size.width, size.height, depth=-1 )
        self.area_buffer.draw_drawable( self.gc, self.area_bg_buffer, 0, 0, 0, 0, -1, -1 )

        # Create view
        map_id = self.data["mods"][self.actual_mod]["actual_map"]
        if map_id != None:
            map_data = self.data["mods"][self.actual_mod]["maps"][map_id]
            borders = []
            for y in range( map_data["height"] ):
                for x in range( map_data["width"] ):

                    # Get position
                    xx, yy = int( ( self.xslide + x - y )*TILE_WIDTH/2 ), int( ( self.yslide + x + y )*TILE_HEIGHT/2 )
                    if xx < 0 or yy < -TILE_HEIGHT or xx > size.width+TILE_WIDTH or yy > size.height+TILE_HEIGHT: continue

                    # Background
                    try: tile = int( map_data["background"][y][x] )
                    except: tile = 0
                    if tile and tile in self.data["tiles"][map_data["tileset"]]:
                        self.area_buffer.draw_pixbuf( self.gc, self.data["tiles"][map_data["tileset"]][tile][0], 0, 0,
                            xx-self.data["tiles"][map_data["tileset"]][tile][1], yy-self.data["tiles"][map_data["tileset"]][tile][2], -1, -1, gtk.gdk.RGB_DITHER_NONE, 0, 0)

                    # Collisions
                    try: coll = int( map_data["collision"][y][x] )
                    except: coll = 0

                    # Show positions
                    if self.button_coords.get_active(): borders.append( [coll, xx, yy, str( x ) + "," + str( y ), 0] )

            # Show positions
            for border in borders: show_border( *border )
            borders = []

            # Matrix of map
            for y in range( map_data["height"] ):
                for x in range( map_data["width"] ):

                    # Get position
                    xx, yy = int( ( self.xslide + x - y )*TILE_WIDTH/2 ), int( ( self.yslide + x + y )*TILE_HEIGHT/2 )
                    if xx < 0 or yy < -TILE_HEIGHT or xx > size.width+TILE_WIDTH or yy > size.height+TILE_HEIGHT: continue

                    # Objects (hidden)
                    if not self.button_objs.get_active():
                        try: tile = int( map_data["object"][y][x] )
                        except: tile = 0
                        try: coll = int( map_data["collision"][y][x] )
                        except: coll = 0
                        if self.button_coords.get_active() and tile and tile in self.data["tiles"][map_data["tileset"]]:
                            borders.append( [coll, xx, yy, str( x ) + "," + str( y ) + "\n" + str( tile ), 4] )

                        # Events (hidden)
                        if str( x ) + ";" + str( y ) in map_data["events"].keys():
                            borders.append( [-1, xx, yy, "", 2] )

                    # Objects (showed)
                    else:
                        try: tile = int( map_data["object"][y][x] )
                        except: tile = 0
                        if tile and tile in self.data["tiles"][map_data["tileset"]]:
                            self.area_buffer.draw_pixbuf( self.gc, self.data["tiles"][map_data["tileset"]][tile][0], 0, 0,
                                xx-self.data["tiles"][map_data["tileset"]][tile][1],
                                yy-self.data["tiles"][map_data["tileset"]][tile][2], -1, -1, gtk.gdk.RGB_DITHER_NONE, 0, 0)

                        # Events (showed)
                        if str( x ) + ";" + str( y ) in map_data["events"].keys():
                            events_text = ""
                            for i in range( len( map_data["events"][str( x ) + ";" + str( y )] ) ):
                                events_text += ( map_data["events"][str( x ) + ";" + str( y )][i]["type"] if "type" in map_data["events"][str( x ) + ";" + str( y )][i] else "EVENT" ) + "\n"
                            borders.append( [-1, xx, yy, events_text, 2] )

                    # Units
                    if str( x ) + ";" + str( y ) in map_data["enemies"].keys():
                        try:
                            unit = self.data["units"][map_data["enemies"][str( x ) + ";" + str( y )]["type"]]
                            self.area_buffer.draw_pixbuf( self.gc, self.data["pictures"][unit['cache']], 0, 0,
                                int( xx-self.data["pictures_width"][unit['cache']]/2 ),
                                int( yy-3*self.data["pictures_height"][unit['cache']]/4 ), -1, -1, gtk.gdk.RGB_DITHER_NONE, 0, 0)
                        except: pass

            # Show object positions and other text
            for border in borders: show_border( *border )

        # Refresh screen
        self.area.window.draw_drawable( self.gc, self.area_buffer, 0, 0, 0, 0, -1, -1 )

        # No repeat
        return False


    def key_press_event( self, widget, event, data=None ):
        """
            Handle key press events.

            @param widget: area pyGTK widget object
            @param event: redraw event object
            @param data: additive information (not used)
        """

        # Key press event
        if event.type == gtk.gdk.KEY_PRESS:

            # Set fullscreen
            if event.keyval == 65480:
                self.fullscreen = not self.fullscreen
                self.window.fullscreen() if self.fullscreen else self.window.unfullscreen()
                return True

            # Right
            if event.keyval == 65363:
                self.xslide -= SCROLL_SPEED
                self.area_expose() # Redrawing
                return True

            # Down
            if event.keyval == 65364:
                self.yslide -= SCROLL_SPEED * 2
                self.area_expose() # Redrawing
                return True

            # Left
            if event.keyval == 65361:
                self.xslide += SCROLL_SPEED
                self.area_expose() # Redrawing
                return True

            # Up
            if event.keyval == 65362:
                self.yslide += SCROLL_SPEED * 2
                self.area_expose() # Redrawing
                return True


    def area_motion_event( self, widget, event, data=None ):
        """
            Handle mouse motion event in editor main screen.

            @param widget: area pyGTK widget object
            @param event: redraw event object
            @param data: additive information (not used)
        """

        # Show selection
        if self.button_press != None:

            # Get map coordinates
            map_data = self.data["mods"][self.actual_mod]["maps"][self.data["mods"][self.actual_mod]["actual_map"]]
            diff, x, y = 99999999, 0, 0
            for y in range( map_data["height"] ):
                for x in range( map_data["width"] ):
                    if abs( ( self.xslide + x - y )*TILE_WIDTH/2 - event.x )/TILE_WIDTH*2 + abs( ( self.yslide + x + y )*TILE_HEIGHT/2 - event.y )/TILE_HEIGHT*2 < diff:
                        xpos, ypos, diff = x, y, abs( ( self.xslide + x - y )*TILE_WIDTH/2 - event.x )/TILE_WIDTH*2 + abs( ( self.yslide + x + y )*TILE_HEIGHT/2 - event.y )/TILE_HEIGHT*2

            # Refresh buffer
            size = self.area.allocation
            area_buffer = gtk.gdk.Pixmap( self.window.window, size.width, size.height, depth=-1 )
            area_buffer.draw_drawable( self.gc, self.area_buffer, 0, 0, 0, 0, -1, -1 )
            gc = gtk.gdk.GC( self.window.window ); gc.set_foreground( self.window.window.get_colormap().alloc_color( SELECTION_COLOR ) )

            # Matrix of map
            for y in range( min( self.button_press[1], ypos ), max( self.button_press[1], ypos )+1 ):
                for x in range( min( self.button_press[0], xpos ), max( self.button_press[0], xpos )+1 ):

                    # Get position
                    xx, yy = int( ( self.xslide + x - y )*TILE_WIDTH/2 ), int( ( self.yslide + x + y )*TILE_HEIGHT/2 )
                    if xx < 0 or yy < -TILE_HEIGHT or xx > size.width+TILE_WIDTH or yy > size.height+TILE_HEIGHT: continue

                    # Show markers
                    area_buffer.draw_line( gc, xx-TILE_WIDTH/2+MARKER_BORDER*2+2, yy-1, xx, yy-TILE_HEIGHT/2+MARKER_BORDER )   # Left top
                    area_buffer.draw_line( gc, xx, yy-TILE_HEIGHT/2+MARKER_BORDER, xx+TILE_WIDTH/2-MARKER_BORDER*2-2, yy-1 )   # Right top
                    area_buffer.draw_line( gc, xx-TILE_WIDTH/2+MARKER_BORDER*2+2, yy-1, xx, yy+TILE_HEIGHT/2-MARKER_BORDER-2 ) # Left bottom
                    area_buffer.draw_line( gc, xx, yy+TILE_HEIGHT/2-MARKER_BORDER-2, xx+TILE_WIDTH/2-MARKER_BORDER*2-2, yy-1 ) # Right bottom

            # Refresh screen
            self.area.window.draw_drawable( self.gc, area_buffer, 0, 0, 0, 0, -1, -1 )


    def area_press_event( self, widget, event, data=None ):
        """
            Handle mouse button press event in editor main screen.

            @param widget: area pyGTK widget object
            @param event: redraw event object
            @param data: additive information (not used)
        """

        # Get map coordinates
        map_id = self.data["mods"][self.actual_mod]["actual_map"]
        if map_id != None:
            map_data = self.data["mods"][self.actual_mod]["maps"][map_id]
            diff, x, y = 99999999, 0, 0
            for y in range( map_data["height"] ):
                for x in range( map_data["width"] ):
                    if abs( ( self.xslide + x - y )*TILE_WIDTH/2 - event.x )/TILE_WIDTH*2 + abs( ( self.yslide + x + y )*TILE_HEIGHT/2 - event.y )/TILE_HEIGHT*2 < diff:
                        xpos, ypos, diff = x, y, abs( ( self.xslide + x - y )*TILE_WIDTH/2 - event.x )/TILE_WIDTH*2 + abs( ( self.yslide + x + y )*TILE_HEIGHT/2 - event.y )/TILE_HEIGHT*2
            self.button_press = [xpos, ypos]


    def area_release_event( self, widget, event, data=None ):
        """
            Handle mouse button release event in editor main screen.

            @param widget: area pyGTK widget object
            @param event: redraw event object
            @param data: additive information (not used)
        """

        map_id = self.data["mods"][self.actual_mod]["actual_map"]
        if map_id == None: return False

        # Slide screen with middle button
        size = self.area.allocation
        if event.button == 2 or event.get_state() & gtk.gdk.CONTROL_MASK:
            self.xslide -= int( ( event.x - size.width / 2 ) / ( TILE_WIDTH / 2 ) )
            self.yslide -= int( ( event.y - size.height / 2 ) / ( TILE_HEIGHT / 2 ) )

        # Map data events
        else:

            # Get map coordinates
            map_data = self.data["mods"][self.actual_mod]["maps"][map_id]
            map_data["changed"] = True
            diff, x, y = 99999999, 0, 0
            for y in range( map_data["height"] ):
                for x in range( map_data["width"] ):
                    if abs( ( self.xslide + x - y )*TILE_WIDTH/2 - event.x )/TILE_WIDTH*2 + abs( ( self.yslide + x + y )*TILE_HEIGHT/2 - event.y )/TILE_HEIGHT*2 < diff:
                        xpos, ypos, diff = x, y, abs( ( self.xslide + x - y )*TILE_WIDTH/2 - event.x )/TILE_WIDTH*2 + abs( ( self.yslide + x + y )*TILE_HEIGHT/2 - event.y )/TILE_HEIGHT*2

            # Menu to right button
            if event.button == 3:

                # Dialog window
                dia = gtk.Dialog( "Action", self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
                    ( "Delete ground", 906, "Delete object", 905, "Delete unit", 901, "Delete all", 900, "Start here", 800, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
                dia.connect( "delete_event", lambda w, d: True )

                # Collision editor
                frame = gtk.Frame( "Collision" )
                box = gtk.VBox( False, 2 )
                frame.add( box )
                frame.set_border_width( 2 )
                dia.vbox.pack_start( frame, True, True, 2 )
                tbox = gtk.HBox( True, 2 )
                button = gtk.Button( "Set to _field" )
                button.connect( "clicked", lambda w: dia.response( 910 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Set to _wall" )
                button.connect( "clicked", lambda w: dia.response( 911 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Set to wate_r" )
                button.connect( "clicked", lambda w: dia.response( 912 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Set to _closed" )
                button.connect( "clicked", lambda w: dia.response( 913 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Set to _object" )
                button.connect( "clicked", lambda w: dia.response( 914 ) )
                tbox.pack_start( button, True, True, 2 )
                box.pack_start( tbox, False, False, 2 )

                # Notebook
                notebook = gtk.Notebook()
                notebook.set_tab_pos( gtk.POS_TOP )
                dia.vbox.pack_start( notebook, True, True, 2 )

                # Event editor
                box = gtk.VBox( False, 2 )
                notebook.append_page( box, gtk.Label( " Events of tile " ) )
                event_store = gtk.ListStore( str )
                event_list = gtk.TreeView( event_store )
                event_list.set_size_request( 148, -1 )
                renderer = gtk.CellRendererText()
                column = gtk.TreeViewColumn( 'Event' )
                column.pack_start( renderer, True )
                column.set_attributes( renderer, text=0 )
                event_list.append_column( column )
                event_list.set_headers_visible( False )
                swin = gtk.ScrolledWindow()
                swin.set_policy( gtk.POLICY_NEVER, gtk.POLICY_ALWAYS )
                swin.add( event_list )
                box.set_size_request( -1, 200 )
                box.pack_start( swin, True, True, 2 )
                #event_list.connect( 'row-activated', self.dialog_unit )
                tbox = gtk.HBox( True, 2 )
                button = gtk.Button( "Add event" )
                button.connect( "clicked", lambda w: dia.response( 904 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Edit event" )
                button.connect( "clicked", lambda w: dia.response( 903 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Delete event" )
                button.connect( "clicked", lambda w: dia.response( 902 ) )
                tbox.pack_start( button, True, True, 2 )
                box.pack_start( tbox, False, False, 2 )

                # Fill the event list
                if str( xpos ) + ";" + str( ypos ) in map_data["events"]:
                    for event in map_data["events"][str( xpos ) + ";" + str( ypos )]: event_store.append( [event["type"] if "type" in event else "EVENT"] )
                event_list.set_cursor( 0 )

                # Item editor
                box = gtk.VBox( False, 2 )
                notebook.append_page( box, gtk.Label( " Items " ) )
                item_store = gtk.ListStore( str, str )
                item_list = gtk.TreeView( item_store )
                item_list.set_size_request( 148, -1 )
                renderer = gtk.CellRendererText()
                column = gtk.TreeViewColumn( 'Item' )
                column.pack_start( renderer, True )
                column.set_attributes( renderer, text=0 )
                item_list.append_column( column )
                renderer = gtk.CellRendererText()
                column = gtk.TreeViewColumn( 'Name' )
                column.pack_start( renderer, True )
                column.set_attributes( renderer, text=1 )
                item_list.append_column( column )
                item_list.set_headers_visible( False )
                swin = gtk.ScrolledWindow()
                swin.set_policy( gtk.POLICY_NEVER, gtk.POLICY_ALWAYS )
                swin.add( item_list )
                box.set_size_request( -1, 200 )
                box.pack_start( swin, True, True, 2 )
                #item_list.connect( 'row-activated', self.dialog_unit )
                tbox = gtk.HBox( True, 2 )
                button = gtk.Button( "Add item" )
                button.connect( "clicked", lambda w: dia.response( 924 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Edit item" )
                button.connect( "clicked", lambda w: dia.response( 923 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Delete item" )
                button.connect( "clicked", lambda w: dia.response( 922 ) )
                tbox.pack_start( button, True, True, 2 )
                box.pack_start( tbox, False, False, 2 )

                # Fill the item list
                for item in self.data["mods"][self.actual_mod]["items"]: item_store.append( [item["id"] if "id" in item else "ITEM", item["name"] if "name" in item else "Unnamed"] )
                item_list.set_cursor( 0 )

                # Quest editor
                box = gtk.VBox( False, 2 )
                notebook.append_page( box, gtk.Label( " Quests " ) )
                quest_store = gtk.ListStore( str, str, str )
                quest_list = gtk.TreeView( quest_store )
                quest_list.set_size_request( 148, -1 )
                renderer = gtk.CellRendererText()
                column = gtk.TreeViewColumn( 'Quest' )
                column.pack_start( renderer, True )
                column.set_attributes( renderer, text=0 )
                quest_list.append_column( column )
                quest_list.set_headers_visible( False )
                swin = gtk.ScrolledWindow()
                swin.set_policy( gtk.POLICY_NEVER, gtk.POLICY_ALWAYS )
                swin.add( quest_list )
                box.set_size_request( -1, 200 )
                box.pack_start( swin, True, True, 2 )
                #quest_list.connect( 'row-activated', self.dialog_unit )
                tbox = gtk.HBox( True, 2 )
                button = gtk.Button( "Add quest" )
                button.connect( "clicked", lambda w: dia.response( 934 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Edit quest" )
                button.connect( "clicked", lambda w: dia.response( 933 ) )
                tbox.pack_start( button, True, True, 2 )
                button = gtk.Button( "Delete quest" )
                button.connect( "clicked", lambda w: dia.response( 932 ) )
                tbox.pack_start( button, True, True, 2 )
                box.pack_start( tbox, False, False, 2 )

                # Fill the quest list
                for quest in self.data["mods"][self.actual_mod]["quests"].keys():
                    for i in range( len( self.data["mods"][self.actual_mod]["quests"][quest] ) ):
                        quest_store.append( [self.data["mods"][self.actual_mod]["quests"][quest][i]["quest_text"] if "quest_text" in self.data["mods"][self.actual_mod]["quests"][quest][i] else "QUEST", quest, str( i )] )
                quest_list.set_cursor( 0 )

                # Show and handle result
                dia.show_all()
                result = dia.run()

                for y in range( min( self.button_press[1], ypos ), max( self.button_press[1], ypos )+1 ):
                    for x in range( min( self.button_press[0], xpos ), max( self.button_press[0], xpos )+1 ):

                        # Set collisions
                        if result == 910: map_data["collision"][y][x] = 0
                        if result == 911: map_data["collision"][y][x] = 1
                        if result == 912: map_data["collision"][y][x] = 2
                        if result in ( 900, 913, 906 ): map_data["collision"][y][x] = 3
                        if result == 914: map_data["collision"][y][x] = 4

                        # Delete map elements
                        if result in ( 900, 906 ): map_data["background"][y][x] = 0
                        if result in ( 900, 905 ): map_data["object"][y][x] = 0
                        if result in ( 900, 901 ) and str( x ) + ";" + str( y ) in map_data["enemies"]: del map_data["enemies"][str( x ) + ";" + str( ypos )]

                        # Delete events, items, quests
                        if result in ( 900, 902 ) and str( x ) + ";" + str( y ) in map_data["events"] and event_list.get_selection().get_selected_rows()[1]:
                            path, column = event_list.get_cursor()
                            if column: del map_data["events"][str( x ) + ";" + str( y )][path[0]]
                        if result == 922 and item_list.get_selection().get_selected_rows()[1]:
                            path, column = item_list.get_cursor()
                            if column: del self.data["mods"][self.actual_mod]["items"][path[0]]
                        if result == 932 and quest_list.get_selection().get_selected_rows()[1]:
                            path, column = quest_list.get_cursor()
                            if column: del self.data["mods"][self.actual_mod]["quests"][quest_store[path[0]][1]][int( quest_store[path[0]][2] )]

                # New start position
                if result == 800:
                    open( WORK_DIR + "mods/" + self.data["mods"][self.actual_mod]["name"] + "/maps/spawn.txt", 'w' ).write( """
# this file is automatically loaded when a New Game starts.
# it's a dummy map to send the player to the actual starting point.

[header]
width=1
height=1
location=0,0,3

[event]
type=teleport
location=0,0,1,1
intermap=""" + str( self.data["mods"][self.actual_mod]["maps"][self.data["mods"][self.actual_mod]["actual_map"]]["name"] ) + "," + str( xpos ) + "," + str( ypos ) + "\n" )

                # Add or edit events
                elif result in ( 903, 904 ):

                    # Create event data
                    column = False
                    if str( xpos ) + ";" + str( ypos ) in map_data["events"] and event_list.get_selection().get_selected_rows()[1] and result == 903:
                        path, column = event_list.get_cursor()
                        if column: item = map_data["events"][str( xpos ) + ";" + str( ypos )][path[0]].copy()
                    else: item = { "type": "teleport", "location": str( min( self.button_press[0], xpos ) ) + "," + str( min( self.button_press[1], ypos ) ) + "," + str( max( self.button_press[0], xpos ) - min( self.button_press[0], xpos ) + 1 ) + "," + str( max( self.button_press[1], ypos ) - min( self.button_press[1], ypos ) + 1 ) }
                    for x in self.text_cache["event"]:
                        if x not in item: item[x] = ""

                    # Dialog window
                    dia.destroy()
                    dia = gtk.Dialog( "Event", self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR, ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
                    dia.connect( "delete_event", lambda w, d: True )

                    # Data
                    box = gtk.HBox( True, 2 )
                    box1 = gtk.VBox( False, 2 )
                    entry = {}
                    line = 0
                    for x in sorted( item.keys() ):
                        line += 1
                        box2 = gtk.HBox( False, 2 )
                        box2.pack_start( gtk.Label( x + ":" ), False, False, 2 )
                        clist = gtk.combo_box_entry_new_text()
                        entry[x] = clist.child
                        if "event_" + x in self.text_cache:
                            for i in self.text_cache["event_" + x]: clist.append_text( i )
                        entry[x].set_text( item[x] )
                        box2.pack_start( clist, True, True, 2 )
                        box1.pack_start( box2, False, False, 2 )
                        if not line % 10:
                            box.pack_start( box1, False, False, 2 )
                            box1 = gtk.VBox( False, 2 )
                    if line % 10: box.pack_start( box1, False, False, 2 )
                    dia.vbox.pack_start( box, False, False, 2 )

                    # Show and handle result
                    dia.show_all()
                    result = dia.run()
                    if result == gtk.RESPONSE_OK:
                        if column: del map_data["events"][str( xpos ) + ";" + str( ypos )][path[0]]
                        for e in entry.keys():
                            if entry[e].get_text(): item[e] = entry[e].get_text()
                            else: del item[e]
                        try:
                            if ";".join( item["location"].split( "," )[:2] ) not in map_data["events"]: map_data["events"][";".join( item["location"].split( "," )[:2] )] = []
                            map_data["events"][";".join( item["location"].split( "," )[:2] )].append( item )
                        except Exception, E: print( str( E ) )

                # Add or edit item
                elif result in ( 923, 924 ):

                    # Create item data
                    column = False
                    if item_list.get_selection().get_selected_rows()[1] and result == 923:
                        path, column = item_list.get_cursor()
                        if column: item = self.data["mods"][self.actual_mod]["items"][path[0]].copy()
                    else: item = {}
                    for x in self.text_cache["item"]:
                        if x not in item: item[x] = ""

                    # Dialog window
                    dia.destroy()
                    dia = gtk.Dialog( "Item", self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR, ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
                    dia.connect( "delete_event", lambda w, d: True )

                    # Data
                    box = gtk.HBox( True, 2 )
                    box1 = gtk.VBox( False, 2 )
                    entry = {}
                    line = 0
                    for x in sorted( item.keys() ):
                        line += 1
                        box2 = gtk.HBox( False, 2 )
                        box2.pack_start( gtk.Label( x + ":" ), False, False, 2 )
                        clist = gtk.combo_box_entry_new_text()
                        entry[x] = clist.child
                        if "item_" + x in self.text_cache:
                            for i in self.text_cache["item_" + x]: clist.append_text( i )
                        entry[x].set_text( item[x] )
                        box2.pack_start( clist, True, True, 2 )
                        box1.pack_start( box2, False, False, 2 )
                        if not line % 10:
                            box.pack_start( box1, False, False, 2 )
                            box1 = gtk.VBox( False, 2 )
                    if line % 10: box.pack_start( box1, False, False, 2 )
                    dia.vbox.pack_start( box, False, False, 2 )

                    # Show and handle result
                    dia.show_all()
                    result = dia.run()
                    if result == gtk.RESPONSE_OK:
                        if column: del self.data["mods"][self.actual_mod]["items"][path[0]]
                        for e in entry.keys():
                            if entry[e].get_text(): item[e] = entry[e].get_text()
                        try: self.data["mods"][self.actual_mod]["items"].append( item )
                        except Exception, E: print( str( E ) )

                # Add or edit quest
                elif result in ( 933, 934 ):

                    # Create quest data
                    column = False
                    if quest_list.get_selection().get_selected_rows()[1] and result == 933:
                        path, column = quest_list.get_cursor()
                        if column: item = self.data["mods"][self.actual_mod]["quests"][quest_store[path[0]][1]][int( quest_store[path[0]][2] )].copy()
                    else: item = {}
                    for x in self.text_cache["quest"]:
                        if x not in item: item[x] = ""

                    # Dialog window
                    dia.destroy()
                    dia = gtk.Dialog( "Quest", self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR, ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
                    dia.connect( "delete_event", lambda w, d: True )

                    # Data
                    box = gtk.HBox( True, 2 )
                    box1 = gtk.VBox( False, 2 )
                    entry = {}
                    line = 0
                    for x in sorted( item.keys() ):
                        line += 1
                        box2 = gtk.HBox( False, 2 )
                        box2.pack_start( gtk.Label( x + ":" ), False, False, 2 )
                        clist = gtk.combo_box_entry_new_text()
                        entry[x] = clist.child
                        if "quest_" + self.data["mods"][self.actual_mod]["name"] + "_" + x in self.text_cache:
                            for i in self.text_cache["quest_" + self.data["mods"][self.actual_mod]["name"] + "_" + x]: clist.append_text( i )
                        entry[x].set_text( item[x] )
                        box2.pack_start( clist, True, True, 2 )
                        box1.pack_start( box2, False, False, 2 )
                        if not line % 10:
                            box.pack_start( box1, False, False, 2 )
                            box1 = gtk.VBox( False, 2 )
                    if line % 10: box.pack_start( box1, False, False, 2 )
                    dia.vbox.pack_start( box, False, False, 2 )

                    # Show and handle result
                    dia.show_all()
                    result = dia.run()
                    if result == gtk.RESPONSE_OK:
                        if column: del self.data["mods"][self.actual_mod]["quests"][quest_store[path[0]][1]][int( quest_store[path[0]][2] )]
                        for e in entry.keys():
                            if entry[e].get_text(): item[e] = entry[e].get_text()
                        try: self.data["mods"][self.actual_mod]["quests"][quest_store[path[0]][1]].append( item )
                        except Exception, E: print( str( E ) )

                dia.destroy()

            # Put elements to map with left button
            else:

                # Put enemy
                if self.button_un.get_active():
                    for y in range( min( self.button_press[1], ypos ), max( self.button_press[1], ypos )+1 ):
                        for x in range( min( self.button_press[0], xpos ), max( self.button_press[0], xpos )+1 ):
                            map_data["enemies"][str( x ) + ";" + str( y )] = {}
                            map_data["enemies"][str( x ) + ";" + str( y )]["type"] = self.unit_store[self.unit_list.get_cursor()[0][0]][1]
                            map_data["enemies"][str( x ) + ";" + str( y )]["location"] = str( x ) + "," + str( y ) + ",0"

                # Put ground or object
                else:
                    tiles = [path[0] for path in self.tile_list.get_selection().get_selected_rows()[1]]

                    for y in range( min( self.button_press[1], ypos ), max( self.button_press[1], ypos )+1 ):
                        for x in range( min( self.button_press[0], xpos ), max( self.button_press[0], xpos )+1 ):
                            try:
                                map_data["object" if self.button_ob.get_active() else "background"][y][x] = self.tile_store[tiles[( random.randint( 1, len( tiles ) ) if self.button_rnd.get_active() else y*3+x ) % len( tiles )]][1]
                                coll = self.data["tiles"][map_data["tileset"]][int( map_data["object" if self.button_ob.get_active() else "background"][y][x] )][3]
                                map_data["collision"][y][x] = coll if coll != -1 else 0
                            except Exception, E: print E

        # Dismiss selection
        self.button_press = None

        # Redrawing
        self.area_expose()
        return False


    def change_type( self, widget=None ):
        """
            Change type.

            @param widget: pyGTK widget object
        """

        # List switching
        if self.button_un.get_active(): self.tile_frame.hide(); self.unit_frame.show()
        else: self.tile_frame.show(); self.unit_frame.hide()


    def dialog_box( self, widget, text, title="Information", buttons=( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE ) ):
        """
            General dialog window.

            @param widget: parent pyGTK widget
            @param text: showed text
            @param title: window title
            @param buttons: buttons map
        """

        # Dialog window
        dia = gtk.Dialog( title, self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR, buttons )
        dia.set_position( gtk.WIN_POS_CENTER_ALWAYS )
        dia.connect( "delete_event", lambda w, d: True )
        image = gtk.Image()
        image.set_from_file( self.logofile )
        dia.vbox.pack_start( image, False, False )
        dia.vbox.pack_start( gtk.Label( text ), False, False, 10 )
        dia.show_all()

        # Show and handle result
        result = dia.run()
        dia.destroy()
        if result == gtk.RESPONSE_CLOSE or buttons == ( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE ): return False
        return True


    def level_save( self, widget=None ):

        # Create directories
        for filename in ( "", "enemies", "images", "items", "languages", "maps", "npcs", "quests" ):
            if not os.path.exists( WORK_DIR + "mods/" + self.data["mods"][self.actual_mod]["name"] + "/" + filename ):
                os.makedirs( WORK_DIR + "mods/" + self.data["mods"][self.actual_mod]["name"] + "/" + filename )

        # Save changed maps of mod
        pot = []
        for actual_map in self.data["mods"][self.actual_mod]["maps"]:
            if actual_map["name"] == "spawn.txt": continue
            print( "Check map: " + actual_map["name"] + " ..." )

            # Header
            data = "[header]\n"
            if "width" in actual_map: data += "width=" + str( actual_map["width"] ) + "\n"
            if "height" in actual_map: data += "height=" + str( actual_map["height"] ) + "\n"
            if "music" in actual_map: data += "music=" + str( actual_map["music"] ) + "\n"
            if "tileset" in actual_map: data += "tileset=" + str( actual_map["tileset"] ) + "\n"
            if "title" in actual_map:
                data += "title=" + str( actual_map["title"] ) + "\n"
                if actual_map["title"] not in pot: pot.append( actual_map["title"] )

            # Background
            data += "\n[layer]\ntype=background\ndata=\n"
            for y in actual_map["background"][:-1]: data += "".join( [str( x ) + "," for x in y] ) + "\n"
            data += ",".join( [str( x ) for x in actual_map["background"][-1]] ) + "\n"

            # Objects
            data += "\n[layer]\ntype=object\ndata=\n"
            for y in actual_map["object"][:-1]: data += "".join( [str( x ) + "," for x in y] ) + "\n"
            data += ",".join( [str( x ) for x in actual_map["object"][-1]] ) + "\n"

            # Collisions
            data += "\n[layer]\ntype=collision\ndata=\n"
            for y in actual_map["collision"][:-1]: data += "".join( [str( x ) + "," for x in y] ) + "\n"
            data += ",".join( [str( x ) for x in actual_map["collision"][-1]] ) + "\n"

            # Store enemies
            for x in actual_map["enemies"].keys():
                data += "\n[enemy]\n"
                for i in actual_map["enemies"][x].keys():
                    data += i + "=" + actual_map["enemies"][x][i] + "\n"
                    if i == "name" and actual_map["enemies"][x][i] not in pot: pot.append( actual_map["enemies"][x][i] )

            # Store events
            for x in actual_map["events"]:
                for ev in actual_map["events"][x]:
                    data += "\n[event]\n"
                    for i in ev.keys():
                        if ev[i]:
                            data += i + "=" + ev[i] + "\n"
                            if i in ( "msg", "tooltip" ) and ev[i] not in pot: pot.append( ev[i] )

            # Create file
            if not actual_map["changed"]: continue
            print( "Save map: " + actual_map["name"] + " ..." )
            f = open( WORK_DIR + actual_map["file"], 'w' )
            f.write( data + "\n" )
            f.close()
            actual_map["dir"] = WORK_DIR
            actual_map["changed"] = False

        # Create POT file
        f = open( WORK_DIR + "mods/" + self.data["mods"][self.actual_mod]["name"] + "/languages/data.pot", 'w' )
        f.write( """msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2012-05-13 23:40+\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
""" )
        for x in pot: f.write( '\nmsgid "' + x.replace( '"', '\\"' ) + '"\nmsgstr ""\n' )
        f.close()


    def change_mod( self, widget=None ):

        # Set actual map
        self.level_list.disconnect( self.level_reload )
        self.actual_mod = [x["name"] for x in self.data["mods"]].index( self.mod_list.get_model()[self.mod_list.get_active()][0] )
        self.level_list.get_model().clear()
        for x in self.data["mods"][self.actual_mod]["maps"]: self.level_list.append_text( x["name"] )
        self.level_reload = self.level_list.connect( 'changed', self.change_level )
        self.level_list.set_active( self.data["mods"][self.actual_mod]["actual_map"] if self.data["mods"][self.actual_mod]["actual_map"] != None else 0 )


    def change_level( self, widget=None, preload=None ):

        # Set actual map
        if preload != None: self.data["mods"][self.actual_mod]["actual_map"] = preload
        elif widget:
            if widget.get_active() == -1:
                self.data["mods"][self.actual_mod]["actual_map"] = None
                self.area_expose()
                return
            self.window.set_sensitive( False )
            self.data["mods"][self.actual_mod]["actual_map"] = [x["name"] for x in self.data["mods"][self.actual_mod]["maps"]].index( widget.get_model()[widget.get_active()][0] )

        # Check state
        map_data = self.data["mods"][self.actual_mod]["maps"][self.data["mods"][self.actual_mod]["actual_map"]]
        if not map_data["background"]:

            # Load the file up
            if preload == None: print( "Change map: " + map_data["name"] + " ..." )
            section, layer = 0, "background"
            enemies, events = [], []
            for line in [x.strip() for x in open( map_data["dir"] + map_data["file"], 'r' ).readlines() if x.strip() and x[:1] != "#"]:
                if line == "[header]": section = 1
                elif line == "[enemy]": section = 2; enemies.append( {} )
                elif line == "[event]": section = 3; events.append( {} )
                elif line == "[layer]": section = 4
                elif line[:1] == "[": section = 0
                elif section == 1 and "=" in line: map_data[line.split( "=", 1 )[0]] = int( line.split( "=", 1 )[1] ) if line.split( "=", 1 )[0] in ( "width", "height" ) else line.split( "=", 1 )[1]
                elif section == 4 and line[:5] == "type=": layer = line[5:]; map_data[layer] = []
                elif section == 4 and "=" not in line and "," in line: map_data[layer].append( [int( x ) for x in line.split( "," ) if x != ""] )
                elif section == 2 and "=" in line: enemies[-1][line.split( "=", 1 )[0]] = line.split( "=", 1 )[1]
                elif section == 3 and "=" in line:
                    if line.split( "=", 1 )[0] == "loot" and line.split( "=", 1 )[1] not in self.text_cache["event_loot"]:
                        self.text_cache["event_loot"].append( line.split( "=", 1 )[1] )
                    events[-1][line.split( "=", 1 )[0]] = line.split( "=", 1 )[1]

            # Store enemies
            map_data["enemies"] = {}
            for x in enemies:
                try: map_data["enemies"][";".join( x["location" if "location" in x else "spawnpoint"].split( "," )[:2] )] = x
                except Exception, E: print( "Exception: " + str( E ) )

            # Store events
            map_data["events"] = {}
            for x in events:
                try:
                    if ";".join( x["location"].split( "," )[:2] ) not in map_data["events"]: map_data["events"][";".join( x["location"].split( "," )[:2] )] = []
                    map_data["events"][";".join( x["location"].split( "," )[:2] )].append( x )
                    for field in x.keys():
                        if field not in self.text_cache["event"]: self.text_cache["event"].append( field )
                        if "event_" + field not in self.text_cache: self.text_cache["event_" + field] = []
                        if x[field] not in self.text_cache["event_" + field]: self.text_cache["event_" + field].append( x[field] )
                except Exception, E: print( "Exception: " + str( E ) )

            # Prestore collision
            for y in range( map_data["height"] ):
                for x in range( map_data["width"] ):
                    try: tile = int( map_data["background"][y][x] )
                    except: tile = -1
                    if tile and tile in self.data["tiles"][map_data["tileset"]]:
                        try: self.data["tiles"][map_data["tileset"]][tile][3] = int( map_data["collision"][y][x] )
                        except: pass
                    try: tile = int( map_data["object"][y][x] )
                    except: tile = -1
                    if tile and tile in self.data["tiles"][map_data["tileset"]]:
                        try: self.data["tiles"][map_data["tileset"]][tile][3] = int( map_data["collision"][y][x] )
                        except: pass

        if preload == None:

            # Show tile images
            self.tile_store.clear()
            for tile in self.data["tiles"][map_data["tileset"]].keys(): self.tile_store.append( [ self.data["tiles"][map_data["tileset"]][tile][0], tile ] )
            self.tile_list.set_cursor( 0 )

            # Reset enemies
            self.unit_list.set_cursor( 0 )

            # Redraw area
            self.xslide, self.yslide = int( self.area_size[0]/TILE_WIDTH - map_data["width"]/2 + map_data["height"]/2 ), int( self.area_size[1]/TILE_HEIGHT - map_data["width"]/2 - map_data["height"]/2 )
            self.area_expose()
            self.window.set_sensitive( True )


    def level_create( self, widget=None ):

        # Prepare data files
        level_data = { "name": "unknown", "dir": WORK_DIR, "spawnpoint": [ 8, 8, 7 ], "width": 16, "height": 16, "music": "music/overworld_theme.ogg", "tileset": self.default_tileset, "title": "Unknown", "enemies": {}, "events": {} }
        quest_data = { "name": "unnamed", "actual_map": 0, "maps": [], "items": [], "quests": {} }

        # Dialog window
        dia = gtk.Dialog( "New", self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR, ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
        dia.connect( "delete_event", lambda w, d: True )

        # Mod code
        box2 = gtk.HBox( False, 4 )
        box2.pack_start( gtk.Label( "Mod (code):" ), False, False, 4 )
        entry_mod = gtk.Entry()
        entry_mod.set_text( self.data["mods"][self.actual_mod]["name"] )
        box2.pack_start( entry_mod, True, True, 4 )
        dia.vbox.pack_start( box2, False, False, 4 )

        # Level code
        box2 = gtk.HBox( False, 4 )
        box2.pack_start( gtk.Label( "Level (code):" ), False, False, 4 )
        entry_name = gtk.Entry()
        entry_name.set_text( level_data["name"] )
        box2.pack_start( entry_name, True, True, 4 )
        dia.vbox.pack_start( box2, False, False, 4 )

        # Title
        box2 = gtk.HBox( False, 4 )
        box2.pack_start( gtk.Label( "Title:" ), False, False, 4 )
        entry_title = gtk.Entry()
        entry_title.set_text( level_data["title"] )
        box2.pack_start( entry_title, True, True, 4 )
        dia.vbox.pack_start( box2, False, False, 4 )

        # Width
        box2 = gtk.HBox( False, 4 )
        box2.pack_start( gtk.Label( "Width:" ), False, False, 4 )
        entry_width = gtk.Entry()
        entry_width.set_text( str( level_data["width"] ) )
        box2.pack_start( entry_width, True, True, 4 )
        dia.vbox.pack_start( box2, False, False, 4 )

        # Height
        box2 = gtk.HBox( False, 4 )
        box2.pack_start( gtk.Label( "Height:" ), False, False, 4 )
        entry_height = gtk.Entry()
        entry_height.set_text( str( level_data["height"] ) )
        box2.pack_start( entry_height, True, True, 4 )
        dia.vbox.pack_start( box2, False, False, 4 )

        # Music
        box2 = gtk.HBox( False, 4 )
        box2.pack_start( gtk.Label( "Music:" ), False, False, 4 )
        list_music = gtk.combo_box_new_text()
        for mod in self.data["mods"]:
            if os.path.isdir( WORK_DIR + "mods/" + mod["name"] + "/music" ):
                for x in [f for f in os.listdir( WORK_DIR + "mods/" + mod["name"] + "/music" ) if f.split( "." )[-1] == "ogg"]: list_music.append_text( "music/" + x )
        for x in range( len( list_music.get_model() ) ):
            if list_music.get_model()[x][0] == level_data["music"]: list_music.set_active( x )
        box2.pack_start( list_music, True, True, 4 )
        dia.vbox.pack_start( box2, False, False, 4 )

        # Tileset
        box2 = gtk.HBox( False, 4 )
        box2.pack_start( gtk.Label( "Tileset:" ), False, False, 4 )
        list_tiles = gtk.combo_box_new_text()
        for mod in self.data["mods"]:
            if os.path.isdir( WORK_DIR + "mods/" + mod["name"] + "/tilesetdefs" ):
                for x in [f for f in os.listdir( WORK_DIR + "mods/" + mod["name"] + "/tilesetdefs" ) if f.split( "." )[-1] == "txt"]: list_tiles.append_text( "tilesetdefs/" + x )
        for x in range( len( list_tiles.get_model() ) ):
            if list_tiles.get_model()[x][0] == level_data["tileset"]: list_tiles.set_active( x )
        box2.pack_start( list_tiles, True, True, 4 )
        dia.vbox.pack_start( box2, False, False, 4 )

        # Show and handle result
        dia.show_all()
        result = dia.run()
        if result == gtk.RESPONSE_OK:
            quest_data["name"] = entry_mod.get_text()
            level_data["name"] = entry_name.get_text()
            #level_data["file"] = entry_name.get_text()
            level_data["title"] = entry_title.get_text()
            level_data["width"] = int( entry_width.get_text() )
            level_data["height"] = int( entry_height.get_text() )
            level_data["music"] = list_music.get_model()[list_music.get_active()][0]
            level_data["tileset"] = list_tiles.get_model()[list_tiles.get_active()][0]
            level_data["background"] = [[16 + (x - y * 3) % 16 for x in range( level_data["width"] )] for y in range( level_data["height"] )]
            level_data["object"] = [[0 for x in range( level_data["width"] )] for y in range( level_data["height"] )]
            level_data["collision"] = [[0 for x in range( level_data["width"] )] for y in range( level_data["height"] )]
            level_data["changed"] = True
            level_data["readonly"] = False
            level_data["file"] = WORK_DIR + "mods/" + quest_data["name"] + "/maps/" + level_data["name"] + ".txt"

            # Create mod, if not exists
            if quest_data["name"] not in [x["name"] for x in self.data["mods"]]:
                if not os.path.exists( WORK_DIR + "mods/" + quest_data["name"] ): os.makedirs( WORK_DIR + "mods/" + quest_data["name"] )
                for filename in ( "enemies", "images", "items", "languages", "maps", "npcs", "quests" ):
                    if not os.path.exists( WORK_DIR + "mods/" + quest_data["name"] + "/" + filename ): os.makedirs( WORK_DIR + "mods/" + quest_data["name"] + "/" + filename )
                self.data["mods"].append( quest_data )
                open( WORK_DIR + "mods/mods.txt", 'a' ).write( "\n" + quest_data["name"] + "\n" )
                self.mod_list.append_text( quest_data["name"] )

            # Change cache
            self.text_cache["event_intermap"].append( level_data["name"] + ",{x},{y}")

            # Select level
            mod = [x["name"] for x in self.data["mods"]].index( quest_data["name"] )
            self.data["mods"][mod]["maps"].append( level_data )
            self.level_list.append_text( level_data["name"] )
            for x in range( len( self.level_list.get_model() ) ):
                if self.level_list.get_model()[x][0] == level_data["name"]:
                    self.data["mods"][mod]["actual_map"] = x
                    break
            for x in range( len( self.mod_list.get_model() ) ):
                if self.mod_list.get_model()[x][0] == quest_data["name"]:
                    self.mod_list.set_active( x )
                    break
            self.change_mod()
            self.level_save()

        # Close window
        dia.destroy()


    def dialog_unit( self, treeview, path=None, view_column=None ):

        # Get selected
        path, column = treeview.get_cursor()
        if not column: return
        unit = self.unit_store[path[0]][1]

        # Dialog window
        dia = gtk.Dialog( "Unit", self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
            ( "Copy as new", 999, gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) if self.data["units"][unit]["readonly"]
            else ( "Delete", 998, "Copy as new", 999, gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )
        dia.connect( "delete_event", lambda w, d: True )

        # Data
        box = gtk.HBox( True, 2 )
        box1 = gtk.VBox( True, 2 )
        entry = {}
        line = 0
        event = self.data["units"][unit].copy()
        for x in self.text_cache["unit"]:
            if x not in event: event[x] = ""
        for x in event:
            if x in ( "readonly", "file", "quest" ): continue
            line += 1
            box2 = gtk.HBox( False, 2 )
            box2.pack_start( gtk.Label( x + ":" ), False, False, 2 )
            entry[x] = gtk.Entry()
            entry[x].set_text( event[x] )
            if self.data["units"][unit]["readonly"]: entry[x].set_sensitive( False )
            box2.pack_start( entry[x], True, True, 2 )
            box1.pack_start( box2, False, False, 2 )
            if not line % int( ( len( event ) + 2 ) / 3 ):
                box.pack_start( box1, False, False, 2 )
                box1 = gtk.VBox( True, 2 )
        if line % int( ( len( event ) + 2 ) / 3 ): box.pack_start( box1, False, False, 2 )
        dia.vbox.pack_start( box, False, False, 2 )

        # Name of copy
        dia.vbox.pack_start( gtk.HSeparator(), True, True, 2 )
        box2 = gtk.HBox( False, 2 )
        box2.pack_start( gtk.Label( "Name of copy:" ), False, False, 2 )
        name = gtk.Entry()
        name.set_text( "copy_of_" + unit )
        box2.pack_start( name, True, True, 2 )
        dia.vbox.pack_start( box2, False, False, 2 )

        # Show and handle result
        dia.show_all()
        result = dia.run()
        if result == gtk.RESPONSE_OK:
            for x in entry.keys():
                if entry[x].get_text() or x in self.data["units"][unit]: self.data["units"][unit][x] = entry[x].get_text()
        if result == 999:
            self.data["units"][name.get_text()] = {}
            for x in self.data["units"][unit].keys(): self.data["units"][name.get_text()][x] = self.data["units"][unit][x]
            self.data["units"][name.get_text()]["readonly"] = False
            self.unit_store.append( [self.data["pictures"][self.data["units"][name.get_text()]['cache']], name.get_text()] )
        if result == 998:
            del self.data["units"][unit]

        dia.destroy()


    def delete_event( self, widget, event=None ):
        return self.dialog_box( widget, "Quest Editor\n \nAre you sure to quit?", "Exit", ( gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL ) )


    def destroy_event( self, widget ):
        if not self.delete_event( widget ):
            gtk.main_quit()


    def __init__( self ):
        """
            Initialize editor object.
        """

        # Main variable
        self.area_buffer = None
        self.area_bg_buffer = None
        self.area_size = [ DEF_X_SIZE-2, DEF_Y_SIZE-2 ]
        self.gc = None
        self.xslide, self.yslide = 9, 1
        self.button_press = None
        self.text_cache = { "unit": [], "quest": [], "item": [], "event": [] }
        self.text_cache["event_loot"] = ['id,,,', 'random,,,']
        self.fullscreen = False

        # Status window
        dia = gtk.Dialog( "Event", None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR, () )
        dia.connect( "delete_event", lambda w, d: True )
        dia.set_position( gtk.WIN_POS_CENTER_ALWAYS )
        dia.set_size_request( 480, -1 )
        dia.set_sensitive( False )
        dia.set_decorated( False )
        dia.set_resizable( False )
        dia.set_border_width( 10 )
        pb = gtk.ProgressBar()
        dia.vbox.pack_start( gtk.Label( "Loading..." ), True, True, 2 )
        dia.vbox.pack_start( pb, True, True, 2 )
        dia.show_all()
        while gtk.events_pending(): gtk.main_iteration( False )

        # Prepare data files
        self.data = { "changed": False, "tiles": {}, "pictures": {}, "pictures_width": {}, "pictures_height": {}, "units": {}, "mods": [] }
        maps = []
        for quest in [x.strip() for x in open( WORK_DIR + "mods/mods.txt", 'r' ).readlines() if x[:1] != "#" and x.strip()]:
            #if quest != "fantasycore":
            if quest not in [x["name"] for x in self.data["mods"]]: self.data["mods"].append( { "name": quest, "actual_map": 0, "maps": [], "items": [], "quests": {} } )
        print( "Found mods: %s" % str( [x["name"] for x in reversed( self.data["mods"] )] ) )

        # Find game icon
        for x in reversed( self.data["mods"] ):
            modname = x["name"]
            if os.path.isfile( FLARE_DIR + "mods/" + modname + "/images/logo/icon.png" ):
                self.logofile = FLARE_DIR + "mods/" + modname + "/images/logo/icon.png"
                break

        # Read TILESET data
        for quest in [x["name"] for x in reversed( self.data["mods"] )]:
            if os.path.isdir( WORK_DIR + "mods/" + quest + "/tilesetdefs" ):
                print( "(%s) Load tile set..." % quest )
                for tileset in [f for f in os.listdir( WORK_DIR + "mods/" + quest + "/tilesetdefs" ) if f.split( "." )[-1] == "txt"]:
                    if tileset in self.data["tiles"]:
                        print( "(%s)  ... %s (already stored)" % ( quest, tileset ) )
                        continue
                    print( "(%s) ... %s" % ( quest, tileset ) )
                    pb.pulse()
                    pb.set_text( "Load tileset: %s ..." % tileset )
                    while gtk.events_pending(): gtk.main_iteration( False )
                    filedata = open( WORK_DIR + "mods/" + quest + "/tilesetdefs/" + tileset, 'r' ).readlines()
                    pixbuf = None
                    for quest2 in [x["name"] for x in reversed( self.data["mods"] )]:
                        if os.path.isfile( WORK_DIR + "mods/" + quest2 + "/" + [x.rstrip()[4:] for x in filedata if x[:4] == "img="][0] ):
                            pixbuf = gtk.gdk.pixbuf_new_from_file( WORK_DIR + "mods/" + quest2 + "/" + [x.rstrip()[4:] for x in filedata if x[:4] == "img="][0] )
                            break
                    if not pixbuf:
                        print( "ERROR: Missing image file (SKIP)" )
                        continue
                    tileset = "tilesetdefs/" + tileset
                    self.data["tiles"][tileset] = {}
                    if not pixbuf.get_has_alpha(): pixbuf = pixbuf.add_alpha( True, 255, 0, 255 )
                    self.data["tiles"][tileset][0] = [ gtk.gdk.pixbuf_new_from_file( self.logofile ), 0, 0, 3 ]
                    for tile in [x.rstrip()[5:].split(",") for x in filedata if x[:5] == "tile="]:
                        self.data["tiles"][tileset][int( tile[0] )] = [ pixbuf.subpixbuf( int( tile[1] ), int( tile[2] ), int( tile[3] ), int( tile[4] ) ), int( tile[5] ), int( tile[6] ), -1 ]

        for x in self.data["tiles"]:
            self.default_tileset = x
            break

        for x in self.data["mods"]:
            self.default_mod = x["name"]
            break

        # Load ENEMIES
        for quest in [x["name"] for x in reversed( self.data["mods"] )]:
            if os.path.isdir( WORK_DIR + "mods/" + quest + "/enemies" ):
                print( "(%s)  Load enemies..." % quest )
                for unit in [f[:-4] for f in os.listdir( WORK_DIR + "mods/" + quest + "/enemies" ) if f.split( "." )[-1] == "txt"]:
                    if unit in self.data["units"]:
                        print( "(%s) ... %s (already stored)" % ( quest, enemy['cache'] ) )
                        continue
                    pb.set_text( "Load unit: %s ..." % unit )
                    pb.pulse()
                    while gtk.events_pending(): gtk.main_iteration( False )
                    enemy = { "readonly": quest == self.default_mod, "file": "mods/" + quest + "/enemies/" + unit + ".txt", "quest": quest, "cache": quest + "." + unit, "level": "?", "hp": "?" }
                    for line in [x.strip() for x in open( WORK_DIR + enemy["file"], 'r' ).readlines() if x.strip() and x[:1] != "#"]:
                        if "=" in line: enemy[line.split( "=", 1 )[0]] = line.split( "=", 1 )[1]
                    if enemy['cache'] not in self.data["pictures"]:
                        if os.path.exists( WORK_DIR + ".cache/" + enemy['cache'] + ".png" ):
                            print( "(%s) ... %s (already cached)" % ( quest, enemy['cache'] ) )
                            self.data["pictures"][enemy['cache']] = gtk.gdk.pixbuf_new_from_file( WORK_DIR + ".cache/" + enemy['cache'] + ".png" )
                            self.data["pictures_width"][enemy['cache']] = self.data["pictures"][enemy['cache']].get_width()
                            self.data["pictures_height"][enemy['cache']] = self.data["pictures"][enemy['cache']].get_height()
                        else:
                            print( "(%s) ... %s" % ( quest, enemy['cache'] ) )
                            anim_data = {}
                            for quest2 in [x["name"] for x in reversed( self.data["mods"] )]:
                                if os.path.isfile( WORK_DIR + "mods/" + quest2 + "/" + enemy['animations'] ):
                                    for line in [x.strip() for x in open( WORK_DIR + "mods/" + quest2 + "/" + enemy['animations'], 'r' ).readlines() if x.strip() and x[:1] != "#"]:
                                        if "=" in line and line.split( "=", 1 )[0] not in anim_data: anim_data[line.split( "=", 1 )[0]] = line.split( "=", 1 )[1]
                                    break
                            if not anim_data:
                                print( "ERROR: Missing amination file (SKIP)" )
                                continue
                            pic = None
                            for quest2 in [x["name"] for x in reversed( self.data["mods"] )]:
                                if os.path.isfile( WORK_DIR + "mods/" + quest2 + "/" + anim_data['image'] ):
                                    pic = gtk.gdk.pixbuf_new_from_file( WORK_DIR + "mods/" + quest2 + "/" + anim_data['image'] )
                                    break
                            if not pic:
                                print( "ERROR: Missing image file (SKIP)" )
                                continue
                            self.data["pictures_width"][enemy['cache']] = int( anim_data["frame"].split( "," )[4] )
                            self.data["pictures_height"][enemy['cache']] = int( anim_data["frame"].split( "," )[5] )
                            pic = pic.subpixbuf( int( anim_data["frame"].split( "," )[2] ), int( anim_data["frame"].split( "," )[3] ),
                                self.data["pictures_width"][enemy['cache']], self.data["pictures_height"][enemy['cache']] )
                            pixmap, dummy = pic.render_pixmap_and_mask()
                            gc = pixmap.new_gc(); gc.set_foreground( pixmap.get_colormap().alloc_color( TEXT_COLOR ) )
                            gcs = pixmap.new_gc(); gcs.set_foreground( pixmap.get_colormap().alloc_color( SHADOW_COLOR ) )
                            gcb = pixmap.new_gc(); gcb.set_foreground( pixmap.get_colormap().alloc_color( BACKGROUND_COLOR ) )
                            txt = dia.create_pango_layout( enemy['level'] + "/" + enemy['hp'] )
                            txt.set_font_description( pango.FontDescription( "sans 8" ) )
                            size = txt.get_pixel_size()
                            #pixmap.draw_rectangle( gcs, gtk.TRUE, ( self.data["pictures_width"][enemy['cache']] - size[0] ) / 2 - 2, self.data["pictures_height"][enemy['cache']] - size[1] - 4, size[0] + 4, size[1] + 4)
                            for x in range( -1, 2 ):
                                for y in range( -1, 2 ):
                                    pixmap.draw_layout( gcs, ( self.data["pictures_width"][enemy['cache']] - size[0] ) / 2 + x, self.data["pictures_height"][enemy['cache']] - size[1] - 2 + y, txt )
                            pixmap.draw_layout( gc, ( self.data["pictures_width"][enemy['cache']] - size[0] ) / 2, self.data["pictures_height"][enemy['cache']] - size[1] - 2, txt )
                            pic.get_from_drawable( pixmap, pixmap.get_colormap(), 0, 0, 0, 0, -1, -1 )
                            #if not pic.get_has_alpha(): pic = pic.add_alpha( True, 255, 0, 255 )
                            pic = pic.add_alpha( True, 0, 0, 0 )
                            self.data["pictures"][enemy['cache']] = pic
                            pic.save( WORK_DIR + ".cache/" + enemy['cache'] + ".png", "png" )
                    for field in enemy.keys():
                        if field not in self.text_cache["unit"]: self.text_cache["unit"].append( field )
                    self.data["units"][unit] = enemy

        # Load MAPS
        for quest in [x["name"] for x in reversed( self.data["mods"] )]:
            quest_id = [x["name"] for x in self.data["mods"]].index( quest )
            if os.path.isdir( WORK_DIR + "mods/" + quest + "/maps" ):
                print( "(%s) Load maps..." % quest )
                for name in [f for f in os.listdir( WORK_DIR + "mods/" + quest + "/maps" ) if f.split( "." )[-1] == "txt"]:
                    if name in [x["name"] for x in self.data["mods"][quest_id]["maps"]]:
                        print( "(%s) ... %s (already stored)" % ( quest, name ) )
                        continue
                    print( "(%s) ... %s" % ( quest, name ) )
                    self.data["mods"][quest_id]["maps"].append( { "changed": False, "dir": WORK_DIR, "name": name, "background": [], "object": [], "collision": [], "events": {}, "enemies": {}, "file": "mods/" + quest + "/maps/" + name, "tileset": self.default_tileset } )
                    pb.set_text( "Load map: " + name + " ..." )
                    pb.pulse()
                    while gtk.events_pending(): gtk.main_iteration( False )
                    if PRELOAD:
                        self.actual_mod = quest_id
                        self.change_level( preload=[x["name"] for x in self.data["mods"][quest_id]["maps"]].index( name ) )
                    maps.append( name + ",{x},{y}" )

            # Load items
            print( "(%s) Load items..." % quest )
            pb.set_text( "Load items: " + quest + " ..." )
            pb.pulse()
            while gtk.events_pending(): gtk.main_iteration( False )
            if os.path.isfile( WORK_DIR + "mods/" + quest + "/items/items.txt" ):
                items = []
                for line in [x.strip() for x in open( WORK_DIR + "mods/" + quest + "/items/items.txt", 'r' ).readlines() if x.strip() and x[:1] != "#"]:
                    if line == "[item]": items.append( {} )
                    elif "=" in line:
                        items[-1][line.split( "=", 1 )[0]] = line.split( "=", 1 )[1]
                        if line.split( "=", 1 )[0] not in self.text_cache["item"]: self.text_cache["item"].append( line.split( "=", 1 )[0] )
                for x in items:
                    if x["id"] not in [i["id"] for i in self.data["mods"][quest_id]["items"]]: self.data["mods"][quest_id]["items"].append( x )
                    for field in x.keys():
                        if field not in self.text_cache["item"]: self.text_cache["item"].append( field )
                        if "item_" + field not in self.text_cache: self.text_cache["item_" + field] = []
                        if x[field] not in self.text_cache["item_" + field]: self.text_cache["item_" + field].append( x[field] )

            # Load quests
            if os.path.isfile( WORK_DIR + "mods/" + quest + "/quests/index.txt" ):
                print( "(%s) Load quests..." % quest )
                for name in [x.strip() for x in open( WORK_DIR + "mods/" + quest + "/quests/index.txt", 'r' ).readlines() if x[:1] != "#" and x.strip()]:
                    if name in self.data["mods"][quest_id]["quests"]: continue
                    print( "(%s) ... %s" % ( quest, name ) )
                    pb.set_text( "Load quest: " + name + " ..." )
                    pb.pulse()
                    while gtk.events_pending(): gtk.main_iteration( False )
                    self.data["mods"][quest_id]["quests"][name] = []
                    if os.path.isfile( WORK_DIR + "mods/" + quest + "/quests/" + name ):
                        quests = []
                        for line in [x.strip() for x in open( WORK_DIR + "mods/" + quest + "/quests/" + name, 'r' ).readlines() if x.strip() and x[:1] != "#"]:
                            if line == "[quest]": quests.append( {} )
                            elif "=" in line:
                                quests[-1][line.split( "=", 1 )[0]] = line.split( "=", 1 )[1]
                                if line.split( "=", 1 )[0] not in self.text_cache["quest"]: self.text_cache["quest"].append( line.split( "=", 1 )[0] )
                        for x in quests:
                            self.data["mods"][quest_id]["quests"][name].append( x )
                            for field in x.keys():
                                if field not in self.text_cache["quest"]: self.text_cache["quest"].append( field )
                                if "quest_" + quest + "_" + field not in self.text_cache: self.text_cache["quest_" + quest + "_" + field] = []
                                if x[field] not in self.text_cache["quest_" + quest + "_" + field]: self.text_cache["quest_" + quest + "_" + field].append( x[field] )

            #pb.set_fraction( pb.get_fraction() + 0.02 )
            pb.pulse()
            while gtk.events_pending(): gtk.main_iteration( False )

            # Reset selected map
            #if quest != "fantasycore":
            self.data["mods"][quest_id]["actual_map"] = 0
        self.actual_mod = 0

        # Cache correction
        try: del self.text_cache["event"][self.text_cache["event"].index( "sound" )]
        except: pass
        self.text_cache["event_intermap"] = maps
        self.text_cache["event_msg"] = ['""', '{msg}']
        self.text_cache["event_tooltip"] = ['""', '{msg}']
        self.text_cache["event_power_damage"] = ['{min},{max}']
        self.text_cache["event_location"] = ['{x},{y},{x_size},{y_size}']
        self.text_cache["event_mapmod"] = ['object,{x},{y},{id}', 'collision,{x},{y},{id}']
        try: self.text_cache["event_set_status"] = set( self.text_cache["event_set_status"] + self.text_cache["event_unset_status"] + self.text_cache["event_requires_status"] + self.text_cache["event_requires_not"] )
        except: pass
        try: self.text_cache["event_unset_status"] = self.text_cache["event_set_status"]
        except: pass
        try: self.text_cache["event_requires_status"] = self.text_cache["event_set_status"]
        except: pass
        try: self.text_cache["event_requires_not"] = self.text_cache["event_set_status"]
        except: pass

        # Main window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title( TITLE )
        self.window.maximize()
        self.window.connect( "delete_event", self.delete_event )
        self.window.connect( "destroy", lambda w: gtk.main_quit() )
        try: self.window.set_icon_from_file( self.logofile )
        except: pass
        self.window.set_position( gtk.WIN_POS_CENTER_ALWAYS )
        self.window.set_sensitive( False )

        # Main widget
        #box = gtk.HBox( False, 2 )
        box = gtk.HPaned()
        self.window.add( box )

        # Game area
        self.area = gtk.DrawingArea()
        self.area.set_size_request( DEF_X_SIZE, DEF_Y_SIZE )
        self.area.connect( "expose-event", self.area_expose )
        self.area.set_events( gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK )
        self.area.connect( "button-press-event", self.area_press_event )
        self.area.connect( "button-release-event", self.area_release_event )
        self.area.connect( "motion_notify_event", self.area_motion_event )
        self.window.connect( "key-press-event", self.key_press_event )
        frame = gtk.Frame()
        frame.add( self.area )
        frame.set_border_width( 2 )

        # Right button section
        rightbox = gtk.VBox( False, 2 )
        #box.pack_start( rightbox, False, False, 2 )
        #box.pack_start( frame, True, True, 2 )
        box.add1( rightbox )
        box.add2( frame )
        box.set_position( 320 )

        # Mod selector
        fbox = gtk.VBox( False, 2 )
        frame = gtk.Frame( " Mod " )
        frame.add( fbox )
        tbox = gtk.HBox( False, 2 )
        #tbox.pack_start( gtk.Label( "Mod:" ), False, False, 2 )
        rightbox.pack_start( frame, False, False, 2 )
        self.mod_list = gtk.combo_box_new_text()
        for x in self.data["mods"]:
            if x["name"] != "default": self.mod_list.append_text( x["name"] )
        tbox.pack_start( self.mod_list, True, True, 2 )
        fbox.pack_start( tbox, False, False, 2 )
        tbox = gtk.HBox( False, 2 )
        button = gtk.Button( "_New Map" )
        button.connect( "clicked", self.level_create )
        tbox.pack_start( button, True, True, 2 )
        button = gtk.Button( "_Save Map" )
        button.connect( "clicked", self.level_save )
        tbox.pack_start( button, True, True, 2 )
        button = gtk.Button( "_Exit" )
        button.connect( "clicked", self.destroy_event )
        tbox.pack_start( button, True, True, 2 )
        fbox.pack_start( tbox, False, False, 2 )

        # Level selector
        fbox = gtk.VBox( False, 2 )
        frame = gtk.Frame( " Level " )
        frame.add( fbox )
        rightbox.pack_start( frame, True, True, 2 )
        tbox = gtk.HBox( False, 2 )
        #tbox.pack_start( gtk.Label( "Lev:" ), False, False, 2 )
        self.level_list = gtk.combo_box_new_text()
        for x in self.data["mods"][self.actual_mod]["maps"]: self.level_list.append_text( x["name"] )
        self.level_list.set_active( self.data["mods"][self.actual_mod]["actual_map"] )
        tbox.pack_start( self.level_list, True, True, 2 )
        fbox.pack_start( tbox, False, False, 2 )

        # Type selector
        tbox = gtk.HBox( False, 2 )
        self.button_bg = gtk.RadioButton( None, "Bg" )
        self.button_bg.connect( "clicked", self.change_type )
        tbox.pack_start( self.button_bg, True, True, 2 )
        self.button_ob = gtk.RadioButton( self.button_bg, "Obj" )
        self.button_ob.connect( "clicked", self.change_type )
        tbox.pack_start( self.button_ob, True, True, 2 )
        self.button_un = gtk.RadioButton( self.button_ob, "Unit" )
        self.button_un.connect( "clicked", self.change_type )
        tbox.pack_start( self.button_un, True, True, 2 )
        fbox.pack_start( tbox, False, False, 2 )

        # Tile list
        self.tile_store = gtk.ListStore( gtk.gdk.Pixbuf, str )
        self.tile_list = gtk.TreeView( self.tile_store )
        self.tile_list.set_size_request( 148, -1 )
        renderer = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn( 'Tile' )
        column.pack_start( renderer, True )
        column.add_attribute( renderer, 'pixbuf', 0 )
        self.tile_list.append_column( column )
        self.tile_list.set_headers_visible(False)
        swin = gtk.ScrolledWindow()
        swin.set_policy( gtk.POLICY_NEVER, gtk.POLICY_ALWAYS )
        swin.add( self.tile_list )
        self.tile_frame = gtk.Frame()
        self.tile_frame.add( swin )
        self.tile_frame.set_border_width( 2 )
        fbox.pack_start( self.tile_frame, True, True, 2 )
        self.tile_list.get_selection().set_mode( gtk.SELECTION_MULTIPLE )

        # Unit list
        self.unit_store = gtk.ListStore( gtk.gdk.Pixbuf, str )
        self.unit_list = gtk.TreeView( self.unit_store )
        self.unit_list.set_size_request( 148, -1 )
        renderer = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn( 'Unit' )
        column.pack_start( renderer, True )
        column.add_attribute( renderer, 'pixbuf', 0 )
        self.unit_list.append_column( column )
        self.unit_list.set_headers_visible(False)
        swin = gtk.ScrolledWindow()
        swin.set_policy( gtk.POLICY_NEVER, gtk.POLICY_ALWAYS )
        swin.add( self.unit_list )
        self.unit_frame = gtk.Frame()
        self.unit_frame.add( swin )
        self.unit_frame.set_border_width( 2 )
        fbox.pack_start( self.unit_frame, True, True, 2 )
        for unit in self.data["units"].keys(): self.unit_store.append( [ self.data["pictures"][self.data["units"][unit]['cache']], unit ] )
        self.unit_list.set_cursor( 0 )
        self.unit_list.connect( 'row-activated', self.dialog_unit )

        # Viewer switchers
        tbox = gtk.HBox( False, 2 )
        self.button_coords = gtk.CheckButton( "_POS" )
        #self.button_coords.set_active( True )
        self.button_coords.connect( "clicked", self.area_expose )
        tbox.pack_start( self.button_coords, True, True, 2 )
        self.button_objs = gtk.CheckButton( "_OBJ" )
        self.button_objs.set_active( True )
        self.button_objs.connect( "clicked", self.area_expose )
        tbox.pack_start( self.button_objs, True, True, 2 )
        self.button_rnd = gtk.CheckButton( "_RND" )
        self.button_rnd.connect( "clicked", self.area_expose )
        tbox.pack_start( self.button_rnd, True, True, 2 )
        fbox.pack_start( tbox, False, False, 2 )

        # Create view
        dia.destroy()
        self.window.show_all()
        self.unit_frame.hide()

        # Load default level
        self.level_reload = self.level_list.connect( 'changed', self.change_level )
        self.mod_list.connect( 'changed', self.change_mod )
        self.mod_list.set_active( self.actual_mod )
        print( "Start..." )

        # Hello
        self.dialog_box( self.window, __HELP__, "Quick help" )


if __name__ == "__main__":

    FlareEdit()
    gtk.main()

# END
