# main.py (UPDATED)
from settings import *
from player import Player
from sprite import *
from random import randint, choice
from pytmx.util_pygame import load_pygame
from groups import AllSprites
import random

class Game:
    def __init__(self):
        # Setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Alagad: Conquest of Philippines Mythical Creatures")
        self.clock = pygame.time.Clock()
        self.running = True

        # Game State
        self.state = MENU

        # #Groups Sprite
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        # Gun timer
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 100

        # Ammo / Reload
        self.max_ammo = 100
        self.ammo = self.max_ammo
        self.is_reloading = False
        self.reload_start_time = 0
        self.reload_duration = 1000  # milliseconds

        # Enemy Timer
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 300)
        self.spawn_positions = []

        # Audios
        self.shoot_sound = pygame.mixer.Sound(join('audio','shoot.wav'))
        self.shoot_sound.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(join('audio','impact.ogg'))
        self.impact_sound.set_volume (0.2)
        self.music = pygame.mixer.Sound(join('audio','music.wav'))
        self.music.set_volume(1)
        self.music_playing = True
        self.music.play(loops = -1)

        self.death_sound = pygame.mixer.Sound(join('audio','death.wav'))

        # Player HP / Hit cooldown
        self.player_max_hp = 100
        self.player_hp = self.player_max_hp
        self.last_hit_time = 0
        self.invuln_duration = 1000  # ms

        # Kills / difficulty scaling
        self.kills = 0
        self.enemy_speed_bonus = 0  # added to spawned enemies' speed
        self.kills_for_speed = 25
        self.speed_increase_amount = 10

        # Fonts
        self.font = pygame.font.Font(None, 40)
        self.big_font = pygame.font.Font(None, 80)

        # Setup
        self.load_images()
        self.setup()

    def game_over(self):
        font = pygame.font.Font(None, 100)
        text = font.render("GAME OVER", True, (0, 0, 0))
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

        self.display_surface.blit(text, text_rect)
        pygame.display.update()
        pygame.time.delay(3000)  # 3-second delay before quitting

    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images','gun', 'bullet.png')).convert_alpha()

        folders = list(walk (join('images','enemies'))) [0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _ , file_names in walk(join('images','enemies',folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = join (folder_path, file_name)
                    surf = pygame.image.load (full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    def input(self):
        # Shooting with left mouse button
        if pygame.mouse.get_pressed()[0] and self.can_shoot and not self.is_reloading and self.state == GAME_ACTIVE:
            if self.ammo > 0:
                self.shoot_sound.play()
                pos = self.gun.rect.center + self.gun.player_direction * 50
                Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
                self.ammo -= 1
                self.can_shoot = False
                self.shoot_time = pygame.time.get_ticks()
            else:
                # no ammo - maybe play an empty sound (not provided)
                self.can_shoot = False
                self.shoot_time = pygame.time.get_ticks()

        # Reload key
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r] and not self.is_reloading and self.ammo < self.max_ammo and self.state == GAME_ACTIVE:
            self.is_reloading = True
            self.reload_start_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot= True

        # Reload handling
        if self.is_reloading:
            current_time = pygame.time.get_ticks()
            if current_time - self.reload_start_time >= self.reload_duration:
                # finish reload
                self.ammo = self.max_ammo
                self.is_reloading = False

    def setup(self):
        # Ground Tiles
        map = load_pygame(join('data','maps','world.tmx'))
        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE),image,self.all_sprites)

        # Collision Tiles 
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x,obj.y),obj.image,(self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x,obj.y),pygame.Surface((obj.width,obj.height)),self.collision_sprites)

        # Player Spawn and Starting Point
        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player ((obj.x,obj.y), self.all_sprites, self.collision_sprites)
                self.gun = Gun(self.player, self.all_sprites)
            else:
                self.spawn_positions.append((obj.x, obj.y))

    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in list(self.bullet_sprites):
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites,False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        # ensure we count each enemy only once (only if not already dying)
                        if hasattr(sprite, 'death_time') and sprite.death_time == 0:
                            sprite.destroy()
                            self.kills += 1

                            # 50% chance to "drop" bullets (no visual): +10 bullets
                            if random.random() < 0.5:
                                self.ammo = min(self.max_ammo, self.ammo + 10)

                            # every X kills increase enemy speed bonus
                            if self.kills % self.kills_for_speed == 0:
                                self.enemy_speed_bonus += self.speed_increase_amount

                        # kill the bullet after hitting
                        bullet.kill()

    def player_collision(self):
        # check collisions with enemies; apply invulnerability cooldown
        now = pygame.time.get_ticks()
        hits = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask)
        if hits:
            if now - self.last_hit_time >= self.invuln_duration:
                # player takes damage
                self.player_hp -= 10
                self.last_hit_time = now
                # if HP <= 0 -> game over
                if self.player_hp <= 0:
                    self.death_sound.play()
                    self.game_over()
                    self.running = False

    def draw_hud(self):
        # HP Bar (top-left)
        bar_width = 300
        bar_height = 30
        padding = 10
        x = padding
        y = padding
        # background
        pygame.draw.rect(self.display_surface, (50,50,50), (x, y, bar_width, bar_height))
        # foreground
        hp_ratio = max(0, self.player_hp) / self.player_max_hp
        pygame.draw.rect(self.display_surface, (200,20,20), (x, y, bar_width * hp_ratio, bar_height))
        # border
        pygame.draw.rect(self.display_surface, (255,255,255), (x, y, bar_width, bar_height), 2)
        # HP text
        hp_text = self.font.render(f'HP: {max(0, self.player_hp)} / {self.player_max_hp}', True, (255,255,255))
        self.display_surface.blit(hp_text, (x + 8, y + (bar_height - hp_text.get_height()) // 2))

        # Kills (top-right)
        kills_text = self.font.render(f'Kills: {self.kills}', True, (255,255,255))
        kills_x = WINDOW_WIDTH - kills_text.get_width() - padding
        kills_y = padding
        self.display_surface.blit(kills_text, (kills_x, kills_y))

        # Ammo (bottom-right)
        ammo_text = self.font.render(f'Ammo: {self.ammo} / {self.max_ammo}' + (' (Reloading...)' if self.is_reloading else ''), True, (255,255,255))
        ammo_x = WINDOW_WIDTH - ammo_text.get_width() - padding
        ammo_y = WINDOW_HEIGHT - ammo_text.get_height() - padding
        self.display_surface.blit(ammo_text, (ammo_x, ammo_y))

    def draw_menu(self):
        # simple menu UI
        self.display_surface.fill(MENU_BG_COLOR)
        title = self.big_font.render("ALAGAD", True, (255,255,255))
        subtitle = self.font.render("Conquest of Philippines Mythical Creatures", True, (200,200,200))
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 150))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH//2, 220))
        self.display_surface.blit(title, title_rect)
        self.display_surface.blit(subtitle, subtitle_rect)

        # Buttons (Start / Toggle Music / Exit)
        btn_w, btn_h = 300, 60
        spacing = 20
        start_rect = pygame.Rect((WINDOW_WIDTH//2 - btn_w//2, 320), (btn_w, btn_h))
        music_rect = pygame.Rect((WINDOW_WIDTH//2 - btn_w//2, 320 + btn_h + spacing), (btn_w, btn_h))
        exit_rect = pygame.Rect((WINDOW_WIDTH//2 - btn_w//2, 320 + (btn_h + spacing) * 2), (btn_w, btn_h))

        # draw buttons
        pygame.draw.rect(self.display_surface, BUTTON_COLOR, start_rect)
        pygame.draw.rect(self.display_surface, BUTTON_COLOR, music_rect)
        pygame.draw.rect(self.display_surface, BUTTON_COLOR, exit_rect)

        # button labels
        start_txt = self.font.render("START", True, (0,0,0))
        music_txt = self.font.render("TOGGLE MUSIC (On)" if self.music_playing else "TOGGLE MUSIC (Off)", True, (0,0,0))
        exit_txt = self.font.render("EXIT", True, (0,0,0))

        self.display_surface.blit(start_txt, (start_rect.centerx - start_txt.get_width()//2, start_rect.centery - start_txt.get_height()//2))
        self.display_surface.blit(music_txt, (music_rect.centerx - music_txt.get_width()//2, music_rect.centery - music_txt.get_height()//2))
        self.display_surface.blit(exit_txt, (exit_rect.centerx - exit_txt.get_width()//2, exit_rect.centery - exit_txt.get_height()//2))

        return start_rect, music_rect, exit_rect

    def run(self):
        while self.running:
            dt = self.clock.tick() / 1000

            # ----- UNIVERSAL EVENT HANDLING -----
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # ----- MENU STATE -----
            if self.state == MENU:
                self.display_surface.fill(MENU_BG_COLOR)
                start_rect, music_rect, exit_rect = self.draw_menu()

                # Handle menu button clicks
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if start_rect.collidepoint(event.pos):
                            self.state = GAME_ACTIVE
                        elif music_rect.collidepoint(event.pos):
                            if self.music_playing:
                                self.music.stop()
                                self.music_playing = False
                            else:
                                self.music.play(loops=-1)
                                self.music_playing = True
                        elif exit_rect.collidepoint(event.pos):
                            self.running = False

                pygame.display.update()
                continue  # skip game logic this frames

            # ----- GAME ACTIVE STATE -----
            if self.state == GAME_ACTIVE:
                # Enemy spawning
                for event in events:
                    if event.type == self.enemy_event:
                        pos = choice(self.spawn_positions)
                        frames = choice(list(self.enemy_frames.values()))
                        enemy = Enemy(pos, frames, (self.all_sprites, self.enemy_sprites),
                                    self.player, self.collision_sprites)
                        enemy.speed += self.enemy_speed_bonus

                # Gameplay logic
                self.gun_timer()
                self.input()
                self.all_sprites.update(dt)
                self.bullet_collision()
                self.player_collision()

                # Drawing
                self.display_surface.fill('black')
                self.all_sprites.draw(self.player.rect.center)
                self.draw_hud()
                pygame.display.update()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
