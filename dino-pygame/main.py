import pygame
import os
import random
import sys

# Initialize Pygame
pygame.init()

# =============================================================================
# CONFIGURATION - Matching Pygame asset dimensions with Chrome Dino mechanics
# =============================================================================

# Logical game dimensions (matching Pygame asset scale)
# Original assets are designed for ~1100x600 but we scale proportionally
LOGICAL_WIDTH = 1100
LOGICAL_HEIGHT = 300

# Initial window size (can be resized)
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 300

FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (83, 83, 83)

# Scale factor from Chrome Dino (600x150) to Pygame dimensions (1100x300)
# This allows us to use Chrome's physics values scaled appropriately
SCALE_X = LOGICAL_WIDTH / 600
SCALE_Y = LOGICAL_HEIGHT / 150

# Physics Constants (from original Chrome Dino, scaled to new dimensions)
GRAVITY = 0.6 * SCALE_Y
INITIAL_JUMP_VELOCITY = -10 * SCALE_Y  # Trex.config.INIITAL_JUMP_VELOCITY
DROP_VELOCITY = -5 * SCALE_Y  # INITIAL_JUMP_VELOCITY / 2
SPEED_DROP_COEFFICIENT = 3
MIN_JUMP_HEIGHT = 30 * SCALE_Y  # Minimum height before can end jump early

# Game Speed Settings (from Runner.config, scaled for new width)
INITIAL_SPEED = 6 * SCALE_X
MAX_SPEED = 13 * SCALE_X
ACCELERATION = 0.0001 * SCALE_X

# Speed thresholds for obstacle logic (unscaled, these are game logic values)
PTERODACTYL_MIN_SPEED = 8.5 * SCALE_X
CACTUS_SMALL_MULTI_SPEED = 4 * SCALE_X
CACTUS_LARGE_MULTI_SPEED = 7 * SCALE_X

# Obstacle Settings
GAP_COEFFICIENT = 0.6  # Runner.config.GAP_COEFFICIENT
MAX_GAP_COEFFICIENT = 1.5  # Obstacle.MAX_GAP_COEFFICIENT
MAX_OBSTACLE_LENGTH = 3
MAX_OBSTACLE_DUPLICATION = 2
CLEAR_TIME = 3000  # ms before obstacles start appearing

# Cloud Settings
BG_CLOUD_SPEED = 0.2
CLOUD_FREQUENCY = 0.5
MAX_CLOUDS = 6
MIN_CLOUD_GAP = int(100 * SCALE_X)
MAX_CLOUD_GAP = int(400 * SCALE_X)

# Score Settings
SCORE_COEFFICIENT = 0.025 / SCALE_X  # Distance to score conversion (adjusted for scale)
ACHIEVEMENT_DISTANCE = 100  # Score flashes every 100 points
FLASH_DURATION = 250  # ms
FLASH_ITERATIONS = 3

# Ground position (near bottom of screen)
GROUND_Y = int(LOGICAL_HEIGHT * 0.84)  # ~252 for 300px height
GROUND_VISUAL_OFFSET = 12  # Lift texture up so dino doesn't hover
BOTTOM_PAD = 10

# =============================================================================
# SETUP
# =============================================================================

# Create resizable display
SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Dino Runner")

# Asset directory
ASSET_DIR = "Assets"


def load_image(path: str) -> pygame.Surface:
    """Load and convert an image for optimal performance."""
    img = pygame.image.load(path)
    return img.convert_alpha()


