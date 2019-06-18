#! /usr/bin/python

import pygame
from pygame import *

SCREEN_SIZE = pygame.Rect((0, 0, 800, 640))
TILE_SIZE = 64 
GRAVITY = pygame.Vector2((0, 2))

GAMESTATE_INTRO = 0
GAMESTATE_LEVEL_INIT = 1
GAMESTATE_LEVEL_PLAY = 2
GAMESTATE_LEVEL_COMPLETE = 3
GAMESTATE_GAMEOVER = 4


# todo -- make these non global in future
level_height = 0
camX = 0


class CameraAwareLayeredUpdates(pygame.sprite.LayeredUpdates):
    def __init__(self, target, world_size):
        super().__init__()
        self.target = target
        self.cam = pygame.Vector2(0, 0)
        self.world_size = world_size
        if self.target:
            self.add(target)

    def update(self, *args):
        global camX
        super().update(*args)
        self.cam.x -= 2.5

        camX = self.cam.x
    
    def draw(self, surface):
        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = []
        dirty_append = dirty.append
        init_rect = self._init_rect
        for spr in self.sprites():
            rec = spritedict[spr]
            newrect = surface_blit(spr.image, spr.rect.move(self.cam))
            if rec is init_rect:
                dirty_append(newrect)
            else:
                if newrect.colliderect(rec):
                    dirty_append(newrect.union(rec))
                else:
                    dirty_append(newrect)
                    dirty_append(rec)
            spritedict[spr] = newrect
        return dirty            


def text_objects(text, font):
    textSurface = font.render(text, True, (0, 0, 0))
    return textSurface, textSurface.get_rect()

def draw_text(screen, text, centerXY):
    largeText = pygame.font.Font('freesansbold.ttf', 40)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = centerXY
    screen.blit(TextSurf, TextRect)

def drawLevelCompleteScreen(screen):
    text = "Level Complete, you won!"
    draw_text(screen, text, ((800/2), (640/2)))


def drawLevelFailedScreen(screen):
    text = "You died, sorry..."
    draw_text(screen, text, ((800/2), 100))

    text = "Press R to retry"
    draw_text(screen, text, ((800/2), 400))


def drawIntroScreen(screen):
    text = "Welcome to Square Runner!"
    draw_text(screen, text, ((800/2), 100))

    text = "Press P to play"
    draw_text(screen, text, ((800/2), 400))


def initLevel(screen):
    global level_height

    level = [
        "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
        "O                                                                                   O",
        "O                                                                                   O",
        "O                                                                                   O",
        "O                      O                                                            O",
        "O                  O                                                                O",
        "O              R           OOOO                                                     O",
        "O          R                                                                        O",
        "O      RT                                               E                            O",
        "OOOOOOOOOO                          OOOO   OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
     ]


    platforms = pygame.sprite.Group()
    player = Player(platforms, (TILE_SIZE, TILE_SIZE))
    level_width  = len(level[0])*TILE_SIZE
    level_height = len(level)*TILE_SIZE
    entities = CameraAwareLayeredUpdates(player, pygame.Rect(0, 0, level_width, level_height))

    # build the level
    x = y = 0
    for row in level:
        for col in row:
            if col == "T":
                Tree((x, y), platforms, entities)
            if col == "E":
                ExitBlock((x, y), platforms, entities)
            if col == "R":
                Rock((x, y), platforms, entities)
            if col == "O":
                OrangeBlock((x,y), platforms, entities)

            x += TILE_SIZE
        y += TILE_SIZE
        x = 0

    return entities


