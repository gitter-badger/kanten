#!/usr/bin/env python
import urwid
from urwid import Padding, Text, Pile, ProgressBar
import time
import IPython
import pudb
import sys
import argparse
DEBUG = False

parser = argparse.ArgumentParser(description='A more aesthetic pager')
parser.add_argument('filenames', metavar='f', nargs='*',
                   help='an integer for the accumulator')
parser.add_argument( '-w','--width', dest='width', metavar='N', type=int,
                   default=80,
                   help='the number of character in a column')

args = parser.parse_args()
width= args.width

if not args.filenames:
    # XXX: in the future this will be an explanation of how to use kanten
    fname = '/home/pi/cur/das.txt'
else:
    fname = args.filenames[0]

off_screen = []

k_next = (' ', 'f', 'z', 'j', 'l',  'ctrl f', 'ctrl v')
k_back = ('b', 'B', 'w', 'k', 'h', 'ctrl b')
k_top = ('g', '<', 'p')
k_end = ('G', '>')
k_info = ('ctrl g', '=')
k_search = ('/',)
k_next_search = ('n',)
k_prev_search = ('N',)
k_toggle_pbar = ('t',)
k_command = (':',)
k_submit = ('enter',)
k_escape = ('esc',)

do_cmd = lambda x: None

def show_or_exit(key):
    global off_screen
    global last_key
    global show
    global do_cmd
    txt = ''

    # set the progress bar visibility, so info can set it just once
    pbh.send(show)

    if key != '.':
        last_key = key
    else:
        key = last_key
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()
    elif key in k_back:
        #off_screen.append(cols.contents.pop())
        for x in range(displayed_columns):
            if off_screen:
                new_first = off_screen.pop()
                cols.contents.insert(0, new_first)
                cols.focus_position=0
    elif key in k_top:
        # take it from the top
        cols.contents = off_screen + cols.contents
        off_screen = []
        cols.focus_position=0
    elif key in k_end:
        # this is the end, my friends, the end, the end.
        off_screen.extend(cols.contents)
        # backfill here properly - fill the hole screen (add back as many columns as can be displayed)
        cols.contents = [off_screen.pop() for x in range(displayed_columns) ][::-1]
        txt = '(END)'
    elif key in k_next:
        for x in range(displayed_columns):
            if len(cols.contents) > displayed_columns:
                off_screen.append(cols.contents.pop(0))
        if len(cols.contents) == displayed_columns:
            txt = '(END)'
    elif key in k_search:
        #cmd_line_text.focus()
        all.set_focus('footer')
        txt = '/'
        do_cmd = lambda x: rehighlight(txts, x)
        cmd_line_text.set_edit_text('')
    elif key in k_command:
        txt = ':'
        all.set_focus('footer')
    elif key in k_submit:
        if all.get_focus() == 'footer':
            input = cmd_line_text.get_edit_text()
            txt = 'submitted ' + input
            cmd_line_text.set_edit_text('');
            do_cmd(input)
            # put code to submit the selection here
            all.set_focus('body')
    elif key in k_escape:
        if all.get_focus() == 'footer':
            txt = ''
            all.set_focus('body')
    elif key in k_next_search:
        # focus pane with a next result only if found
        rehighlight(txts,'com')
        pass
    elif key in k_prev_search:
        rehighlight(txts,'the')
        # focus last result only if found
        pass
    elif key in k_info:
        #loop.widget = loop.cmd
        #all.contents.append(((1, urwid.Filler(Text("hello"))), all.options()))
        txt = fname
        txt += "  (%d / %d)" % (total_cols-len(cols.contents) +
                displayed_columns , total_cols)
        if len(cols.contents) == displayed_columns:
            txt += ' (END)'
        pbh.send(True)
    elif key in k_toggle_pbar:
        show = not show
        pbh.send(show)
    cmd_line_text.set_caption(txt)
    #cmd_line_text.set_edit_text(txt)
    pbar.set_completion(len(off_screen)+displayed_columns)

show = True
def progress_bar_handler():
    """Progress bar coroutine. Send it whether or not you want to show the
    progress bar. 

    XXX: despite good intentions, I think I overengineered this bit. It could
    probably just be a function - I originally was trying to do some timing
    stuff in here, but ended up ripping out before making the commit
    """
    show = (yield)
    while True:
        if not len(p.body):
            p.body.append(pbar)
        if not show:
            if len(p.body):
                p.body.pop()
        show = (yield)

pbh = progress_bar_handler()
pbh.next()

# XXX: implement buffering here, don't read the whole file / piped message
if not sys.stdin.isatty():
    # read from a pipe
    text = sys.stdin.read()
    import os
    sys.stdin.close()
    # reopen stdin now that we've read from the pipe
    sys.__stdin__ = sys.stdin = open('/dev/tty')
    os.dup2(sys.stdin.fileno(), 0)
    fname = 'STDIN'
else:
    with open(fname) as f:
        text = f.read()

height=45

screen =  screen = urwid.raw_display.Screen()
max_width, max_height = screen.get_cols_rows()

height = max_height-10

def make_text(t):
    result = Padding(Text(t, align='left'), ('relative', 100), width, left=2,
            right=2)
    if DEBUG:
        return urwid.LineBox(result)
    return result

