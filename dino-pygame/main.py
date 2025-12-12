import pygame
import os
import random
import sys

# Initialize Pygame
pygame.init()

# =============================================================================
# CONFIGURATION
# =============================================================================

# Display Settings
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Physics Constants (tuned for good gameplay feel)
GRAVITY = 0.6
INITIAL_JUMP_VELOCITY = -13
DROP_VELOCITY = -5
SPEED_DROP_COEFFICIENT = 3

# Game Speed Settings
INITIAL_SPEED = 6
MAX_SPEED = 13
ACCELERATION = 0.1

# Cloud Settings
BG_CLOUD_SPEED = 0.2

# =============================================================================
# SETUP
# =============================================================================

# Create display
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
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


# =============================================================================
# GAME CLASSES
# =============================================================================

class Dino:
    """Player-controlled dinosaur character."""
    
    X_POS = 80
    Y_POS = 310
    Y_POS_DUCK = 340
    
    def __init__(self):
        self.duck_img = ASSETS['ducking']
        self.run_img = ASSETS['running']
        self.jump_img = ASSETS['jumping']
        
        # State flags
        self.is_ducking = False
        self.is_running = True
        self.is_jumping = False
        
        # Animation
        self.step_index = 0
        self.image = self.run_img[0]
        self.rect = self.image.get_rect(x=self.X_POS, y=self.Y_POS)
        
        # Jump physics
        self.jump_velocity = 0.0
        self.speed_drop = False
        
    def update(self, keys, dt: float, game_speed: float):
        """Update dinosaur state based on input."""
        # Handle current state animation
        if self.is_ducking:
            self._duck()
        elif self.is_running:
            self._run()
        elif self.is_jumping:
            self._jump(dt)
        
        # Reset animation cycle
        if self.step_index >= 10:
            self.step_index = 0
        
        # Handle jump input
        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_UP]
        
        if jump_pressed and not self.is_jumping:
            self._start_jump(game_speed)
        elif self.is_jumping and not jump_pressed:
            self._end_jump()
        
        # Handle duck/speed-drop input
        if keys[pygame.K_DOWN]:
            if self.is_jumping:
                self._set_speed_drop()
            else:
                self.is_ducking = True
                self.is_running = False
        elif not self.is_jumping:
            self.is_ducking = False
            self.is_running = True
    
    def _start_jump(self, speed: float):
        """Initiate a jump with velocity based on current game speed."""
        self.is_jumping = True
        self.is_ducking = False
        self.is_running = False
        self.jump_velocity = INITIAL_JUMP_VELOCITY - (speed / 10.0)
        self.speed_drop = False
    
    def _end_jump(self):
        """Allow early jump termination for variable jump height."""
        if self.jump_velocity < DROP_VELOCITY:
            self.jump_velocity = DROP_VELOCITY
    
    def _set_speed_drop(self):
        """Activate fast-fall during jump."""
        if not self.speed_drop:
            self.speed_drop = True
            self.jump_velocity = 1
    
    def _jump(self, dt: float):
        """Update jump physics."""
        self.image = self.jump_img
        
        # Apply velocity with optional speed drop multiplier
        multiplier = SPEED_DROP_COEFFICIENT if self.speed_drop else 1
        self.rect.y += round(self.jump_velocity * dt * multiplier)
        
        # Apply gravity
        self.jump_velocity += GRAVITY * dt
        
        # Check for landing
        if self.rect.y >= self.Y_POS:
            self.rect.y = self.Y_POS
            self.is_jumping = False
            self.is_running = True
            self.jump_velocity = 0
            self.speed_drop = False
    
    def _run(self):
        """Update running animation."""
        frame = self.step_index // 5
        self.image = self.run_img[frame]
        self.rect = self.image.get_rect(x=self.X_POS, y=self.Y_POS)
        self.step_index += 1
    
    def _duck(self):
        """Update ducking animation."""
        frame = self.step_index // 5
        self.image = self.duck_img[frame]
        self.rect = self.image.get_rect(x=self.X_POS, y=self.Y_POS_DUCK)
        self.step_index += 1
    
    def draw(self, screen: pygame.Surface):
        """Draw the dinosaur to the screen."""
        screen.blit(self.image, self.rect)
    
    def get_hitbox(self) -> pygame.Rect:
        """Get a slightly smaller collision box for fair gameplay."""
        return self.rect.inflate(
            -int(self.rect.width * 0.4),
            -int(self.rect.height * 0.3)
        )


class Cloud:
    """Background cloud decoration."""
    
    def __init__(self):
        self.image = ASSETS['cloud']
        self.width = self.image.get_width()
        self.x = SCREEN_WIDTH + random.randint(800, 1000)
        self.y = random.randint(50, 100)
    
    def update(self, speed: float, dt: float):
        """Move cloud and respawn when off-screen."""
        self.x -= speed * BG_CLOUD_SPEED * dt
        if self.x < -self.width:
            self.x = SCREEN_WIDTH + random.randint(2500, 3000)
            self.y = random.randint(50, 100)
    
    def draw(self, screen: pygame.Surface):
        """Draw the cloud."""
        screen.blit(self.image, (self.x, self.y))


