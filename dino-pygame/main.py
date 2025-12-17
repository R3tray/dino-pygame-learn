"""
Chrome Dino Clone - Точная копия физики оригинальной игры
"""
import pygame
import random
import math
import os

# Инициализация pygame
pygame.init()
pygame.mixer.init()

# ============================================================================
# КОНСТАНТЫ ИЗ ОРИГИНАЛЬНОЙ ИГРЫ (index.js)
# ============================================================================

FPS = 60
MS_PER_FRAME = 1000 / FPS

# Runner.config
class Config:
    ACCELERATION = 0.001
    BG_CLOUD_SPEED = 0.8
    BOTTOM_PAD = 10
    CLEAR_TIME = 3000  # ms до появления препятствий
    CLOUD_FREQUENCY = 0.5
    GAMEOVER_CLEAR_TIME = 750
    GAP_COEFFICIENT = 0.6
    GRAVITY = 0.6
    INITIAL_JUMP_VELOCITY = 12
    INVERT_FADE_DURATION = 12000
    INVERT_DISTANCE = 700
    MAX_CLOUDS = 6
    MAX_OBSTACLE_LENGTH = 3
    MAX_OBSTACLE_DUPLICATION = 2
    MAX_SPEED = 13
    MIN_JUMP_HEIGHT = 35
    SPEED = 6
    SPEED_DROP_COEFFICIENT = 3

# Runner.defaultDimensions
DEFAULT_WIDTH = 600
DEFAULT_HEIGHT = 150

# Trex.config
class TrexConfig:
    DROP_VELOCITY = -5
    GRAVITY = 0.6
    HEIGHT = 47
    HEIGHT_DUCK = 30  # Пропорционально спрайту
    INITIAL_JUMP_VELOCITY = -10
    INTRO_DURATION = 1500
    MAX_JUMP_HEIGHT = 30
    MIN_JUMP_HEIGHT = 30
    SPEED_DROP_COEFFICIENT = 3
    START_X_POS = 50
    WIDTH = 44
    WIDTH_DUCK = 59

# Цвета
COLOR_BG = (247, 247, 247)  # #f7f7f7
COLOR_BG_NIGHT = (32, 33, 36)  # Тёмно-серый для ночи
COLOR_TEXT = (83, 83, 83)
COLOR_TEXT_NIGHT = (172, 172, 172)

def invert_surface(surface):
    """Инвертирует цвета surface, сохраняя альфа-канал (быстрый метод)"""
    # Создаём копию с альфа-каналом
    inv = surface.copy()
    
    # Получаем размеры
    w, h = inv.get_size()
    
    # Используем pygame.surfarray для быстрой инверсии
    try:
        # Получаем RGB массив (без альфы)
        rgb = pygame.surfarray.pixels3d(inv)
        rgb[:, :, :] = 255 - rgb[:, :, :]
        del rgb
    except:
        # Fallback если surfarray не работает
        pass
    
    return inv

# ============================================================================
# ЗАГРУЗКА РЕСУРСОВ
# ============================================================================

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "Assets")

def load_image(path, target_size=None):
    """Загрузка изображения с опциональным масштабированием до целевого размера"""
    img = pygame.image.load(os.path.join(ASSETS_PATH, path)).convert_alpha()
    if target_size:
        img = pygame.transform.scale(img, target_size)
    return img

def load_image_scaled(path, scale=0.5):
    """Загрузка изображения с масштабированием по коэффициенту"""
    img = pygame.image.load(os.path.join(ASSETS_PATH, path)).convert_alpha()
    new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
    img = pygame.transform.scale(img, new_size)
    return img