#txt = urwid.Text(text)
#text =  text.replace("\n","\n\n")
def search(text, word):
    txts = text.split(word)
    f = lambda x: ('important', word)
    res = list(f((yield t)) for t in txts)
    
    #res = [t for stub in txts for t in (stub, ('important', word))]
    # N. B. this approach adds a superflous trailing match
    return res[:-1]

def rehighlight(txts, s):
    [t.original_widget.set_text(search(t.original_widget.text, s)) for t in txts]


#text = [
txts = [make_text(t) for t in text.split('\n')]
#s = search(text, 'all')
#txts = [make_text(list(t)) for t in zip(s[::3], s[1::3], s[2::3])]
#[t.original_widget.set_text(search(t.original_widget.text, 'all')) for t in txts]
rehighlight(txts,'all')
#if DEBUG:
#    # my brain finds it easier to deal with boxes
#    txts = [urwid.LineBox(t) for t in txts]
pile  = Pile(txts)


def trim(t, d, w=width):
    """Trim the text in `t` to only `d` lines, assuming a width of `w`"""
    if DEBUG:
        pre_rendered_text = t.original_widget.original_widget.text
        lines = t.original_widget.original_widget.render((width-2,)).text
        # now make a new text widget to hold the remaining lines. It will
        # be added to the next pile, which we will also initialize here
        if d >= len(lines):
            # happens because we clip the text, and not the linebox
            next_start = 0
        else:
            next_start = pre_rendered_text.find(lines[d].strip())
        t.original_widget.original_widget.set_text(pre_rendered_text[:next_start])
        return make_text(pre_rendered_text[next_start:])

    pre_rendered_text = t.original_widget.text
    lines = t.render((w,)).text

    # now make a new text widget to hold the remaining lines. It will
    # be added to the next pile, which we will also initialize here
    next_start = pre_rendered_text.find(lines[d].strip())
    t.original_widget.set_text(pre_rendered_text[:next_start])
    return make_text(pre_rendered_text[next_start:])

def h(e):
    return e.rows((width,))

piles = []
p = Pile([])
for t in txts[:]:
    #if 'What emerges' in t.text: pu.db
    p.contents.append((t, p.options()))
    t_size = t.rows((width,))
    #if piles and h(piles[-1]) > height: pu.db
    while h(p) > height:
        # Add a new pile, and send the trimmings in there
        piles.append(p)
        d = h(t) - (h(p) - height)
        
        #if d <= 0: pu.db
        
        # start the next column
        p_new = Pile([])
        t_extra = trim(t, d, width)
        p_new.contents.append((t_extra, p.options()))
        p = p_new
        t = t_extra


    #if piles and h(piles[-1]) > height:
    #    # ACK!
    #    break
    if h(p) == height:
        piles.append(p)
        # start the next column
        p = Pile([])

# all done, don't forget the last pile which we haven't added to the list yet
piles.append(p)

palette = [
    (None,  'light gray', 'black'),
    ('heading', 'black', 'light gray'),
    ('important', 'black', 'light cyan'),
    ('line', 'black', 'light gray'),
    ('options', 'dark gray', 'black'),
    ('focus heading', 'white', 'dark red'),
    ('focus line', 'black', 'dark red'),
    ('focus options', 'black', 'light gray'),
    ('pg normal',    'white',      'black', 'standout'),
    ('pg complete',  'white',      'dark magenta'),
    ('selected', 'white', 'dark blue')]

#piles = urwid.ListBox(urwid.SimpleFocusListWalker(piles))
#cols = piles
#fill = cols
cols = urwid.Columns(piles, dividechars=1, min_width=width)

# XXX: I need to subclass columns, and make it so the keypress function
# "rolls" the piles under the hood, and re-renders all the widgets.
#
# self.contents.append(self.contents.pop(0))
#
#cols.box_columns.extend(cols.widget_list)


#grid = urwid.GridFlow(txts, cell_width=20, h_sep=4, v_sep=0, align='left')
fill = urwid.Filler(cols, 'top', top=4)
total_cols = len(cols.contents)
displayed_columns = len( cols.column_widths(screen.get_cols_rows()))
pbar = ProgressBar('pg normal', 'pg complete', displayed_columns, total_cols)
p = urwid.ListBox(urwid.SimpleListWalker([pbar]))
cmd_line_text = urwid.Text(fname)
cmd_line = urwid.Filler(cmd_line_text, bottom=1)
#cmd_line = urwid.Overlay(cmd_line, p, 'center', None, 'middle', None)

all = Pile([ fill, (1, p), ]) #(1, cmd_line) ] )
cmd_line_text = urwid.Edit(fname)
all = urwid.Frame(body=all, footer=cmd_line_text)
loop = urwid.MainLoop(all, palette, screen, unhandled_input=show_or_exit)
loop.cmd = cmd_line

#IPython.embed()

loop.run()

if DEBUG:
    for p in piles:
        print h(p)
        for c in p.contents:
            print "\t" , h(c[0])

#print [type(t.original_widget.text) for t in txts]
#print [(t.original_widget.get_text()[1]) for t in txts[0:100]]
f = lambda t:t.original_widget.get_text()[1]
g = lambda t:len(f(t))
#print [f(t) for t in txts[:] if g(t)>0]


#IPython.embed()
#pu.db
