import os
import random
import math
import pygame, sys
import pygame.time
# from button import Button
from os import listdir
from os.path import isfile, join

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 1000
HEIGHT = 600
FPS = 60
PLAYER_VEL = 5
YOYO_VEL = 7
LEVEL_ONE_WIDTH = 4000

# Set window caption
pygame.display.set_caption("Leap Mania")

# Set up window
window = pygame.display.set_mode((WIDTH, HEIGHT))



def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join('assets', dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]
    
    all_sprites = {}
    
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        
        sprites = []
        for i in range(sprite_sheet.get_width() //width): 
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))
            
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
            
    return all_sprites

def get_block(size):
    path = join('assets', "Terrain", 'MyTerrain.png')
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 128, size, size) 
    # rect = pygame.Rect(96, 64, size, size) # Use different block
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "TheLeaper", 32, 32, True)
    ANIMATION_DELAY = 3
    
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        
    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0
        
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel): 
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0
              
    def move_right(self, vel): 
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0
            
    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)
        
        self.fall_count += 1
        self.update_sprite()
        
    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
        
    def hit_head(self):
        self.count = 0
        self.y_vel *= -1
            
    def update_sprite(self):
        sprite_sheet = "idle"
      
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"
            
        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        spite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[spite_index]
        self.animation_count += 1
        self.update()
        
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)
        
    def draw(self, win, offset_x):
        self.update_sprite()  # Ensure sprite is updated
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

        
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
        
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))
        
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)
        
class LeftBoundary(Object):
    def __init__(self, y, height):
        super().__init__(0, y, 1, height)  # 1 pixel wide, spans window height
        self.mask = pygame.mask.from_surface(pygame.Surface((1, height)))  # Invisible mask
        
    def update_position(self, offset_x):
        self.rect.x = offset_x

def get_background(name):
    image = pygame.image.load(join('assets', 'Background', name))
    _,_, width, height = image.get_rect()
    tiles = []
    
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = [i * width, j * height]
            tiles.append(pos)
            
    return tiles, image
        
        
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
                
        collided_objects.append(obj)
        
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    
    player.move(-dx, 0)
    player.update()
    return collided_object
        
def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)
    
    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)
        
    handle_vertical_collision(player, objects, player.y_vel)
      
def draw_window(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)
    
    for obj in objects:
        obj.draw(window, offset_x)
    
    player.draw(window, offset_x)
        
    pygame.display.update()
    
def reset_game():
    block_size = 96
    left_boundary = LeftBoundary(300, HEIGHT)
    player = Player(0, 350, 100, 100)
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
    objects = [left_boundary, Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size),
               Block(block_size * 5, HEIGHT - block_size * 4, block_size),
               Block(block_size * 10, HEIGHT - block_size * 4, block_size),
               Block(block_size * 20, HEIGHT - block_size * 4, block_size),
               Block(block_size * 18, HEIGHT - block_size * 3, block_size)]
    return player, objects
        
# Game event loop
def main(window):
     # Load music
    pygame.mixer.init()  # Initialize the mixer module
    pygame.mixer.music.load("assets/Music/ohno.wav")  # Load the music file
    pygame.mixer.music.play(-1)  # Play the music indefinitely (-1)
    
    # Initialize variables
    block_size = 96
    left_boundary = LeftBoundary(300, HEIGHT)
    player = Player(0, 350, 100, 100)
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
    objects = [left_boundary, Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 1, HEIGHT - block_size * 2, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size),
               Block(block_size * 5, HEIGHT - block_size * 4, block_size),
               Block(block_size * 7, HEIGHT - block_size * 2, block_size),
               Block(block_size * 10, HEIGHT - block_size * 4, block_size),
               Block(block_size * 13, HEIGHT - block_size * 4, block_size),
               Block(block_size * 17, HEIGHT - block_size * 3, block_size),
               Block(block_size * 21, HEIGHT - block_size * 3, block_size),
               Block(block_size * 24, HEIGHT - block_size * 3, block_size),
               Block(block_size * 26, HEIGHT - block_size * 2, block_size),]
    
    # Initialize variables
    reset_delay = 2000  # 4 seconds in milliseconds
    fall_time = None
    
    offset_x = 0
    scroll_area_width = 200
    background, bg_image = get_background('Test.png')
    clock = pygame.time.Clock()
    run = True
    
    # Main loop
    while run:
        clock.tick(FPS) # Never go over the framerate
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # Quit if the red button is clicked
                run = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        handle_move(player, objects)
        
        # Track player moving right
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0):
            offset_x += player.x_vel
            left_boundary.update_position(offset_x)  # Update left boundary position

        # if player.rect.y > HEIGHT:
        #     pygame.mixer.music.stop()
            
         # Check if player fell off the edge
        if player.rect.y > HEIGHT:
            if fall_time is None:
                fall_time = pygame.time.get_ticks()  # Record the time when player falls
            elif pygame.time.get_ticks() - fall_time >= reset_delay:
                # Reset the game after the delay
                player, objects = reset_game()
                offset_x = 0
                fall_time = None
            
        # Print debug info
        print(f"Player X: {player.rect.x}")
            
        draw_window(window, background, bg_image, player, objects, offset_x)

                
    pygame.quit()
    quit()
    
if __name__ == "__main__":
    main(window)