def load_assets():
    """Load all game assets with error handling."""
    try:
        assets = {
            'running': [
                load_image(os.path.join(ASSET_DIR, "Dino", "DinoRun1.png")),
                load_image(os.path.join(ASSET_DIR, "Dino", "DinoRun2.png"))
            ],
            'jumping': load_image(os.path.join(ASSET_DIR, "Dino", "DinoJump.png")),
            'ducking': [
                load_image(os.path.join(ASSET_DIR, "Dino", "DinoDuck1.png")),
                load_image(os.path.join(ASSET_DIR, "Dino", "DinoDuck2.png"))
            ],
            'small_cactus': [
                load_image(os.path.join(ASSET_DIR, "Cactus", "SmallCactus1.png")),
                load_image(os.path.join(ASSET_DIR, "Cactus", "SmallCactus2.png")),
                load_image(os.path.join(ASSET_DIR, "Cactus", "SmallCactus3.png"))
            ],
            'large_cactus': [
                load_image(os.path.join(ASSET_DIR, "Cactus", "LargeCactus1.png")),
                load_image(os.path.join(ASSET_DIR, "Cactus", "LargeCactus2.png")),
                load_image(os.path.join(ASSET_DIR, "Cactus", "LargeCactus3.png"))
            ],
            'bird': [
                load_image(os.path.join(ASSET_DIR, "Bird", "Bird1.png")),
                load_image(os.path.join(ASSET_DIR, "Bird", "Bird2.png"))
            ],
            'cloud': load_image(os.path.join(ASSET_DIR, "Other", "Cloud.png")),
            'background': load_image(os.path.join(ASSET_DIR, "Other", "Track.png"))
        }
        return assets
    except FileNotFoundError as e:
        print(f"Error: Could not load assets - {e}")
        print("Make sure the 'Assets' folder is in the same directory as this script.")
        sys.exit(1)


# Load assets
ASSETS = load_assets()

# Get actual sprite dimensions from loaded assets
DINO_WIDTH = ASSETS['running'][0].get_width()
DINO_HEIGHT = ASSETS['running'][0].get_height()
DUCK_WIDTH = ASSETS['ducking'][0].get_width()
DUCK_HEIGHT = ASSETS['ducking'][0].get_height()
TRACK_WIDTH = ASSETS['background'].get_width()
TRACK_HEIGHT = ASSETS['background'].get_height()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_random_num(min_val: int, max_val: int) -> int:
    """Get random integer in range [min, max]."""
    return random.randint(min_val, max_val)


# =============================================================================
# GAME CLASSES
# =============================================================================