def main():
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE.size)
    pygame.display.set_caption("Use arrows to move!")
    timer = pygame.time.Clock()

    entities = None
    state = GAMESTATE_INTRO

    while 1:
        # Process Events
        for e in pygame.event.get():
            if e.type == QUIT: 
                return
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                return
            if e.type == KEYDOWN and e.key == K_p and state == GAMESTATE_INTRO:
                state = GAMESTATE_LEVEL_INIT
            if e.type == KEYDOWN and e.key == K_r and state == GAMESTATE_GAMEOVER:
                state = GAMESTATE_LEVEL_INIT
            if e.type == USEREVENT:
                print("got a user event!\n\n")
                print(e)

                if (hasattr(e, "level_complete") and e.level_complete == True and state == GAMESTATE_LEVEL_PLAY):
                    print("changing state to level complete")
                    state = GAMESTATE_LEVEL_COMPLETE

                if (hasattr(e, "dead") and e.dead == True and state == GAMESTATE_LEVEL_PLAY):
                    print("changing state to game over")
                    state = GAMESTATE_GAMEOVER


        # State machine
        if state == GAMESTATE_INTRO:
            screen.fill((255, 255, 255))
            drawIntroScreen(screen)
        elif state == GAMESTATE_LEVEL_INIT:
            entities = initLevel(screen)
            state = GAMESTATE_LEVEL_PLAY
        elif state == GAMESTATE_LEVEL_PLAY:
            entities.update()
            screen.fill((255, 255, 255))
            entities.draw(screen)

        elif state == GAMESTATE_LEVEL_COMPLETE:
            screen.fill((255, 255, 255))
            drawLevelCompleteScreen(screen)

        elif state == GAMESTATE_GAMEOVER:
            screen.fill((255, 255, 255))
            drawLevelFailedScreen(screen)

        
        pygame.display.update()
        timer.tick(50)


class Entity(pygame.sprite.Sprite):
    def __init__(self, color, pos, *groups):
        super().__init__(*groups)
        self.image = Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=pos)

class Player(Entity):
    def __init__(self, platforms, pos, *groups):
        super().__init__(Color("#0000FF"), pos)
        self.vel = pygame.Vector2((0, 0))
        self.onGround = False
        self.platforms = platforms
        self.speed = 15
        self.jump_strength = 16

        pygame.draw.rect(self.image, (0, 0, 255), (0, 0, 20, 20))


    def update(self):
        pressed = pygame.key.get_pressed()
        up = pressed[K_UP]
        left = pressed[K_LEFT]
        right = pressed[K_RIGHT]
        running = pressed[K_SPACE]
        down = pressed[K_DOWN]

        if up:
            # only jump if on the ground
            if self.onGround: self.vel.y = -self.jump_strength
        #if down:
        #    self.vel.y = self.jump_strength
        if left:
            self.vel.x = -self.speed
        if right:
            self.vel.x = self.speed
        if running:
            self.vel.x *= 1.5
        if not self.onGround:
            # only accelerate with gravity if in the air
            self.vel += GRAVITY
            # max falling speed
            if self.vel.y > 200: self.vel.y = 200

        #print(self.vel.y)
        if not(left or right):
            self.vel.x = 0
        # increment in x direction
        self.rect.left += self.vel.x
        # do x-axis collisions
        self.collide(self.vel.x, 0, self.platforms)
        # increment in y direction
        self.rect.top += self.vel.y
        # assuming we're in the air
        self.onGround = False;
        # do y-axis collisions
        self.collide(0, self.vel.y, self.platforms)

        # see if player died
        if ((self.rect.y > level_height) or (abs(camX) > self.rect.x)):
            e = pygame.event.Event(pygame.USEREVENT, dead=True)
            pygame.event.post(e)

    def collide(self, xvel, yvel, platforms):
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if isinstance(p, ExitBlock):
                    e = pygame.event.Event(pygame.USEREVENT, level_complete=True)
                    pygame.event.post(e)
                if xvel > 0:
                    self.rect.right = p.rect.left
                if xvel < 0:
                    self.rect.left = p.rect.right
                if yvel > 0:
                    self.rect.bottom = p.rect.top
                    self.onGround = True
                    self.yvel = 0
                if yvel < 0:
                    self.rect.top = p.rect.bottom

class OrangeBlock(Entity):
    def __init__(self, pos, *groups):
        super().__init__(Color('#FFA500'), pos, *groups)

            
class Tree(Entity):
    def __init__(self, pos, *groups):
        super().__init__(Color("#DDDDDD"), pos, *groups)

        img = pygame.image.load("mooky-tree.png")
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        self.image.blit(img, (0, 0))

class Rock(Entity):
    def __init__(self, pos, *groups):
        super().__init__(Color("#DDDDDD"), pos, *groups)

        img = pygame.image.load("mooky-rocks.png")
        img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
        self.image.blit(img, (0, 0))


class ExitBlock(Entity):
    def __init__(self, pos, *groups):
        super().__init__(Color("#FF0000"), pos, *groups)

if __name__ == "__main__":
    main()

