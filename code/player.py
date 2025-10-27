from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups,collision_sprites):
        #Character Sprite
        super().__init__(groups)
        self.load_images()
        self.state, self.frame_index = "down", 0
        self.image = pygame.image.load(join('images','player','down','0.png')).convert_alpha()
        self.rect = self.image.get_frect(center = pos)

        #Movement
        self.direction = pygame.math.Vector2()
        self.speed = 500
        self.collision_sprites = collision_sprites

        #hitbox
        self.hitbox_rect= self.rect.inflate(-90,-90)

    def load_images(self):
        self.frames= {'left':[],'right':[],'up':[],'down':[]}

        for state in self.frames.keys():
            for folder_path, sub_folders, file_names in walk(join( 'images','player',state)):
                if file_names:
                    for file_name in sorted(file_names, key= lambda name: int (name.split('.')[0])):
                        full_path = join(folder_path,file_name)
                        surf = pygame.image.load(full_path).convert_alpha()
                        self.frames[state].append(surf)
        print(self.frames)

    def input(self):
        key = pygame.key.get_pressed()
        self.direction.x = int(key[pygame.K_RIGHT] or key[pygame.K_d]) - int(key[pygame.K_LEFT] or key[pygame.K_a])
        self.direction.y = int(key[pygame.K_DOWN] or key[pygame.K_s]) - int(key[pygame.K_UP] or key[pygame.K_w])
        self.direction = self.direction.normalize() if self.direction else self.direction

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y > 0: self.hitbox_rect.bottom= sprite.rect.top
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom

    def animate(self, dt):
        # Get the State
        if self.direction.x !=0:
            self.state = 'right' if self.direction.x > 0 else 'left'
        if self.direction.y !=0:
            self.state = 'down' if self.direction.y > 0 else 'up'
        


        #Animation
        self.frame_index = self.frame_index + 5 * dt if self.direction else 0 
        self.image = self.frames[self.state][int(self.frame_index)% len (self.frames[self.state])]

    def update(self, dt) :
        self.input()
        self.move(dt)
        self.animate(dt)