class Assets:
    """Контейнер для всех игровых ресурсов"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance
    
    def load(self):
        if self._loaded:
            return
        
        # Дино спрайты - масштабируем до оригинальных размеров Chrome
        # Оригинал: 44x47, duck: 59x25
        self.dino_run = [
            load_image("Dino/DinoRun1.png", (44, 47)),
            load_image("Dino/DinoRun2.png", (44, 47))
        ]
        self.dino_duck = [
            load_image("Dino/DinoDuck1.png", (59, 30)),  # Сохраняем пропорции спрайта
            load_image("Dino/DinoDuck2.png", (59, 30))
        ]
        self.dino_jump = load_image("Dino/DinoJump.png", (44, 47))
        self.dino_dead = load_image("Dino/DinoDead.png", (44, 47))
        self.dino_start = load_image("Dino/DinoStart.png", (44, 47))
        
        # Препятствия - масштабируем пропорционально до оригинальной высоты
        # SmallCactus: оригинал высота 35, LargeCactus: высота 50
        self.small_cactus = [
            load_image("Cactus/SmallCactus1.png", (17, 35)),
            load_image("Cactus/SmallCactus2.png", (34, 35)),
            load_image("Cactus/SmallCactus3.png", (51, 35))
        ]
        self.large_cactus = [
            load_image("Cactus/LargeCactus1.png", (25, 50)),
            load_image("Cactus/LargeCactus2.png", (50, 50)),
            load_image("Cactus/LargeCactus3.png", (75, 50))
        ]
        # Bird: оригинал 46x40
        self.bird = [
            load_image("Bird/Bird1.png", (46, 40)),
            load_image("Bird/Bird2.png", (46, 40))
        ]
        
        # Окружение
        # Cloud: оригинал 46x14
        self.cloud = load_image("Other/Cloud.png", (46, 27))  # Пропорционально
        # Track: оригинал 600x12
        self.track = load_image("Other/Track.png", (1200, 12))
        # UI
        self.game_over = load_image("Other/GameOver.png", (191, 11))
        self.reset = load_image("Other/Reset.png", (36, 32))
        
        # Создаём инвертированные версии для ночного режима
        self._create_inverted_sprites()
        
        self._loaded = True
    
    def _create_inverted_sprites(self):
        """Создание инвертированных версий спрайтов для ночного режима"""
        self.dino_run_inv = [invert_surface(s) for s in self.dino_run]
        self.dino_duck_inv = [invert_surface(s) for s in self.dino_duck]
        self.dino_jump_inv = invert_surface(self.dino_jump)
        self.dino_dead_inv = invert_surface(self.dino_dead)
        self.dino_start_inv = invert_surface(self.dino_start)
        
        self.small_cactus_inv = [invert_surface(s) for s in self.small_cactus]
        self.large_cactus_inv = [invert_surface(s) for s in self.large_cactus]
        self.bird_inv = [invert_surface(s) for s in self.bird]
        
        self.cloud_inv = invert_surface(self.cloud)
        self.track_inv = invert_surface(self.track)
        self.reset_inv = invert_surface(self.reset)

# ============================================================================
# COLLISION BOX
# ============================================================================

class CollisionBox:
    """Collision box для детальной проверки столкновений"""
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

def box_compare(box1, box2):
    """AABB проверка столкновения двух боксов"""
    return (box1.x < box2.x + box2.width and
            box1.x + box1.width > box2.x and
            box1.y < box2.y + box2.height and
            box1.y + box1.height > box2.y)

def create_adjusted_collision_box(box, adjustment):
    """Создание скорректированного collision box"""
    return CollisionBox(
        box.x + adjustment.x,
        box.y + adjustment.y,
        box.width,
        box.height
    )

# ============================================================================
# TREX (ДИНО)
# ============================================================================

class Trex:
    """T-Rex персонаж с точной физикой из оригинала"""
    
    # Collision boxes из оригинала
    COLLISION_BOXES_RUNNING = [
        CollisionBox(22, 0, 17, 16),
        CollisionBox(1, 18, 30, 9),
        CollisionBox(10, 35, 14, 8),
        CollisionBox(1, 24, 29, 5),
        CollisionBox(5, 30, 21, 4),
        CollisionBox(9, 34, 15, 4)
    ]
    
    COLLISION_BOXES_DUCKING = [
        CollisionBox(1, 18, 55, 25)
    ]
    
    # Анимация
    BLINK_TIMING = 7000
    
    class Status:
        CRASHED = 'CRASHED'
        DUCKING = 'DUCKING'
        JUMPING = 'JUMPING'
        RUNNING = 'RUNNING'
        WAITING = 'WAITING'
    
    def __init__(self, assets):
        self.assets = assets
        self.x_pos = 0
        self.y_pos = 0
        self.ground_y_pos = 0
        
        self.current_frame = 0
        self.blink_delay = 0
        self.blink_count = 0
        self.anim_start_time = 0
        self.timer = 0
        self.ms_per_frame = MS_PER_FRAME
        
        self.config = TrexConfig()
        self.status = self.Status.WAITING
        
        self.jumping = False
        self.ducking = False
        self.jump_velocity = 0
        self.reached_min_height = False
        self.speed_drop = False
        self.jump_count = 0
        
        self.playing_intro = False
        
        self.init()
    
    def init(self):
        """Инициализация позиции"""
        self.ground_y_pos = DEFAULT_HEIGHT - self.config.HEIGHT - Config.BOTTOM_PAD
        self.y_pos = self.ground_y_pos
        self.min_jump_height = self.ground_y_pos - self.config.MIN_JUMP_HEIGHT
        self.x_pos = self.config.START_X_POS
    
    def set_blink_delay(self):
        """Установка случайной задержки моргания"""
        self.blink_delay = random.randint(1, self.BLINK_TIMING)
    
    def start_jump(self, speed):
        """Начало прыжка"""
        if not self.jumping:
            self.status = self.Status.JUMPING
            self.current_frame = 0
            # Корректировка скорости прыжка на основе текущей скорости игры
            self.jump_velocity = self.config.INITIAL_JUMP_VELOCITY - (speed / 10)
            self.jumping = True
            self.reached_min_height = False
            self.speed_drop = False
    
    def end_jump(self):
        """Завершение прыжка (отпускание клавиши)"""
        if self.reached_min_height and self.jump_velocity < self.config.DROP_VELOCITY:
            self.jump_velocity = self.config.DROP_VELOCITY
    
    def update_jump(self, delta_time):
        """Обновление прыжка - точная формула из оригинала"""
        ms_per_frame = MS_PER_FRAME  # 1000/60
        frames_elapsed = delta_time / ms_per_frame
        
        # Speed drop увеличивает скорость падения
        if self.speed_drop:
            self.y_pos += self.jump_velocity * self.config.SPEED_DROP_COEFFICIENT * frames_elapsed
        else:
            self.y_pos += self.jump_velocity * frames_elapsed
        
        self.jump_velocity += self.config.GRAVITY * frames_elapsed
        
        # Достигнута минимальная высота прыжка
        if self.y_pos < self.min_jump_height or self.speed_drop:
            self.reached_min_height = True
        
        # Достигнута максимальная высота
        if self.y_pos < self.config.MAX_JUMP_HEIGHT or self.speed_drop:
            self.end_jump()
        
        # Приземление
        if self.y_pos > self.ground_y_pos:
            was_speed_drop = self.speed_drop
            self.reset()
            self.jump_count += 1
            
            if was_speed_drop:
                self.set_duck(True)
    
    def set_speed_drop(self):
        """Быстрое падение при нажатии вниз в воздухе"""
        self.speed_drop = True
        self.jump_velocity = 1
    
    def set_duck(self, is_ducking):
        """Включение/выключение приседания"""
        if is_ducking and self.status != self.Status.DUCKING:
            self.status = self.Status.DUCKING
            self.current_frame = 0
            self.ducking = True
        elif self.status == self.Status.DUCKING:
            self.status = self.Status.RUNNING
            self.current_frame = 0
            self.ducking = False
    
    def reset(self):
        """Сброс в состояние бега"""
        self.y_pos = self.ground_y_pos
        self.jump_velocity = 0
        self.jumping = False
        self.ducking = False
        self.status = self.Status.RUNNING
        self.speed_drop = False
        self.jump_count = 0
    
    def update(self, delta_time, opt_status=None):
        """Обновление состояния дино"""
        self.timer += delta_time
        
        if opt_status:
            self.status = opt_status
            self.current_frame = 0
            
            if opt_status == self.Status.WAITING:
                self.anim_start_time = pygame.time.get_ticks()
                self.set_blink_delay()
        
        # Анимация
        anim_speed = {
            self.Status.WAITING: 1000 / 3,
            self.Status.RUNNING: 1000 / 12,
            self.Status.CRASHED: 1000 / 60,
            self.Status.JUMPING: 1000 / 60,
            self.Status.DUCKING: 1000 / 8
        }
        
        ms_per_frame = anim_speed.get(self.status, MS_PER_FRAME)
        
        if self.timer >= ms_per_frame:
            if self.status == self.Status.RUNNING:
                self.current_frame = (self.current_frame + 1) % 2
            elif self.status == self.Status.DUCKING:
                self.current_frame = (self.current_frame + 1) % 2
            self.timer = 0
    
    def draw(self, surface, inverted=False):
        """Отрисовка дино"""
        if self.status == self.Status.CRASHED:
            img = self.assets.dino_dead_inv if inverted else self.assets.dino_dead
        elif self.status == self.Status.JUMPING:
            img = self.assets.dino_jump_inv if inverted else self.assets.dino_jump
        elif self.status == self.Status.DUCKING:
            imgs = self.assets.dino_duck_inv if inverted else self.assets.dino_duck
            img = imgs[self.current_frame]
        elif self.status == self.Status.WAITING:
            img = self.assets.dino_start_inv if inverted else self.assets.dino_start
        else:  # RUNNING
            imgs = self.assets.dino_run_inv if inverted else self.assets.dino_run
            img = imgs[self.current_frame]
        
        # Корректировка Y для duck спрайта
        y_offset = 0
        if self.ducking and self.status != self.Status.CRASHED:
            y_offset = self.config.HEIGHT - self.config.HEIGHT_DUCK
        
        surface.blit(img, (self.x_pos, self.y_pos + y_offset))
    
    def get_collision_boxes(self):
        """Получение collision boxes для текущего состояния"""
        if self.ducking:
            return self.COLLISION_BOXES_DUCKING
        return self.COLLISION_BOXES_RUNNING

# ============================================================================
# ПРЕПЯТСТВИЯ
# ============================================================================

class ObstacleType:
    """Конфигурация типа препятствия"""
    def __init__(self, name, width, height, y_pos, multiple_speed, min_gap, 
                 min_speed, collision_boxes, num_frames=0, frame_rate=0, speed_offset=0):
        self.name = name
        self.width = width
        self.height = height
        self.y_pos = y_pos  # может быть числом или списком
        self.multiple_speed = multiple_speed
        self.min_gap = min_gap
        self.min_speed = min_speed
        self.collision_boxes = collision_boxes
        self.num_frames = num_frames
        self.frame_rate = frame_rate
        self.speed_offset = speed_offset

# Типы препятствий из оригинала
OBSTACLE_TYPES = [
    ObstacleType(
        name='CACTUS_SMALL',
        width=17,
        height=35,
        y_pos=105,
        multiple_speed=4,
        min_gap=120,
        min_speed=0,
        collision_boxes=[
            CollisionBox(0, 7, 5, 27),
            CollisionBox(4, 0, 6, 34),
            CollisionBox(10, 4, 7, 14)
        ]
    ),
    ObstacleType(
        name='CACTUS_LARGE',
        width=25,
        height=50,
        y_pos=90,
        multiple_speed=7,
        min_gap=120,
        min_speed=0,
        collision_boxes=[
            CollisionBox(0, 12, 7, 38),
            CollisionBox(8, 0, 7, 49),
            CollisionBox(13, 10, 10, 38)
        ]
    ),
    ObstacleType(
        name='PTERODACTYL',
        width=46,
        height=40,
        y_pos=[100, 75, 50],  # Разные высоты
        multiple_speed=999,
        min_speed=8.5,
        min_gap=150,
        collision_boxes=[
            CollisionBox(15, 15, 16, 5),
            CollisionBox(18, 21, 24, 6),
            CollisionBox(2, 14, 4, 3),
            CollisionBox(6, 10, 4, 7),
            CollisionBox(10, 8, 6, 9)
        ],
        num_frames=2,
        frame_rate=1000 / 6,
        speed_offset=0.8
    )
]

MAX_GAP_COEFFICIENT = 1.5

class Obstacle:
    """Препятствие"""
    
    def __init__(self, assets, type_config, dimensions, gap_coefficient, speed, opt_x_offset=0):
        self.assets = assets
        self.type_config = type_config
        self.gap_coefficient = gap_coefficient
        self.size = random.randint(1, Config.MAX_OBSTACLE_LENGTH)
        self.dimensions = dimensions
        self.remove = False
        self.x_pos = dimensions['WIDTH'] + opt_x_offset
        self.y_pos = 0
        self.width = 0
        self.collision_boxes = []
        self.gap = 0
        self.speed_offset = 0
        
        self.current_frame = 0
        self.timer = 0
        
        self.following_obstacle_created = False
        
        self.init(speed)
    
    def init(self, speed):
        """Инициализация препятствия"""
        # Клонируем collision boxes
        self.collision_boxes = [
            CollisionBox(cb.x, cb.y, cb.width, cb.height) 
            for cb in self.type_config.collision_boxes
        ]
        
        # Размер группы только при достаточной скорости
        if self.size > 1 and self.type_config.multiple_speed > speed:
            self.size = 1
        
        self.width = self.type_config.width * self.size
        
        # Y позиция (случайная для птеродактиля)
        if isinstance(self.type_config.y_pos, list):
            self.y_pos = random.choice(self.type_config.y_pos)
        else:
            self.y_pos = self.type_config.y_pos
        
        # Корректировка collision boxes для групп
        if self.size > 1 and len(self.collision_boxes) >= 3:
            self.collision_boxes[1].width = (self.width - 
                                             self.collision_boxes[0].width - 
                                             self.collision_boxes[2].width)
            self.collision_boxes[2].x = self.width - self.collision_boxes[2].width
        
        # Случайное смещение скорости для птеродактиля
        if self.type_config.speed_offset:
            self.speed_offset = (self.type_config.speed_offset if random.random() > 0.5 
                                else -self.type_config.speed_offset)
        
        self.gap = self.get_gap(self.gap_coefficient, speed)
    
    def get_gap(self, gap_coefficient, speed):
        """Расчёт промежутка до следующего препятствия"""
        min_gap = round(self.width * speed + self.type_config.min_gap * gap_coefficient)
        max_gap = round(min_gap * MAX_GAP_COEFFICIENT)
        return random.randint(min_gap, max_gap)
    
    def update(self, delta_time, speed):
        """Обновление позиции препятствия"""
        if not self.remove:
            actual_speed = speed + self.speed_offset if self.type_config.speed_offset else speed
            self.x_pos -= (actual_speed * FPS / 1000) * delta_time
            
            # Анимация (для птеродактиля)
            if self.type_config.num_frames:
                self.timer += delta_time
                if self.timer >= self.type_config.frame_rate:
                    self.current_frame = (self.current_frame + 1) % self.type_config.num_frames
                    self.timer = 0
            
            if not self.is_visible():
                self.remove = True
    
    def is_visible(self):
        """Проверка видимости на экране"""
        return self.x_pos + self.width > 0
    
    def draw(self, surface, inverted=False):
        """Отрисовка препятствия"""
        if self.type_config.name == 'CACTUS_SMALL':
            imgs = self.assets.small_cactus_inv if inverted else self.assets.small_cactus
            img = imgs[min(self.size - 1, len(imgs) - 1)]
            surface.blit(img, (self.x_pos, self.y_pos))
        elif self.type_config.name == 'CACTUS_LARGE':
            imgs = self.assets.large_cactus_inv if inverted else self.assets.large_cactus
            img = imgs[min(self.size - 1, len(imgs) - 1)]
            surface.blit(img, (self.x_pos, self.y_pos))
        elif self.type_config.name == 'PTERODACTYL':
            imgs = self.assets.bird_inv if inverted else self.assets.bird
            img = imgs[self.current_frame]
            surface.blit(img, (self.x_pos, self.y_pos))

# ============================================================================
# ОБЛАКА
# ============================================================================

class Cloud:
    """Облако на фоне"""
    
    WIDTH = 46
    HEIGHT = 27  # Пропорционально масштабированный спрайт
    MIN_CLOUD_GAP = 100
    MAX_CLOUD_GAP = 400
    MIN_SKY_LEVEL = 71
    MAX_SKY_LEVEL = 30
    
    def __init__(self, assets, container_width):
        self.assets = assets
        self.container_width = container_width
        self.x_pos = container_width
        self.y_pos = random.randint(self.MAX_SKY_LEVEL, self.MIN_SKY_LEVEL)
        self.remove = False
        self.cloud_gap = random.randint(self.MIN_CLOUD_GAP, self.MAX_CLOUD_GAP)
    
    def update(self, speed):
        """Обновление позиции облака"""
        if not self.remove:
            self.x_pos -= speed
            if not self.is_visible():
                self.remove = True
    
    def is_visible(self):
        return self.x_pos + self.WIDTH > 0
    
    def draw(self, surface, inverted=False):
        img = self.assets.cloud_inv if inverted else self.assets.cloud
        surface.blit(img, (self.x_pos, self.y_pos))

# ============================================================================
# НОЧНОЙ РЕЖИМ
# ============================================================================

class NightMode:
    """Ночной режим с луной и звёздами"""
    
    FADE_SPEED = 0.035
    NUM_STARS = 2
    STAR_SIZE = 9
    STAR_SPEED = 0.3
    STAR_MAX_Y = 70
    MOON_SPEED = 0.25
    
    def __init__(self, container_width):
        self.container_width = container_width
        self.x_pos = container_width - 50
        self.y_pos = 30
        self.current_phase = 0
        self.opacity = 0
        self.stars = []
        self.draw_stars = False
        self.place_stars()
        
        # Оптимизация: создаём поверхность один раз
        self.night_surface = pygame.Surface((self.container_width, DEFAULT_HEIGHT), pygame.SRCALPHA)
    
    def place_stars(self):
        """Размещение звёзд"""
        segment_size = self.container_width // self.NUM_STARS
        self.stars = []
        for i in range(self.NUM_STARS):
            self.stars.append({
                'x': random.randint(segment_size * i, segment_size * (i + 1)),
                'y': random.randint(0, self.STAR_MAX_Y)
            })
    
    def update(self, activated):
        """Обновление ночного режима"""
        # Смена фазы луны при активации
        if activated and self.opacity == 0:
            self.current_phase = (self.current_phase + 1) % 7
        
        # Fade in/out
        if activated and self.opacity < 1:
            self.opacity = min(1, self.opacity + self.FADE_SPEED)
        elif not activated and self.opacity > 0:
            self.opacity = max(0, self.opacity - self.FADE_SPEED)
        
        # Движение луны и звёзд
        if self.opacity > 0:
            self.x_pos = self.update_x_pos(self.x_pos, self.MOON_SPEED)
            
            if self.draw_stars:
                for star in self.stars:
                    star['x'] = self.update_x_pos(star['x'], self.STAR_SPEED)
            
            self.draw_stars = True
        else:
            self.place_stars()
    
    def update_x_pos(self, current_pos, speed):
        """Обновление X позиции с циклом"""
        if current_pos < -20:
            return self.container_width
        return current_pos - speed
    
    def draw(self, surface):
        """Отрисовка ночного неба"""
        if self.opacity <= 0:
            return
        
        # Очистка поверхности (прозрачный цвет)
        self.night_surface.fill((0, 0, 0, 0))
        
        # Звёзды
        if self.draw_stars:
            star_color = (255, 255, 255, int(255 * self.opacity))
            for star in self.stars:
                pygame.draw.circle(self.night_surface, star_color, 
                                 (int(star['x']), star['y']), 2)
        
        # Луна (простой круг)
        moon_color = (255, 255, 255, int(255 * self.opacity))
        pygame.draw.circle(self.night_surface, moon_color, 
                          (int(self.x_pos), self.y_pos), 10)
        
        surface.blit(self.night_surface, (0, 0))
    
    def reset(self):
        self.current_phase = 0
        self.opacity = 0

# ============================================================================
# HORIZON LINE (ЗЕМЛЯ)
# ============================================================================

class HorizonLine:
    """Линия горизонта/земля"""
    
    HEIGHT = 12
    YPOS = 127
    
    def __init__(self, assets):
        self.assets = assets
        self.track_width = assets.track.get_width()
        self.x_pos = 0
        self.y_pos = self.YPOS
    
    def update(self, delta_time, speed):
        """Обновление позиции земли"""
        increment = speed * (FPS / 1000) * delta_time
        self.x_pos -= increment
        
        # Циклическое перемещение
        if self.x_pos <= -self.track_width:
            self.x_pos += self.track_width
    
    def draw(self, surface, inverted=False):
        """Отрисовка земли - рисуем столько сегментов, сколько нужно"""
        track = self.assets.track_inv if inverted else self.assets.track
        
        # Начинаем с текущей позиции и рисуем пока не покроем экран
        x = self.x_pos
        while x < DEFAULT_WIDTH:
            surface.blit(track, (x, self.y_pos))
            x += self.track_width
    
    def reset(self):
        self.x_pos = 0

# ============================================================================
# HORIZON (ФОН)
# ============================================================================

class Horizon:
    """Управление фоном: земля, облака, препятствия"""
    
    def __init__(self, assets, dimensions, gap_coefficient):
        self.assets = assets
        self.dimensions = dimensions
        self.gap_coefficient = gap_coefficient
        
        self.obstacles = []
        self.obstacle_history = []
        self.clouds = []
        self.cloud_frequency = Config.CLOUD_FREQUENCY
        self.cloud_speed = Config.BG_CLOUD_SPEED
        
        self.horizon_line = HorizonLine(assets)
        self.night_mode = NightMode(dimensions['WIDTH'])
        
        self.running_time = 0
        
        # Добавляем начальное облако
        self.add_cloud()
    
    def add_cloud(self):
        """Добавление нового облака"""
        self.clouds.append(Cloud(self.assets, self.dimensions['WIDTH']))
    
    def update_clouds(self, delta_time, speed):
        """Обновление облаков"""
        cloud_speed = self.cloud_speed / 1000 * delta_time * speed
        
        if self.clouds:
            for cloud in self.clouds:
                cloud.update(cloud_speed)
            
            last_cloud = self.clouds[-1]
            
            # Добавление нового облака
            if (len(self.clouds) < Config.MAX_CLOUDS and
                (self.dimensions['WIDTH'] - last_cloud.x_pos) > last_cloud.cloud_gap and
                self.cloud_frequency > random.random()):
                self.add_cloud()
            
            # Удаление невидимых облаков
            self.clouds = [c for c in self.clouds if not c.remove]
        else:
            self.add_cloud()
    
    def add_new_obstacle(self, speed):
        """Добавление нового препятствия"""
        # Выбираем случайный тип
        obstacle_type_index = random.randint(0, len(OBSTACLE_TYPES) - 1)
        obstacle_type = OBSTACLE_TYPES[obstacle_type_index]
        
        # Проверка дупликатов и минимальной скорости
        if (self.duplicate_obstacle_check(obstacle_type.name) or
            speed < obstacle_type.min_speed):
            self.add_new_obstacle(speed)
            return
        
        obstacle = Obstacle(
            self.assets, 
            obstacle_type, 
            self.dimensions,
            self.gap_coefficient, 
            speed, 
            obstacle_type.width
        )
        self.obstacles.append(obstacle)
        self.obstacle_history.insert(0, obstacle_type.name)
        
        if len(self.obstacle_history) > 1:
            self.obstacle_history = self.obstacle_history[:Config.MAX_OBSTACLE_DUPLICATION]
    
    def duplicate_obstacle_check(self, next_type):
        """Проверка на слишком частое повторение типа препятствия"""
        duplicate_count = 0
        for obs_type in self.obstacle_history:
            if obs_type == next_type:
                duplicate_count += 1
            else:
                duplicate_count = 0
        return duplicate_count >= Config.MAX_OBSTACLE_DUPLICATION
    
    def update_obstacles(self, delta_time, speed):
        """Обновление препятствий"""
        for obstacle in self.obstacles:
            obstacle.update(delta_time, speed)
        
        # Удаление невидимых
        self.obstacles = [o for o in self.obstacles if not o.remove]
        
        if self.obstacles:
            last_obstacle = self.obstacles[-1]
            
            if (last_obstacle and 
                not last_obstacle.following_obstacle_created and
                last_obstacle.is_visible() and
                (last_obstacle.x_pos + last_obstacle.width + last_obstacle.gap) < 
                 self.dimensions['WIDTH']):
                self.add_new_obstacle(speed)
                last_obstacle.following_obstacle_created = True
        else:
            self.add_new_obstacle(speed)
    
    def update(self, delta_time, speed, update_obstacles, show_night_mode):
        """Обновление всего горизонта"""
        self.running_time += delta_time
        self.horizon_line.update(delta_time, speed)
        self.night_mode.update(show_night_mode)
        self.update_clouds(delta_time, speed)
        
        if update_obstacles:
            self.update_obstacles(delta_time, speed)
    
    def draw(self, surface, inverted=False):
        """Отрисовка горизонта"""
        # Облака (на заднем плане)
        for cloud in self.clouds:
            cloud.draw(surface, inverted)
        
        # Ночное небо (только в ночном режиме)
        if inverted:
            self.night_mode.draw(surface)
        
        # Земля
        self.horizon_line.draw(surface, inverted)
        
        # Препятствия
        for obstacle in self.obstacles:
            obstacle.draw(surface, inverted)
    
    def reset(self):
        """Сброс горизонта"""
        self.obstacles = []
        self.obstacle_history = []
        self.horizon_line.reset()
        self.night_mode.reset()

# ============================================================================
# DISTANCE METER (СЧЁТ)
# ============================================================================

class DistanceMeter:
    """Счётчик дистанции/очков"""
    
    COEFFICIENT = 0.025  # Конвертация пикселей в очки
    ACHIEVEMENT_DISTANCE = 100
    FLASH_DURATION = 250  # мс
    FLASH_ITERATIONS = 3
    
    def __init__(self, width):
        self.x = width - 70
        self.y = 5
        self.current_distance = 0
        self.max_score = 99999
        self.high_score = 0
        self.achievement = False
        self.flash_timer = 0
        self.flash_iterations = 0
        
        # Шрифт
        self.font = pygame.font.Font(None, 24)
    
    def get_actual_distance(self, distance):
        """Конвертация пикселей в очки"""
        return round(distance * self.COEFFICIENT) if distance else 0
    
    def update(self, delta_time, distance):
        """Обновление счётчика"""
        play_sound = False
        paint = True
        
        if not self.achievement:
            actual_distance = self.get_actual_distance(distance)
            
            if actual_distance > 0 and actual_distance % self.ACHIEVEMENT_DISTANCE == 0:
                self.achievement = True
                self.flash_timer = 0
                play_sound = True
            
            self.current_distance = actual_distance
        else:
            if self.flash_iterations <= self.FLASH_ITERATIONS:
                self.flash_timer += delta_time
                
                if self.flash_timer < self.FLASH_DURATION:
                    paint = False
                elif self.flash_timer > self.FLASH_DURATION * 2:
                    self.flash_timer = 0
                    self.flash_iterations += 1
            else:
                self.achievement = False
                self.flash_iterations = 0
                self.flash_timer = 0
        
        return play_sound, paint
    
    def set_high_score(self, distance):
        """Установка рекорда"""
        self.high_score = self.get_actual_distance(distance)
    
    def draw(self, surface, paint=True, inverted=False):
        """Отрисовка счётчика"""
        text_color = COLOR_TEXT_NIGHT if inverted else COLOR_TEXT
        
        if paint:
            # Текущий счёт
            score_text = str(self.current_distance).zfill(5)
            text_surface = self.font.render(score_text, True, text_color)
            surface.blit(text_surface, (self.x, self.y))
        
        # High score
        if self.high_score > 0:
            hi_text = f"HI {str(self.high_score).zfill(5)}"
            hi_surface = self.font.render(hi_text, True, text_color)
            hi_surface.set_alpha(200)
            surface.blit(hi_surface, (self.x - 100, self.y))
    
    def reset(self):
        self.current_distance = 0
        self.achievement = False
        self.flash_timer = 0
        self.flash_iterations = 0

# ============================================================================
# GAME OVER PANEL
# ============================================================================

class GameOverPanel:
    """Панель Game Over"""
    
    def __init__(self, assets, dimensions):
        self.assets = assets
        self.dimensions = dimensions
        # Используем шрифт для текста Game Over
        self.font = pygame.font.Font(None, 24)
    
    def draw(self, surface, inverted=False):
        """Отрисовка панели"""
        text_color = COLOR_TEXT_NIGHT if inverted else COLOR_TEXT
        
        # Game Over текст (шрифтом для чёткости)
        text = self.font.render("G A M E   O V E R", True, text_color)
        go_x = (self.dimensions['WIDTH'] - text.get_width()) // 2
        go_y = (self.dimensions['HEIGHT'] - 25) // 3
        surface.blit(text, (go_x, go_y))
        
        # Кнопка рестарта
        reset_img = self.assets.reset_inv if inverted else self.assets.reset
        reset_x = (self.dimensions['WIDTH'] - reset_img.get_width()) // 2
        reset_y = self.dimensions['HEIGHT'] // 2
        surface.blit(reset_img, (reset_x, reset_y))

# ============================================================================
# ПРОВЕРКА СТОЛКНОВЕНИЙ
# ============================================================================

def check_for_collision(obstacle, trex):
    """Проверка столкновения дино с препятствием"""
    # Внешний bounding box дино
    trex_box = CollisionBox(
        trex.x_pos + 1,
        trex.y_pos + 1,
        trex.config.WIDTH - 2,
        trex.config.HEIGHT - 2
    )
    
    # Корректировка для duck
    if trex.ducking:
        trex_box.height = trex.config.HEIGHT_DUCK - 2
        trex_box.y = trex.y_pos + (trex.config.HEIGHT - trex.config.HEIGHT_DUCK) + 1
    
    # Внешний bounding box препятствия
    obstacle_box = CollisionBox(
        obstacle.x_pos + 1,
        obstacle.y_pos + 1,
        obstacle.type_config.width * obstacle.size - 2,
        obstacle.type_config.height - 2
    )
    
    # Грубая проверка
    if box_compare(trex_box, obstacle_box):
        # Детальная проверка с collision boxes
        trex_collision_boxes = trex.get_collision_boxes()
        obstacle_collision_boxes = obstacle.collision_boxes
        
        for t_box in trex_collision_boxes:
            # Абсолютные координаты бокса дино
            t_abs_x = t_box.x + trex_box.x
            t_abs_y = t_box.y + trex_box.y
            
            for o_box in obstacle_collision_boxes:
                # Абсолютные координаты бокса препятствия
                o_abs_x = o_box.x + obstacle_box.x
                o_abs_y = o_box.y + obstacle_box.y
                
                # Проверка пересечения (AABB)
                if (t_abs_x < o_abs_x + o_box.width and
                    t_abs_x + t_box.width > o_abs_x and
                    t_abs_y < o_abs_y + o_box.height and
                    t_abs_y + t_box.height > o_abs_y):
                    return True
    
    return False

# ============================================================================
# ГЛАВНЫЙ КЛАСС ИГРЫ
# ============================================================================

class Game:
    """Главный класс игры"""
    
    def __init__(self):
        # Размеры окна (пропорционально игровому полю 600x150)
        self.window_width = 900
        self.window_height = 225
        
        # Создание окна с поддержкой ресайза
        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height), 
            pygame.RESIZABLE
        )
        pygame.display.set_caption("Dino Runner")
        
        # Игровая поверхность (логическое разрешение)
        self.game_surface = pygame.Surface((DEFAULT_WIDTH, DEFAULT_HEIGHT))
        
        self.clock = pygame.time.Clock()
        
        # Загрузка ресурсов
        self.assets = Assets()
        self.assets.load()
        
        # Состояние игры
        self.dimensions = {'WIDTH': DEFAULT_WIDTH, 'HEIGHT': DEFAULT_HEIGHT}
        self.current_speed = Config.SPEED
        self.distance_ran = 0
        self.highest_score = 0
        self.running_time = 0
        self.time = 0
        
        self.activated = False
        self.playing = False
        self.crashed = False
        self.won = False
        self.paused = False
        self.inverted = False
        self.invert_timer = 0
        self.invert_trigger = False
        
        # Игровые объекты
        self.trex = Trex(self.assets)
        self.horizon = Horizon(self.assets, self.dimensions, Config.GAP_COEFFICIENT)
        self.distance_meter = DistanceMeter(self.dimensions['WIDTH'])
        self.game_over_panel = None
    
    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.VIDEORESIZE:
                self.window_width = event.w
                self.window_height = event.h
                self.screen = pygame.display.set_mode(
                    (self.window_width, self.window_height), 
                    pygame.RESIZABLE
                )
            
            if event.type == pygame.KEYDOWN:
                self.on_key_down(event)
            
            if event.type == pygame.KEYUP:
                self.on_key_up(event)
        
        return True
    
    def on_key_down(self, event):
        """Обработка нажатия клавиши"""
        # Прыжок: пробел или стрелка вверх
        if event.key in (pygame.K_SPACE, pygame.K_UP):
            if not self.crashed and not self.won:
                if not self.playing:
                    self.playing = True
                    self.activated = True
                
                if not self.trex.jumping and not self.trex.ducking:
                    self.trex.start_jump(self.current_speed)
            elif self.crashed or self.won:
                # Рестарт после game over или победы
                self.restart()
        
        # Приседание: стрелка вниз
        if event.key == pygame.K_DOWN:
            if self.playing and not self.crashed and not self.won:
                if self.trex.jumping:
                    self.trex.set_speed_drop()
                elif not self.trex.jumping and not self.trex.ducking:
                    self.trex.set_duck(True)
        
        # Рестарт: Enter
        if event.key == pygame.K_RETURN and (self.crashed or self.won):
            self.restart()

        # Fullscreen: F11
        if event.key == pygame.K_F11:
            if self.screen.get_flags() & pygame.FULLSCREEN:
                self.screen = pygame.display.set_mode(
                    (self.window_width, self.window_height), 
                    pygame.RESIZABLE
                )
            else:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    
    def on_key_up(self, event):
        """Обработка отпускания клавиши"""
        if event.key in (pygame.K_SPACE, pygame.K_UP):
            if self.trex.jumping:
                self.trex.end_jump()
        
        if event.key == pygame.K_DOWN:
            self.trex.speed_drop = False
            self.trex.set_duck(False)
    
    def update(self, delta_time):
        """Обновление игры"""
        if self.playing:
            if self.trex.jumping:
                self.trex.update_jump(delta_time)
            
            self.running_time += delta_time
            has_obstacles = self.running_time > Config.CLEAR_TIME
            
            # Обновление горизонта
            self.horizon.update(delta_time, self.current_speed, has_obstacles, self.inverted)
            
            # Проверка столкновений
            collision = False
            if has_obstacles and self.horizon.obstacles:
                collision = check_for_collision(self.horizon.obstacles[0], self.trex)
            
            if not collision:
                self.distance_ran += self.current_speed * delta_time / MS_PER_FRAME
                
                # Победа на 100000 очков
                if self.distance_meter.get_actual_distance(self.distance_ran) >= 100000:
                    self.victory()
                
                if self.current_speed < Config.MAX_SPEED:
                    self.current_speed += Config.ACCELERATION
            else:
                self.game_over()
            
            # Обновление счётчика
            play_sound, paint = self.distance_meter.update(
                delta_time, 
                math.ceil(self.distance_ran)
            )
            
            # Ночной режим
            if self.invert_timer > Config.INVERT_FADE_DURATION:
                self.invert_timer = 0
                self.invert_trigger = False
                self.invert(reset=False)
            elif self.invert_timer:
                self.invert_timer += delta_time
            else:
                actual_distance = self.distance_meter.get_actual_distance(
                    math.ceil(self.distance_ran)
                )
                if actual_distance > 0:
                    self.invert_trigger = (actual_distance % Config.INVERT_DISTANCE == 0)
                    
                    if self.invert_trigger and self.invert_timer == 0:
                        self.invert_timer += delta_time
                        self.invert(reset=False)
            
            # Обновление дино
            self.trex.update(delta_time)
    
    def invert(self, reset=False):
        """Переключение ночного режима"""
        if reset:
            self.inverted = False
            self.invert_timer = 0
        else:
            self.inverted = not self.inverted if self.invert_trigger else self.inverted
    
    def victory(self):
        """Победа"""
        self.playing = False
        self.won = True
        self.trex.update(100, Trex.Status.WAITING)
        
        if self.distance_ran > self.highest_score:
            self.highest_score = math.ceil(self.distance_ran)
            self.distance_meter.set_high_score(self.highest_score)

    def game_over(self):
        """Game Over"""
        self.playing = False
        self.crashed = True
        self.trex.update(100, Trex.Status.CRASHED)
        
        if not self.game_over_panel:
            self.game_over_panel = GameOverPanel(self.assets, self.dimensions)
        
        if self.distance_ran > self.highest_score:
            self.highest_score = math.ceil(self.distance_ran)
            self.distance_meter.set_high_score(self.highest_score)
    
    def restart(self):
        """Перезапуск игры"""
        self.running_time = 0
        self.playing = True
        self.crashed = False
        self.won = False
        self.distance_ran = 0
        self.current_speed = Config.SPEED
        
        self.distance_meter.reset()
        self.horizon.reset()
        self.trex.reset()
        self.trex.init()
        
        self.invert(reset=True)
    
    def draw(self):
        """Отрисовка игры"""
        # Очистка игровой поверхности
        bg_color = COLOR_BG_NIGHT if self.inverted else COLOR_BG
        self.game_surface.fill(bg_color)
        
        # Отрисовка горизонта
        self.horizon.draw(self.game_surface, self.inverted)
        
        # Отрисовка дино
        self.trex.draw(self.game_surface, self.inverted)
        
        # Отрисовка счёта
        _, paint = self.distance_meter.update(0, math.ceil(self.distance_ran))
        self.distance_meter.draw(self.game_surface, paint, self.inverted)
        
        # Game Over панель
        if self.crashed and self.game_over_panel:
            self.game_over_panel.draw(self.game_surface, self.inverted)
        
        # Victory message
        if self.won:
            font = pygame.font.Font(None, 48)
            text_color = COLOR_TEXT_NIGHT if self.inverted else COLOR_TEXT
            text = font.render("V I C T O R Y !", True, text_color)
            text_rect = text.get_rect(center=(DEFAULT_WIDTH // 2, DEFAULT_HEIGHT // 2))
            self.game_surface.blit(text, text_rect)
        
        # Масштабирование на размер окна с сохранением пропорций
        self.render_to_screen()
    
    def render_to_screen(self):
        """Масштабирование и центрирование игровой поверхности"""
        # Вычисление масштаба с сохранением пропорций
        scale_x = self.window_width / DEFAULT_WIDTH
        scale_y = self.window_height / DEFAULT_HEIGHT
        scale = min(scale_x, scale_y)
        
        # Новые размеры
        new_width = int(DEFAULT_WIDTH * scale)
        new_height = int(DEFAULT_HEIGHT * scale)
        
        # Масштабирование с качественной интерполяцией
        scaled_surface = pygame.transform.scale(self.game_surface, (new_width, new_height))
        
        # Центрирование
        x_offset = (self.window_width - new_width) // 2
        y_offset = (self.window_height - new_height) // 2
        
        # Очистка экрана и отрисовка
        bg_color = (32, 33, 36) if self.inverted else (247, 247, 247)
        self.screen.fill(bg_color)
        self.screen.blit(scaled_surface, (x_offset, y_offset))
        
        pygame.display.flip()
    
    def run(self):
        """Главный игровой цикл"""
        running = True
        
        while running:
            # Delta time в миллисекундах
            delta_time = self.clock.tick(FPS)
            
            # Обработка событий
            running = self.handle_events()
            
            # Обновление
            self.update(delta_time)
            
            # Отрисовка
            self.draw()
        
        pygame.quit()

# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

if __name__ == "__main__":
    game = Game()
    game.run()
