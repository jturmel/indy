#!/usr/bin/env python

import curses
import curses.textpad
import os
import re

"""
TODO Keep an LRU to pre-populate the list
TODO Possibly cache the results as you type each letter that way if you
     backspace we can just use the cache
TODO Handle terminal resizing
"""

WINS = {}
ALL_FILES = None
CHAR_COMBOS = {}


def find(partial):
    '''
    Walk directory path and find files matching search
    If multiple files are found, call prompt() with list
    '''
    # Make the search fuzzy match
    search = '.*?'.join(map(re.escape, list(partial)))

    scores = []
    for f in ALL_FILES:
        scores.append(calculate_score(search, partial, f))

    # Zip scores & all files together, but only for scores > 0
    matches = [f for (score, f) in sorted(zip(scores, ALL_FILES),
               reverse=True) if score > 0]

    return matches


def get_char_combos(chars):
    '''
    Get the 2 letter character combos from a string
    '''
    global CHAR_COMBOS
    combo_list = CHAR_COMBOS.get(chars)

    if combo_list is None:
        char_list = []
        combo_list = []
        for char in chars:
            char_list.append(char)
        for key, val in enumerate(char_list):
            try:
                next_key = key + 1
                combo_list.append(val + char_list[next_key])
            except IndexError:
                break
        CHAR_COMBOS[chars] = combo_list

    return combo_list


def calculate_score(regex, literal, path):
    '''
    Get the score for a given path matching a pattern
    If the path ends with the pattern, give the highest score
    Also if the pattern is an exact match in the path, give a high score
    Otherwise, do more complicated algorithm to decide what I'm really
    trying to find.
    Also if no 2 characters in the string are in a row, assume that
    isn't really what we're looking for and discard
    '''
    if path.endswith(literal):
        score = 100
    elif literal in path:
        # This is an exact match to give it a high score
        # Start with 100, but give more precendence to an exact match
        # ending with the exact match
        match = re.search(regex, path)
        len_from_end = len(path) - match.end()
        score = 100 - len_from_end
    else:
        match = re.search(regex, path)
        # A match is scored more if the characters in the patterns are closer
        # to each other and if it's closer to the end of the path
        if match is None:
            score = 0
        else:
            # Check if any 2 characters in the pattern are consecutive in path
            char_combos = get_char_combos(literal)
            any_match = False
            for cc in char_combos:
                if cc in path:
                    any_match = True
                    break

            if any_match is False:
                score = 0
            else:
                distance_between = match.end() - match.start()
                len_from_end = len(path) - match.end()
                score = 100 - len_from_end - distance_between

    return score


def reset_input(val):
    __, mx = WINS['input'].getmaxyx()
    clr = ''.join([' '] * (mx - 2))
    WINS['input'].addstr(0, 0, clr)
    WINS['input'].addstr(0, 0, val)
    WINS['input'].refresh()


def clear_results():
    __, mx = WINS['results'].getmaxyx()
    clr = ''.join([' '] * (mx - 2))
    for i in range(0, 10):
        WINS['results'].addstr(i, 0, clr)

    WINS['results'].refresh()


def vim_open(path):
    '''
    Open the given file path in vim
    '''
    os.execlp('vim', 'vim', path)


def main():
    global ALL_FILES
    global WINS
    global CHAR_COMBOS

    rootdir = os.getcwd()
    ALL_FILES = []
    for root, dirs, files in os.walk(rootdir):
        if '.git' in dirs:
            dirs.remove('.git')
        for f in files:
            # Skip files that end in .swp
            if f.endswith(('.swp', '.pyc')):
                continue

            full_path = os.path.abspath(os.path.join(root, f))

            full_path = full_path.replace(rootdir, '')
            ALL_FILES.append(full_path)

    screen = curses.initscr()
    my, mx = screen.getmaxyx()

    top_y = my - 14

    WINS['main'] = curses.newwin(14, mx, top_y, 0)
    WINS['main'].border(0)
    WINS['main'].hline(11, 1, curses.ACS_HLINE, mx - 2)
    WINS['main'].refresh()

    WINS['results'] = WINS['main'].derwin(10, mx - 4, 1, 2)
    WINS['results'].refresh()

    WINS['input'] = WINS['main'].derwin(1, mx - 4, 12, 2)
    WINS['input'].keypad(1)
    WINS['input'].refresh()

    query = []

    matches = []
    curses.noecho()
    cur_choice = None
    my, mx = WINS['input'].getmaxyx()
    cy, cx = WINS['input'].getyx()
    while True:
        my, mx = WINS['input'].getmaxyx()
        cy, cx = WINS['input'].getyx()

        c = WINS['input'].getch()

        if c == curses.KEY_UP:
            if len(matches) > 0:
                if not cur_choice:
                    pos = len(matches)
                else:
                    pos = cur_choice - 1

                if pos == 0:
                    pos = 10

                WINS['results'].move(pos - 1, 0)
                WINS['results'].refresh()
                cur_choice = pos
            continue
        if c == curses.KEY_DOWN:
            if len(matches) > 0:
                if not cur_choice:
                    pos = 1
                else:
                    pos = cur_choice + 1

                if pos == 11:
                    pos = 1

                WINS['results'].move(pos - 1, 0)
                WINS['results'].refresh()
                cur_choice = pos
            continue
        if c == 10:
            if cur_choice:
                vim_open('.{0}'.format(matches[cur_choice - 1]))
                exit()
            break
        elif c == 127:
            cur_choice = None
            WINS['input'].delch(cy, cx)
            if cx == 0:
                clear_results()
                continue
            WINS['input'].delch(cy, cx - 1)
            query.pop()
        elif c >= 0 and c <= 255:
            cur_choice = None
            query.append(chr(c))
        else:
            cur_choice = None
            continue

        q = ''.join(query)
        matches = find(q)
        #fuzzyMatcher.setPattern(q)
        reset_input(q)

        matches = matches[:10]
        matches.reverse()

        clear_results()
        for i, match in enumerate(matches):
            WINS['results'].addstr(i, 0, match)

        WINS['results'].refresh()
        WINS['input'].refresh()

    curses.endwin()

if __name__ == '__main__':
    main()
