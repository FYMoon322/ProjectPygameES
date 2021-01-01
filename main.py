import pygame
import os
import sys
import pygame_gui
import math
from copy import deepcopy
import random


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    return image


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dx = target.dx
        target.dx = 0


class Asphalt(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, *groups):
        super().__init__(*groups)
        self.image = load_image(r'Background/Constructions/asphalt.png')
        self.rect = self.image.get_rect().move(
            TILE_WIDTH * pos_x, TILE_HEIGHT * pos_y)


class Hero(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, *groups):
        super().__init__(*groups)
        self.image = load_image(r'Sprites\Semen\Walk (1) — копия.png')
        self.rect = self.image.get_rect().move(pos_x * TILE_WIDTH, pos_y * TILE_HEIGHT - self.image.get_width() // 2)
        self.lower_bound = 200
        self.upper_bound = 600
        self.vx = 50
        self.vy = 0
        self.dx = 0

    def update(self, *args, **kwargs):
        keys = pygame.key.get_pressed()

        # Проверка на пересечение
        bounds1 = pygame.sprite.spritecollide(self, bound_group, False)

        # Отбор спрайтов которые пересекаются по маске
        bounds = []
        for sprite in bounds1:
            if sprite is None:
                continue
            coord = pygame.sprite.collide_mask(sprite, self)
            if coord:
                print(*coord)
                bounds.append((sprite, *coord))
        print()

        # Проверка куда можно пойти
        GoLeft, GoRight, GoUp, GoDown = True, True, True, True
        x2, y2, w2, h2 = self.rect.x, self.rect.y, self.rect.w, self.rect.h
        for sprite, x, y in bounds:
            x1, y1, w1, h1 = sprite.rect.x, sprite.rect.y, sprite.rect.w, sprite.rect.h
            if y1 + h1 >= y2 > y1 and (min(x1, x2) <= max(x1, x2) <= min(x1 + w1, x2 + w2) or
                                       max(x1, x2) <= min(x1 + w1, x2 + w2) <= max(x1 + w1, x2 + w2)) and \
                    (x != 0 and x != TILE_WIDTH - 1):
                GoUp = False
            if y2 + h2 >= y1 > y2 and (min(x1, x2) <= max(x1, x2) <= min(x1 + w1, x2 + w2) or
                                       max(x1, x2) <= min(x1 + w1, x2 + w2) <= max(x1 + w1, x2 + w2)) and \
                    (x != 0 and x != TILE_WIDTH - 1):
                GoDown = False
            if x2 + w2 >= x1 > x2 and (min(y1, y2) <= max(y1, y2) <= min(y1 + h1, y2 + h2) or
                                       max(y1, y2) <= min(y1 + h1, y2 + h2) <= max(y1 + h1, y2 + h2)) and \
                    (y != 0 and y != TILE_HEIGHT - 1):
                GoRight = False
            if x1 + w1 >= x2 > x1 and (min(y1, y2) <= max(y1, y2) <= min(y1 + h1, y2 + h2) or
                                       max(y1, y2) <= min(y1 + h1, y2 + h2) <= max(y1 + h1, y2 + h2)) and \
                    (y != 0 and y != TILE_HEIGHT - 1):
                GoLeft = False

        # Передвижение
        if keys[pygame.K_RIGHT]:
            if GoRight:
                self.rect.x += math.ceil(self.vx / FPS)
        if keys[pygame.K_LEFT]:
            if GoLeft:
                self.rect.x -= math.ceil(self.vx / FPS)
        if keys[pygame.K_UP]:
            if not GoDown:
                self.vy = 150

        if self.vy > 0:
            if not GoUp:
                self.vy = 0
            else:
                self.rect.y -= math.ceil(self.vy / FPS)
                self.vy -= 1

        if GoDown and self.vy <= 0:
            self.vy = -10
            self.rect.y += math.ceil(abs(self.vy) / FPS)
        elif not GoDown and self.vy == -10:
            self.vy = 0

        self.check_bounds()

    def check_bounds(self):
        self.dx = max(min(self.upper_bound - self.rect.x, 0),
                      max(self.lower_bound - self.rect.x, -1))


class BackGround(pygame.sprite.Sprite):
    def __init__(self, pos_x, *groups):
        super().__init__(*groups)
        self.image = load_image(r'Background\city_background_sunset — копия.png')
        self.rect = self.image.get_rect().move(pos_x, 0)


def generate_level(level, hero_groups, asphalt_groups):
    hero, pos_x, pos_y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == 'a':
                Asphalt(x, y, *asphalt_groups)
            if level[y][x] == 'H':
                hero = Hero(x, y, *hero_groups)
                pos_x, pos_y = x, y
    return hero, pos_x, pos_y


def terminate():
    pygame.quit()
    sys.exit()


def confirm_exit():
    pygame_gui.windows.UIConfirmationDialog(
        rect=pygame.Rect((250, 250), (500, 200)),
        manager=UIManager,
        window_title='Подтверждение',
        action_long_desc='Вы действительно хотите таскать мешки с сахаром?',
        action_short_name='Да!',
        blocking=True
    )


def show_credits_and_exit():
    """Показ титров с последующим выходом из игры"""


def end_screen():
    pass


def move_background(bg_first, bg_second):
    """Перемещение заднего фона"""
    img_width = bg_first.rect.width
    bg_first.rect.x %= -img_width
    bg_second.rect.x %= img_width


def play_game():  # TODO Сделать игру:D ага *****; за буквами следи;
    # TODO Пацагы меня не хватит мне срочно нужен супермаркет. Мое сердечко так страдает. Мне нужен супермаркет. Вита, Виталиночка.
    """Запуск игры (игрового цикла)"""

    camera = Camera()
    bg_first, bg_second = BackGround(-4000, all_sprites), BackGround(0, all_sprites)
    hero, hero_pos_x, hero_pos_y = generate_level(load_level('Levels/test_level1.txt'),
                                                  (all_sprites, hero_group),
                                                  (bound_group, all_sprites))

    running_game = True
    while running_game:
        for event_game in pygame.event.get():
            if event_game.type == pygame.QUIT or (event_game.type == pygame.KEYDOWN and
                                                  event_game.key == pygame.K_ESCAPE):
                running_game = False

        hero_group.update(event)
        camera.update(hero)
        # обновляем положение всех спрайтов
        for sprite in all_sprites:
            camera.apply(sprite)

        # Движение BackGround`а (бесконечный фон)
        move_background(bg_first, bg_second)

        screen.fill((0, 0, 0))
        all_sprites.draw(screen)
        hero_group.draw(screen)
        pygame.display.flip()

    return


if __name__ == '__main__':
    # Инициализация
    pygame.init()
    SIZE = WIDTH, HEIGHT = 800, 600
    FPS = 60
    screen = pygame.display.set_mode(SIZE)

    pygame.display.set_caption('Everlasting Mario')
    pygame.display.set_icon(load_image(r'Sprites\Semen\Idle (7).png'))

    # Константы для позиционирования объктов
    TILE_WIDTH, TILE_HEIGHT = 50, 50

    # Создаём менеджер интерфейса с темой для красивого отображения элементов
    UIManager = pygame_gui.UIManager(SIZE, 'base_theme.json')
    # Создаём кнопки
    start_game_btn = pygame_gui.elements.UIButton(
        relative_rect=pygame.rect.Rect((500, 60), (170, 40)),
        text='Начать игру',
        manager=UIManager,
    )
    load_game_btn = pygame_gui.elements.UIButton(
        relative_rect=pygame.rect.Rect((500, 110), (170, 40)),
        text='Загрузить',
        manager=UIManager
    )
    show_achievements_btn = pygame_gui.elements.UIButton(
        relative_rect=pygame.rect.Rect((500, 160), (170, 40)),
        text='Достижения',
        manager=UIManager
    )
    exit_btn = pygame_gui.elements.UIButton(
        relative_rect=pygame.rect.Rect((500, 210), (170, 40)),
        text='Выйти',
        manager=UIManager
    )

    # Фон меню
    image_menu = load_image(r'Background\Menu.jpg')

    running = True

    clock = pygame.time.Clock()

    while running:
        time_delta = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()  # Временно
            #                confirm_exit()
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    running = False
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == start_game_btn:
                        # Создание спарйт-групп
                        bound_group = pygame.sprite.Group()
                        hero_group = pygame.sprite.Group()
                        enemy_group = pygame.sprite.Group()
                        whero_group = pygame.sprite.Group()
                        all_sprites = pygame.sprite.Group()

                        play_game()
                    if event.ui_element == load_game_btn:
                        """Загружаем сохранения"""  # TODO сделать сохранения
                    if event.ui_element == show_achievements_btn:
                        """Показываем достижения"""  # TODO сделать ачивки
                    if event.ui_element == exit_btn:
                        confirm_exit()

            UIManager.process_events(event)

        UIManager.update(time_delta)
        screen.blit(image_menu, (0, 0))
        UIManager.draw_ui(screen)
        pygame.display.flip()

    terminate()