class Obstacle:
    """Base class for obstacles."""
    
    def __init__(self, images: list, type_idx: int, y_pos: int):
        self.images = images
        self.type_idx = type_idx
        self.image = images[type_idx]
        self.rect = self.image.get_rect(x=SCREEN_WIDTH, y=y_pos)
        self.speed_offset = 0.0
    
    def update(self, speed: float, dt: float):
        """Move obstacle left."""
        self.rect.x -= (speed + self.speed_offset) * dt
    
    def draw(self, screen: pygame.Surface):
        """Draw the obstacle."""
        screen.blit(self.image, self.rect)
    
    def get_hitbox(self) -> pygame.Rect:
        """Get collision box."""
        return self.rect.inflate(
            -int(self.rect.width * 0.3),
            -int(self.rect.height * 0.2)
        )
    
    def is_off_screen(self) -> bool:
        """Check if obstacle has left the screen."""
        return self.rect.right < 0


class SmallCactus(Obstacle):
    """Small cactus obstacle."""
    
    def __init__(self):
        super().__init__(
            ASSETS['small_cactus'],
            random.randint(0, 2),
            y_pos=325
        )


class LargeCactus(Obstacle):
    """Large cactus obstacle."""
    
    def __init__(self):
        super().__init__(
            ASSETS['large_cactus'],
            random.randint(0, 2),
            y_pos=300
        )


class Bird(Obstacle):
    """Flying pterodactyl obstacle with animation."""
    
    # Height levels: High (safe), Medium (duck), Low (jump)
    HEIGHT_LEVELS = [250, 270, 320]
    
    def __init__(self):
        y_pos = random.choice(self.HEIGHT_LEVELS)
        super().__init__(ASSETS['bird'], 0, y_pos)
        self.anim_index = 0
        self.speed_offset = 0.8  # Birds move slightly faster
    
    def draw(self, screen: pygame.Surface):
        """Draw with wing animation."""
        frame = self.anim_index // 5
        screen.blit(self.images[frame], self.rect)
        self.anim_index = (self.anim_index + 1) % 10


class Game:
    """Main game manager class."""
    
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font('freesansbold.ttf', 20)
        self.large_font = pygame.font.Font('freesansbold.ttf', 30)
        self.bg_image = ASSETS['background']
        self.bg_width = self.bg_image.get_width()
        
        self.running = True
        self.state = "MENU"
        
        self._reset()
    
    def _reset(self):
        """Reset game state for new game."""
        self.player = Dino()
        self.cloud = Cloud()
        self.obstacles = []
        self.game_speed = INITIAL_SPEED
        self.score = 0.0
        self.bg_x = 0
    
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
            elif event.type == pygame.KEYDOWN:
                if self.state in ("MENU", "GAMEOVER"):
                    self._reset()
                    self.state = "PLAYING"
    
    def _update(self):
        """Update game state."""
        if self.state != "PLAYING":
            return
        
        dt = 1.0  # Fixed timestep for consistent physics
        keys = pygame.key.get_pressed()
        
        # Update entities
        self.player.update(keys, dt, self.game_speed)
        self.cloud.update(self.game_speed, dt)
        
        # Update background
        self.bg_x -= self.game_speed * dt
        if self.bg_x <= -self.bg_width:
            self.bg_x = 0
        
        # Spawn obstacles
        if not self.obstacles:
            self._spawn_obstacle()
        
        # Update obstacles
        for obstacle in self.obstacles[:]:
            obstacle.update(self.game_speed, dt)
            
            if self.player.get_hitbox().colliderect(obstacle.get_hitbox()):
                self.state = "GAMEOVER"
                return
            
            if obstacle.is_off_screen():
                self.obstacles.remove(obstacle)
        
        # Update score and speed
        self.score += 0.1
        if int(self.score) % 100 == 0 and int(self.score) > 0:
            if self.game_speed < MAX_SPEED:
                self.game_speed += ACCELERATION
    
    def _spawn_obstacle(self):
        """Spawn a random obstacle."""
        choice = random.randint(0, 2)
        if choice == 0:
            self.obstacles.append(SmallCactus())
        elif choice == 1:
            self.obstacles.append(LargeCactus())
        else:
            self.obstacles.append(Bird())
    
    def _draw(self):
        """Render the current frame."""
        SCREEN.fill(WHITE)
        
        if self.state == "PLAYING":
            self._draw_game()
        elif self.state == "MENU":
            self._draw_menu("Press Any Key to Start")
        elif self.state == "GAMEOVER":
            self._draw_menu("Press Any Key to Restart", show_score=True)
        
        pygame.display.flip()
    
    def _draw_game(self):
        """Draw the main game screen."""
        # Background (scrolling)
        SCREEN.blit(self.bg_image, (self.bg_x, 380))
        SCREEN.blit(self.bg_image, (self.bg_x + self.bg_width, 380))
        
        # Cloud
        self.cloud.draw(SCREEN)
        
        # Obstacles
        for obstacle in self.obstacles:
            obstacle.draw(SCREEN)
        
        # Player
        self.player.draw(SCREEN)
        
        # Score
        score_text = self.font.render(f"Score: {int(self.score)}", True, BLACK)
        SCREEN.blit(score_text, (SCREEN_WIDTH - 150, 40))
    
    def _draw_menu(self, message: str, show_score: bool = False):
        """Draw menu screen."""
        # Title/Message
        text = self.large_font.render(message, True, BLACK)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        SCREEN.blit(text, text_rect)
        
        # Dino icon
        dino_img = ASSETS['running'][0]
        SCREEN.blit(dino_img, (SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 - 140))
        
        # Score (on game over)
        if show_score:
            score_text = self.font.render(f"Your Score: {int(self.score)}", True, BLACK)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            SCREEN.blit(score_text, score_rect)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    game = Game()
    game.run()
