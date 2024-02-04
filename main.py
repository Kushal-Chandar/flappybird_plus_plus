from collections import deque
import random
import time
import pygame

# game
pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("flappybird")
clock = pygame.time.Clock()
framerate = 144

game_start = False
prestart_speed = 0.2
prestart_flip_time = 2000  # slowly move up and down when idle
start_delay_ms = 100
GAMESTART_EVENT = pygame.USEREVENT + 1
start_event_triggered = False
BIRD_DIE_EVENT = False
score_font = pygame.font.Font(None, 44)


score = 0
best_score = 0

retry_screen_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
retry_screen_surf = pygame.Surface((screen.get_width() / 3, screen.get_height() / 3))


# world
distance_scaler = 155  # 1 meter = 155 pixels
gravity = 9.8

ground = 100
skybox = -100
cut_off_line_top = 100
cut_off_line_bottom = screen.get_height() - 150 - ground
cut_off_line_top_pos = pygame.Vector2(0, cut_off_line_top)
cut_off_line_top_surf = pygame.Surface((screen.get_width(), 5))
cut_off_line_bottom_pos = pygame.Vector2(0, cut_off_line_bottom)
cut_off_line_bottom_surf = pygame.Surface((screen.get_width(), 5))
cut_off_line_ground_pos = pygame.Vector2(0, screen.get_height() - ground)
cut_off_line_ground_surf = pygame.Surface((screen.get_width(), 5))

# player
h = 0.27 * distance_scaler
cube_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
cube_surf = pygame.Surface((h, h))

flap_time = 0.4
flap_cooldown = 0.2 * 1000
flap = False
last_flap = pygame.time.get_ticks()

u = 0
a = 10
min_bird_acc = 2
bird_acc = a
max_bird_acc = 15

# rectangle
gap = 1.1
rectangle_width = 0.75
rect_surf = pygame.Surface((rectangle_width * distance_scaler, screen.get_height()))
spawn_width_offset = 500  # pixels
spawn_location_x = screen.get_width() + spawn_width_offset
spawn_time = 3 * 1000
rectangle_queue = deque(maxlen=20)
last_rect_spawn = pygame.time.get_ticks()
rectangle_cut_off_top = 100
rectangle_cut_off_bottom = int(
    screen.get_height() - 100 - ground - (gap * distance_scaler)
)
rectangle_cut_off_top_pos = pygame.Vector2(0, rectangle_cut_off_top)
rectangle_cut_off_top_surf = pygame.Surface((screen.get_width(), 5))
rectangle_cut_off_bottom_pos = pygame.Vector2(0, rectangle_cut_off_bottom)
rectangle_cut_off_bottom_surf = pygame.Surface((screen.get_width(), 5))
rectangle_speed = 1
r_u = rectangle_speed
rect_id = 0


def get_rectangles_to_draw():
    rects = []
    for _, (top, bottom) in rectangle_queue:
        rects.append(
            {
                "surface": screen,
                "color": "green",
                "rect": rect_surf.get_rect(midbottom=(top.x, top.y)),
            },
        )
        rects.append(
            {
                "surface": screen,
                "color": "black",
                "rect": rect_surf.get_rect(midtop=(bottom.x, bottom.y)),
            },
        )
    return rects


def update_score():
    for rect_id, (top, _) in rectangle_queue:
        global score
        if rect_id == score + 1 and (cube_pos.x) - (h / 2) > top.x + (
            rectangle_width / 2
        ):
            score = rect_id
            print(score)


def draw_rectangles_return_collides(rects: list[dict]):
    collides = []
    for kwargs in rects:
        collide = True
        if "collide" in kwargs:
            collide = False
            del kwargs["collide"]
        pygame.draw.rect(**kwargs)  # can parallelize maybe
        if collide:
            collides.append(kwargs.get("rect"))
    return collides


def game_start_action(start_event_triggered):
    if not start_event_triggered:
        pygame.time.set_timer(GAMESTART_EVENT, start_delay_ms, 1)
        return False, True
    if game_start:
        return True, True


def reset_game():
    global_vars = globals()
    global_vars["BIRD_DIE_EVENT"] = False
    global_vars["start_event_triggered"] = False
    global_vars["game_start"] = False
    global_vars["cube_pos"] = pygame.Vector2(
        screen.get_width() / 2, screen.get_height() / 2
    )
    global_vars["rectangle_queue"].clear()
    global_vars["rect_id"] = 0
    global_vars["score"] = 0
    global_vars["u"] = 0
    global_vars["r_u"] = rectangle_speed
    global_vars["bird_acc"] = a


