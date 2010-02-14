#!/usr/bin/env python

import logging
import os
import sys
import random

import pygame
from pygame.locals import *

import typy.words
import typy.events

if os.environ.get('DEBUG'):
    logging.basicConfig(level=logging.DEBUG)

class LetterSpool(object):
    spooled = None
    parent = None
    font = None
    clear_keys = (K_SPACE,)
    color = (255, 255, 255,)
    parent_width = None
    parent_height = None

    def __init__(self, parent, **kwargs):
        self.__dict__.update(kwargs)
        self.parent = parent
        self.parent_width, self.parent_height = parent.get_size()
        self.font = pygame.font.SysFont('Courier', 32)
        self.spooled = []

    def clear(self):
        logging.debug('LetterSpool.clear()')
        event = pygame.event.Event(typy.events.WORD_COMPLETED,
                word=''.join(self.spooled))
        pygame.event.post(event)
        self.spooled = []

    def handle_key(self, event):
        if event.key in self.clear_keys:
            self.clear()
            return

        if event.key == K_BACKSPACE:
            self.spooled = self.spooled[:-1]
        elif event.key != K_RETURN:
            self.spooled.append(event.unicode)

        buffer = ''.join(self.spooled)
        spool_width, spool_height = self.font.size(buffer)
        offset_y = self.parent_height - (5 + spool_height)
        offset_x = (self.parent_width / 2) - (spool_width / 2)
        self.parent.blit(self.font.render(buffer, 0, self.color),
                (offset_x, offset_y,))

class AnimatingObject(object):
    pass

class AnimatingWord(AnimatingObject):
    def __init__(self, parent, word, **kwargs):
        self.__dict__.update(kwargs)
        self.color = (255, 255, 255,)
        self.parent = parent
        self.parent_width, self.parent_height = parent.get_size()
        self.word = word
        self.step = 0.05
        self.font = pygame.font.SysFont('Courier', 42)

        self.width, self.height = self.font.size(word)
        self.offset_x = self.parent_width
        self.offset_y = (self.parent_height / 2) - (self.height / 2)
        self.surface = self.render_word()

    def render_word(self):
        return self.font.render(self.word, 0, self.color)

    def offscreen(self):
        if self.offset_x + self.width <= 0:
            return True
        return False

    def next_ready(self):
        ''' Returns true if we're far enough left to start the next word '''
        space_w, space_h = self.font.size(' ')
        if self.width + self.offset_x + space_w <= self.parent_width:
            return True
        return False

    def update(self):
        ''' Update the word's position, returning True if it's offscreen '''
        self.parent.fill( (0, 0, 0),
                rect=pygame.Rect(self.offset_x, self.offset_y,
                    self.width, self.height))
        if self.offset_x <= 0:
            self.color = (255, 0, 0)
            self.surface = self.render_word()
        self.parent.blit(self.surface, (self.offset_x, self.offset_y))
        self.offset_x = self.offset_x - self.step
        return False


class GameRunner(object):
    surface = None
    size = None
    clock = None
    tick = 30
    background_music = False
    font = None
    spool = None

    def __init__(self, width, height, **kwargs):
        self.size = width, height
        self.surface = pygame.display.set_mode(self.size,
                pygame.HWSURFACE | pygame.DOUBLEBUF)

        self.clock = pygame.time.Clock()
        self.clock.tick(self.tick)
        pygame.display.set_caption('Typy!')
        pygame.mouse.set_visible(False)

        self.font = pygame.font.SysFont('Courier', 48)
        self.spool = LetterSpool(self.surface)

    def should_exit(self, event):
        if event.type == QUIT:
            return True
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            return True
        return False

    def handle_key_event(self, event):
        ## Return a boolean whether we should continue the runloop
        if self.should_exit(event):
            return False
        if event.type == KEYDOWN:
            self.surface.fill((0, 0, 0))
            self.spool.handle_key(event)
        return True

    def runloop(self):
        run = True
        if self.background_music:
            pygame.mixer.music.load('background.mid')
            pygame.mixer.music.play(-1, 0.0)

        pygame.event.set_allowed(typy.events.WORD_COMPLETED)
        scrollwords = [AnimatingWord(self.surface, w) for w in typy.words.words()]
        last_word_index = 0
        while run:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    run = self.handle_key_event(event)
                    continue
                if event.type == typy.events.WORD_COMPLETED:
                    first_word = scrollwords[0]
                    if first_word.word == event.word:
                        logging.debug('Player completed word "%s"' % event.word)
                        scrollwords = scrollwords[1:]
                        last_word_index -= 1
                        if last_word_index < 0:
                            last_word_index = 0
                    self.surface.fill((0, 0, 0))

            for index, word in enumerate(scrollwords):
                if index <= last_word_index:
                    word.update()

            if last_word_index <= (len(scrollwords) - 1):
                if scrollwords[last_word_index].next_ready():
                    last_word_index += 1

            if scrollwords and scrollwords[0].offscreen():
                scrollwords = scrollwords[1:]
                last_word_index -= 1

            pygame.display.update()
        if self.background_music:
            pygame.mixer.music.stop()

if __name__ == "__main__" :
    pygame.init()
    game = GameRunner(640, 480)
    game.runloop()
    pygame.quit()