class Dino:
    """Player-controlled dinosaur character."""
    
    X_POS = int(50 * SCALE_X)  # Starting x position
    
    def __init__(self):
        self.duck_img = ASSETS['ducking']
        self.run_img = ASSETS['running']
        self.jump_img = ASSETS['jumping']
        
        # Use actual sprite dimensions
        self.width = DINO_WIDTH
        self.height = DINO_HEIGHT
        self.duck_height = DUCK_HEIGHT
        self.duck_width = DUCK_WIDTH
        
        # Calculate ground Y position (dino feet at ground level)
        self.ground_y = GROUND_Y - self.height
        self.min_jump_height = self.ground_y - MIN_JUMP_HEIGHT
        
        # State flags
        self.is_ducking = False
        self.is_running = True
        self.is_jumping = False
        
        # Animation
        self.step_index = 0
        self.image = self.run_img[0]
        self.x = self.X_POS
        self.y = self.ground_y
        
        # Jump physics
        self.jump_velocity = 0.0
        self.speed_drop = False
        self.reached_min_height = False
        self.jump_count = 0
        
    def update(self, keys, delta_time: float, game_speed: float):
        """Update dinosaur state based on input."""
        ms_per_frame = 1000 / FPS
        frames_elapsed = delta_time / ms_per_frame
        
        # Handle current state animation
        if self.is_jumping:
            self._update_jump(delta_time)
        elif self.is_ducking:
            self._duck()
        else:
            self._run()
        
        # Handle jump input
        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_UP]
        
        if jump_pressed and not self.is_jumping and not self.is_ducking:
            self._start_jump(game_speed)
        elif self.is_jumping and not jump_pressed:
            self._end_jump()
        
        # Handle duck/speed-drop input
        if keys[pygame.K_DOWN]:
            if self.is_jumping:
                self._set_speed_drop()
            elif not self.is_jumping:
                self.is_ducking = True
                self.is_running = False
        elif not self.is_jumping:
            self.is_ducking = False
            self.is_running = True
        
        # Speed drop becomes duck if on ground with down held
        if self.speed_drop and self.y >= self.ground_y:
            self.speed_drop = False
            if keys[pygame.K_DOWN]:
                self.is_ducking = True
                self.is_running = False
    
    def _start_jump(self, speed: float):
        """Initiate a jump with velocity based on current game speed."""
        self.is_jumping = True
        self.is_ducking = False
        self.is_running = False
        # Tweak jump velocity based on speed (original behavior)
        self.jump_velocity = INITIAL_JUMP_VELOCITY - (speed / 10)
        self.speed_drop = False
        self.reached_min_height = False
    
    def _end_jump(self):
        """Allow early jump termination for variable jump height."""
        if self.reached_min_height and self.jump_velocity < DROP_VELOCITY:
            self.jump_velocity = DROP_VELOCITY
    
    def _set_speed_drop(self):
        """Activate fast-fall during jump."""
        if not self.speed_drop:
            self.speed_drop = True
            self.jump_velocity = 1  # Immediate downward
    
    def _update_jump(self, delta_time: float):
        """Update jump physics (matches original Trex.updateJump)."""
        self.image = self.jump_img
        
        ms_per_frame = 1000 / FPS
        frames_elapsed = delta_time / ms_per_frame
        
        # Speed drop makes Trex fall faster
        if self.speed_drop:
            self.y += round(self.jump_velocity * SPEED_DROP_COEFFICIENT * frames_elapsed)
        else:
            self.y += round(self.jump_velocity * frames_elapsed)
        
        # Apply gravity
        self.jump_velocity += GRAVITY * frames_elapsed
        
        # Minimum height reached check
        if self.y < self.min_jump_height or self.speed_drop:
            self.reached_min_height = True
        
        # Check for landing
        if self.y >= self.ground_y:
            self.y = self.ground_y
            self.is_jumping = False
            self.is_running = True
            self.jump_velocity = 0
            self.speed_drop = False
            self.reached_min_height = False
            self.jump_count += 1
    
    def _run(self):
        """Update running animation."""
        frame = (self.step_index // 5) % 2
        self.image = self.run_img[frame]
        self.step_index += 1
    
    def _duck(self):
        """Update ducking animation."""
        frame = (self.step_index // 5) % 2
        self.image = self.duck_img[frame]
        self.step_index += 1
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle."""
        if self.is_ducking:
            return pygame.Rect(self.x, GROUND_Y - self.duck_height, 
                             self.duck_width, self.duck_height)
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_hitbox(self) -> pygame.Rect:
        """Get a slightly smaller collision box for fair gameplay."""
        rect = self.get_rect()
        return rect.inflate(-int(rect.width * 0.3), -int(rect.height * 0.2))
    
    def reset(self):
        """Reset to initial state."""
        self.y = self.ground_y
        self.jump_velocity = 0
        self.is_jumping = False
        self.is_ducking = False
        self.is_running = True
        self.speed_drop = False
        self.reached_min_height = False
        self.jump_count = 0
        self.step_index = 0


class Cloud:
    """Background cloud decoration."""
    
    def __init__(self):
        self.image = ASSETS['cloud']
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.x = LOGICAL_WIDTH + get_random_num(0, int(100 * SCALE_X))
        # Clouds in upper portion of sky
        self.y = get_random_num(int(30 * SCALE_Y), int(90 * SCALE_Y))
        self.cloud_gap = get_random_num(MIN_CLOUD_GAP, MAX_CLOUD_GAP)
        self.remove = False
    
    def update(self, speed: float):
        """Move cloud left."""
        self.x -= speed
        if self.x + self.width < 0:
            self.remove = True
    
    def is_visible(self) -> bool:
        return self.x + self.width > 0


class Obstacle:
    """Base class for obstacles with original gap/spawning logic."""
    
    def __init__(self, obstacle_type: str, game_speed: float):
        self.type = obstacle_type
        
        # Get images based on type
        if obstacle_type == 'CACTUS_SMALL':
            self.images = ASSETS['small_cactus']
            self.multiple_speed = CACTUS_SMALL_MULTI_SPEED
            self.min_gap = int(120 * SCALE_X)
            self.min_speed = 0
        elif obstacle_type == 'CACTUS_LARGE':
            self.images = ASSETS['large_cactus']
            self.multiple_speed = CACTUS_LARGE_MULTI_SPEED
            self.min_gap = int(120 * SCALE_X)
            self.min_speed = 0
        else:  # PTERODACTYL
            self.images = ASSETS['bird']
            self.multiple_speed = 999  # Never groups
            self.min_gap = int(150 * SCALE_X)
            self.min_speed = PTERODACTYL_MIN_SPEED
        
        # Get single sprite dimensions
        self.single_width = self.images[0].get_width()
        self.single_height = self.images[0].get_height()
        
        # Determine size (grouping for cacti)
        self.size = get_random_num(1, MAX_OBSTACLE_LENGTH)
        if self.size > 1 and self.multiple_speed > game_speed:
            self.size = 1
        if obstacle_type == 'PTERODACTYL':
            self.size = 1  # Birds never group
        
        self.width = self.single_width * self.size
        self.height = self.single_height
        
        # Y position
        if obstacle_type == 'PTERODACTYL':
            # Variable height for birds
            heights = [GROUND_Y - self.height - int(h * SCALE_Y) for h in [0, 50, 100]]
            self.y = random.choice(heights)
        else:
            # Cacti on ground
            self.y = GROUND_Y - self.height
        
        self.x = LOGICAL_WIDTH
        
        # Speed offset for birds (makes them slightly faster/slower)
        self.speed_offset = 0
        if obstacle_type == 'PTERODACTYL':
            offset = 0.8 * SCALE_X
            self.speed_offset = offset if random.random() > 0.5 else -offset
        
        # Calculate gap until next obstacle
        self.gap = self._get_gap(GAP_COEFFICIENT, game_speed)
        
        self.following_obstacle_created = False
        self.remove = False
        
        # Animation for pterodactyl
        self.current_frame = 0
        self.anim_timer = 0
        self.frame_rate = 1000 / 6  # ~166ms per frame
    
    def _get_gap(self, gap_coefficient: float, speed: float) -> float:
        """Calculate gap to next obstacle (matches original)."""
        min_gap = round(self.width * speed + self.min_gap * gap_coefficient)
        max_gap = round(min_gap * MAX_GAP_COEFFICIENT)
        return get_random_num(min_gap, max_gap)
    
    def update(self, delta_time: float, speed: float):
        """Move obstacle left."""
        if not self.remove:
            actual_speed = speed + self.speed_offset
            # Original: xPos -= Math.floor((speed * FPS / 1000) * deltaTime)
            self.x -= (actual_speed * FPS / 1000) * delta_time
            
            # Update animation frame for pterodactyl
            if self.type == 'PTERODACTYL':
                self.anim_timer += delta_time
                if self.anim_timer >= self.frame_rate:
                    self.current_frame = (self.current_frame + 1) % len(self.images)
                    self.anim_timer = 0
            
            if not self.is_visible():
                self.remove = True
    
    def is_visible(self) -> bool:
        return self.x + self.width > 0
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_hitbox(self) -> pygame.Rect:
        """Get collision box."""
        rect = self.get_rect()
        return rect.inflate(-int(rect.width * 0.2), -int(rect.height * 0.15))


class DistanceMeter:
    """Handles score display with high score and flashing."""
    
    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.achievement = False
        self.flash_timer = 0
        self.flash_iterations = 0
        self.max_score_units = 5
        
    def update(self, delta_time: float, distance: float) -> bool:
        """Update score, returns True if achievement sound should play."""
        play_sound = False
        actual_distance = round(distance * SCORE_COEFFICIENT) if distance else 0
        
        if not self.achievement:
            self.score = actual_distance
            
            if actual_distance > 0 and actual_distance % ACHIEVEMENT_DISTANCE == 0:
                self.achievement = True
                self.flash_timer = 0
                self.flash_iterations = 0
                play_sound = True
        else:
            self.flash_timer += delta_time
            if self.flash_timer > FLASH_DURATION * 2:
                self.flash_timer = 0
                self.flash_iterations += 1
            
            if self.flash_iterations >= FLASH_ITERATIONS:
                self.achievement = False
                self.flash_iterations = 0
        
        return play_sound
    
    def should_draw(self) -> bool:
        """Whether to draw score (for flashing effect)."""
        if not self.achievement:
            return True
        return self.flash_timer >= FLASH_DURATION
    
    def set_high_score(self, distance: float):
        """Update high score."""
        actual = round(distance * SCORE_COEFFICIENT)
        if actual > self.high_score:
            self.high_score = actual
    
    def reset(self):
        """Reset score but keep high score."""
        self.score = 0
        self.achievement = False
        self.flash_timer = 0
        self.flash_iterations = 0


class Game:
    """Main game manager class with arcade mode scaling."""
    
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font('freesansbold.ttf', 20)
        self.large_font = pygame.font.Font('freesansbold.ttf', 32)
        self.bg_image = ASSETS['background']
        
        # Create logical surface for game rendering
        self.game_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
        
        self.running = True
        self.state = "MENU"
        self.window_width = WINDOW_WIDTH
        self.window_height = WINDOW_HEIGHT
        
        self._reset()
    
    def _reset(self):
        """Reset game state for new game."""
        self.player = Dino()
        self.clouds = [Cloud()]
        self.obstacles = []
        self.obstacle_history = []
        self.game_speed = INITIAL_SPEED
        self.distance_ran = 0.0
        self.running_time = 0.0
        self.bg_x = 0
        self.distance_meter = DistanceMeter()
        self.time = pygame.time.get_ticks()
    
    def run(self):
        """Main game loop."""
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(FPS)
        
        pygame.quit()
    
    def _handle_events(self):
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.window_width = event.w
                self.window_height = event.h
            elif event.type == pygame.KEYDOWN:
                if self.state in ("MENU", "GAMEOVER"):
                    if self.state == "GAMEOVER":
                        self.distance_meter.set_high_score(self.distance_ran)
                    self._reset()
                    self.state = "PLAYING"
    
    def _update(self):
        """Update game state."""
        if self.state != "PLAYING":
            return
        
        # Calculate delta time in milliseconds
        now = pygame.time.get_ticks()
        delta_time = now - self.time
        self.time = now
        
        # Cap delta time to prevent large jumps
        delta_time = min(delta_time, 100)
        
        keys = pygame.key.get_pressed()
        
        # Update running time
        self.running_time += delta_time
        has_obstacles = self.running_time > CLEAR_TIME
        
        # Update player
        self.player.update(keys, delta_time, self.game_speed)
        
        # Update clouds
        self._update_clouds(delta_time)
        
        # Update background (scrolling ground)
        bg_increment = (self.game_speed * FPS / 1000) * delta_time
        self.bg_x -= bg_increment
        bg_width = TRACK_WIDTH
        if self.bg_x <= -bg_width:
            self.bg_x += bg_width
        
        # Update obstacles
        if has_obstacles:
            self._update_obstacles(delta_time)
        
        # Check collisions
        for obstacle in self.obstacles:
            if self.player.get_hitbox().colliderect(obstacle.get_hitbox()):
                self.distance_meter.set_high_score(self.distance_ran)
                self.state = "GAMEOVER"
                return
        
        # Update distance and speed
        self.distance_ran += self.game_speed * delta_time / (1000 / FPS)
        
        if self.game_speed < MAX_SPEED:
            self.game_speed += ACCELERATION * delta_time
        
        # Update score
        self.distance_meter.update(delta_time, self.distance_ran)
    
    def _update_clouds(self, delta_time: float):
        """Update cloud positions."""
        cloud_speed = BG_CLOUD_SPEED / 1000 * delta_time * self.game_speed
        
        for cloud in self.clouds[:]:
            cloud.update(cloud_speed)
            if cloud.remove:
                self.clouds.remove(cloud)
        
        # Add new clouds
        if self.clouds:
            last_cloud = self.clouds[-1]
            if (len(self.clouds) < MAX_CLOUDS and 
                (LOGICAL_WIDTH - last_cloud.x) > last_cloud.cloud_gap and
                random.random() < CLOUD_FREQUENCY):
                self.clouds.append(Cloud())
        else:
            self.clouds.append(Cloud())
    
    def _update_obstacles(self, delta_time: float):
        """Update obstacle positions with proper gap/spawning."""
        # Update existing obstacles
        for obstacle in self.obstacles[:]:
            obstacle.update(delta_time, self.game_speed)
            if obstacle.remove:
                self.obstacles.remove(obstacle)
        
        # Check if we need to spawn new obstacle
        if self.obstacles:
            last_obstacle = self.obstacles[-1]
            if (not last_obstacle.following_obstacle_created and
                last_obstacle.is_visible() and
                (last_obstacle.x + last_obstacle.width + last_obstacle.gap) < LOGICAL_WIDTH):
                self._add_new_obstacle()
                last_obstacle.following_obstacle_created = True
        else:
            self._add_new_obstacle()
    
    def _add_new_obstacle(self):
        """Add a new obstacle with duplication check."""
        obstacle_types = ['CACTUS_SMALL', 'CACTUS_LARGE', 'PTERODACTYL']
        
        for _ in range(10):  # Max attempts to find valid type
            type_name = random.choice(obstacle_types)
            
            # Check speed requirement for pterodactyl
            if type_name == 'PTERODACTYL' and self.game_speed < PTERODACTYL_MIN_SPEED:
                continue
            
            # Check duplication
            if self._is_duplicate(type_name):
                continue
            
            # Valid obstacle type found
            obstacle = Obstacle(type_name, self.game_speed)
            self.obstacles.append(obstacle)
            
            # Track history
            self.obstacle_history.insert(0, type_name)
            if len(self.obstacle_history) > MAX_OBSTACLE_DUPLICATION:
                self.obstacle_history = self.obstacle_history[:MAX_OBSTACLE_DUPLICATION]
            
            return
        
        # Fallback: spawn small cactus if all else fails
        obstacle = Obstacle('CACTUS_SMALL', self.game_speed)
        self.obstacles.append(obstacle)
    
    def _is_duplicate(self, obstacle_type: str) -> bool:
        """Check if obstacle type would be too many duplicates in a row."""
        if len(self.obstacle_history) < MAX_OBSTACLE_DUPLICATION:
            return False
        return all(t == obstacle_type for t in self.obstacle_history[:MAX_OBSTACLE_DUPLICATION])
    
    def _draw(self):
        """Render the current frame with arcade mode scaling."""
        # Clear game surface
        self.game_surface.fill(WHITE)
        
        if self.state == "PLAYING":
            self._draw_game()
        elif self.state == "MENU":
            self._draw_menu("Press Any Key to Start")
        elif self.state == "GAMEOVER":
            self._draw_game()  # Show final game state
            self._draw_menu("Game Over", show_score=True)
        
        # Scale game surface to window (arcade mode)
        self._scale_to_window()
        
        pygame.display.flip()
    
    def _draw_game(self):
        """Draw the main game screen to logical surface."""
        # Background (scrolling ground)
        bg_y = GROUND_Y - GROUND_VISUAL_OFFSET
        self.game_surface.blit(self.bg_image, (self.bg_x, bg_y))
        self.game_surface.blit(self.bg_image, (self.bg_x + TRACK_WIDTH, bg_y))
        
        # Clouds
        for cloud in self.clouds:
            self.game_surface.blit(cloud.image, (cloud.x, cloud.y))
        
        # Obstacles
        for obstacle in self.obstacles:
            self._draw_obstacle(obstacle)
        
        # Player
        self._draw_player()
        
        # Score
        self._draw_score()
    
    def _draw_obstacle(self, obstacle: Obstacle):
        """Draw obstacle with proper sizing for groups."""
        if obstacle.type == 'PTERODACTYL':
            img = obstacle.images[obstacle.current_frame]
            self.game_surface.blit(img, (obstacle.x, obstacle.y))
        else:
            # Draw grouped cacti
            for i in range(obstacle.size):
                img_idx = i % len(obstacle.images)
                x = obstacle.x + i * obstacle.single_width
                self.game_surface.blit(obstacle.images[img_idx], (x, obstacle.y))
    
    def _draw_player(self):
        """Draw the player dinosaur."""
        if self.player.is_ducking:
            img = self.player.duck_img[(self.player.step_index // 5) % 2]
            y = GROUND_Y - self.player.duck_height
            self.game_surface.blit(img, (self.player.x, y))
        else:
            self.game_surface.blit(self.player.image, (self.player.x, self.player.y))
    
    def _draw_score(self):
        """Draw score and high score."""
        if not self.distance_meter.should_draw():
            return
        
        # Current score
        score_str = str(self.distance_meter.score).zfill(5)
        score_text = self.font.render(score_str, True, GRAY)
        score_x = LOGICAL_WIDTH - score_text.get_width() - 20
        self.game_surface.blit(score_text, (score_x, 10))
        
        # High score
        if self.distance_meter.high_score > 0:
            hi_str = "HI " + str(self.distance_meter.high_score).zfill(5)
            hi_text = self.font.render(hi_str, True, GRAY)
            hi_x = score_x - hi_text.get_width() - 30
            self.game_surface.blit(hi_text, (hi_x, 10))
    
    def _draw_menu(self, message: str, show_score: bool = False):
        """Draw menu screen overlay."""
        # Semi-transparent overlay for game over
        if show_score:
            overlay = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 200))
            self.game_surface.blit(overlay, (0, 0))
        
        # Message
        text = self.large_font.render(message, True, GRAY)
        text_rect = text.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2))
        self.game_surface.blit(text, text_rect)
        
        # Dino icon
        dino_img = ASSETS['running'][0]
        dino_x = LOGICAL_WIDTH // 2 - dino_img.get_width() // 2
        dino_y = LOGICAL_HEIGHT // 2 - dino_img.get_height() - 30
        self.game_surface.blit(dino_img, (dino_x, dino_y))
        
        # Score on game over
        if show_score:
            score_text = self.font.render(f"Score: {self.distance_meter.score}", True, GRAY)
            score_rect = score_text.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 35))
            self.game_surface.blit(score_text, score_rect)
    
    def _scale_to_window(self):
        """Scale game surface to fit window (arcade mode)."""
        # Calculate scale to fit while maintaining aspect ratio
        scale_x = self.window_width / LOGICAL_WIDTH
        scale_y = self.window_height / LOGICAL_HEIGHT
        scale = min(scale_x, scale_y)
        
        # Calculate scaled dimensions
        scaled_width = int(LOGICAL_WIDTH * scale)
        scaled_height = int(LOGICAL_HEIGHT * scale)
        
        # Center in window
        x = (self.window_width - scaled_width) // 2
        y = (self.window_height - scaled_height) // 2
        
        # Clear screen and draw scaled game
        SCREEN.fill(WHITE)
        scaled_surface = pygame.transform.scale(self.game_surface, (scaled_width, scaled_height))
        SCREEN.blit(scaled_surface, (x, y))


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    game = Game()
    game.run()