running = True
last_time = time.time()
while running:
    flap = False
    dt = time.time() - last_time
    last_time = time.time()
    for event in pygame.event.get():
        if event.type == GAMESTART_EVENT:
            game_start = True
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                if BIRD_DIE_EVENT:
                    reset_game()
                else:
                    flap, start_event_triggered = game_start_action(
                        start_event_triggered
                    )
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT]:
                if BIRD_DIE_EVENT:
                    reset_game()
                else:
                    flap, start_event_triggered = game_start_action(
                        start_event_triggered
                    )

    # Calculate bird motion
    g = gravity if game_start else 0

    if not start_event_triggered:
        if pygame.time.get_ticks() % (prestart_flip_time * 2) < prestart_flip_time:
            cube_pos.y += (-prestart_speed) * distance_scaler * dt
        else:
            cube_pos.y += (prestart_speed) * distance_scaler * dt

    if flap and (pygame.time.get_ticks() - last_flap >= flap_cooldown):
        u += -bird_acc * flap_time
        last_flap = pygame.time.get_ticks()

    u += g * dt

    if cube_pos.y <= screen.get_height():
        cube_pos.y += (u * dt) * distance_scaler

    # Limits
    if cube_pos.y < skybox:
        cube_pos.y = skybox
    if cube_pos.y > screen.get_height() - ground:
        cube_pos.y = screen.get_height() - ground

    if cube_pos.y <= cut_off_line_top_pos.y:
        bird_acc = min(bird_acc, min_bird_acc)
    elif cube_pos.y >= cut_off_line_bottom_pos.y:
        bird_acc = max(bird_acc, max_bird_acc)
    if cube_pos.y >= cut_off_line_top_pos.y and cube_pos.y <= cut_off_line_bottom_pos.y:
        bird_acc = a

    # Spawn Rectangles
    if game_start and pygame.time.get_ticks() - last_rect_spawn >= spawn_time:
        # randomizing logic here
        gap_start = random.randint(
            rectangle_cut_off_top,
            rectangle_cut_off_bottom,
        )
        rects = (
            pygame.Vector2(spawn_location_x, gap_start),
            pygame.Vector2(spawn_location_x, gap_start + (gap * distance_scaler)),
        )
        last_rect_spawn = pygame.time.get_ticks()
        rect_id += 1
        rectangle_queue.append((rect_id, rects))
        if rectangle_queue[0][1][0].x <= -100:
            rectangle_queue.popleft()

    # Move Rectangles:
    for _, (top, bottom) in rectangle_queue:
        top.x -= (r_u * dt) * distance_scaler
        bottom.x -= (r_u * dt) * distance_scaler

    # Render Game
    screen.fill(color="lightblue")
    collide_rects = draw_rectangles_return_collides(
        [
            {
                "surface": screen,
                "color": "black",
                "rect": cut_off_line_top_surf.get_rect(
                    midleft=(cut_off_line_top_pos.x, cut_off_line_top_pos.y)
                ),
                "collide": False,
            },
            {
                "surface": screen,
                "color": "pink",
                "rect": cut_off_line_bottom_surf.get_rect(
                    midleft=(cut_off_line_bottom_pos.x, cut_off_line_bottom_pos.y)
                ),
                "collide": False,
            },
        ]
        + get_rectangles_to_draw()
        + [
            {
                "surface": screen,
                "color": "grey",
                "rect": cut_off_line_ground_surf.get_rect(
                    midleft=(cut_off_line_ground_pos.x, cut_off_line_ground_pos.y)
                ),
            },
            {
                "surface": screen,
                "color": "yellow",
                "rect": cube_surf.get_rect(midbottom=(cube_pos.x, cube_pos.y)),
            },
        ]
    )

    update_score()

    # Handle Collisions
    bird_rect = collide_rects.pop()
    ground_rect = collide_rects[-1]
    collisions = bird_rect.collidelistall(collide_rects)

    if game_start and len(collisions) >= 1:
        r_u = 0
        bird_acc = 0
        u = max(u, 0)

    if game_start and bird_rect.colliderect(ground_rect):
        BIRD_DIE_EVENT = True

    # Display Score
    if BIRD_DIE_EVENT:
        best_score = max(score, best_score)
        score_surface = score_font.render(f"{score}", True, "White")
        score_text_surface = score_font.render("SCORE", True, "orange1")
        best_score_surface = score_font.render(f"{best_score}", True, "White")
        best_score_text_surface = score_font.render("BEST", True, "orange1")
        space_to_restart = score_font.render("Restart??", True, "White")
        retry_screen_rect = retry_screen_surf.get_rect(
            center=(retry_screen_pos.x, retry_screen_pos.y)
        )
        pygame.time.delay(150)
        pygame.draw.rect(screen, "palegoldenrod", retry_screen_rect, border_radius=10)
        pygame.draw.rect(screen, "black", retry_screen_rect, 5, 10)
        screen.blits(
            [
                (
                    score_text_surface,
                    score_text_surface.get_rect(
                        center=(
                            retry_screen_rect.topleft
                            + pygame.Vector2(
                                retry_screen_rect.w / 4,
                                retry_screen_rect.h / 5,
                            )
                        )
                    ),
                ),
                (
                    score_surface,
                    score_surface.get_rect(
                        center=(
                            retry_screen_rect.topleft
                            + pygame.Vector2(
                                retry_screen_rect.w / 4,
                                retry_screen_rect.h / 3,
                            )
                        )
                    ),
                ),
                (
                    best_score_text_surface,
                    best_score_text_surface.get_rect(
                        center=(
                            retry_screen_rect.topright
                            + pygame.Vector2(
                                -retry_screen_rect.w / 4,
                                retry_screen_rect.h / 5,
                            )
                        )
                    ),
                ),
                (
                    best_score_surface,
                    best_score_surface.get_rect(
                        center=(
                            retry_screen_rect.topright
                            + pygame.Vector2(
                                -retry_screen_rect.w / 4,
                                retry_screen_rect.h / 3,
                            )
                        )
                    ),
                ),
                (
                    space_to_restart,
                    space_to_restart.get_rect(
                        center=(
                            retry_screen_rect.centerx,
                            retry_screen_rect.centery + retry_screen_rect.h / 4,
                        )
                    ),
                ),
            ]
        )
    else:
        score_surface = score_font.render(f"{score}", True, "White")
        screen.blit(
            score_surface,
            score_surface.get_rect(midtop=(screen.get_width() / 2, cut_off_line_top)),
        )

    # Update Game
    pygame.display.flip()
    clock.tick(framerate)

pygame.quit()
