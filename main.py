from collections import deque
import random
import time
import pygame

# game
pygame.init()
pygame.display.set_caption("flappybird")
screen = pygame.display.set_mode((1280, 720))
screen_width = screen.get_width()
screen_height = screen.get_height()
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


# world
distance_scaler = 155  # 1 meter = 155 pixels
gravity = 9.8

ground = 100
skybox = -100
cut_off_line_top = 100
cut_off_line_bottom = screen_height - 150 - ground

ground_image = pygame.transform.scale(
    pygame.image.load("./assets/ground.png").convert_alpha(), (100, 100)
)
ground_scroll_speed = 1
g_u = ground_scroll_speed
ground_pos = pygame.Vector2(0, screen_height - ground)

retry_screen_pos = pygame.Vector2(screen_width / 2, screen_height / 2)
retry_screen_surf = pygame.Surface((screen_width / 3, screen_height / 3))

background_image = pygame.transform.scale2x(
    pygame.image.load("./assets/background.png").convert_alpha()
)
background_scroll_speed = 0.5
bg_u = background_scroll_speed
background_pos = pygame.Vector2(0, screen_height - ground)

# player
h = 0.27 * distance_scaler
player_pos = pygame.Vector2(screen_width / 2, screen_height / 2)

bird_states = [
    pygame.transform.scale(
        pygame.image.load("./assets/bird_flap_up.png").convert_alpha(),
        (h, h),
    ),
    pygame.transform.scale(
        pygame.image.load("./assets/bird_flap_idle.png").convert_alpha(),
        (h, h),
    ),
    pygame.transform.scale(
        pygame.image.load("./assets/bird_flap_down.png").convert_alpha(),
        (h, h),
    ),
]
bird_state = 1
player_rect = bird_states[bird_state].get_rect()


flap_time = 0.4
flap_cooldown = 0.2 * 1000
flap = False
last_flap = pygame.time.get_ticks()

animate_flap = True
flap_animation_time = 0.08 * 1000
last_flap_animation = pygame.time.get_ticks()

u = 0
a = 10
min_bird_acc = 2
bird_acc = a
max_bird_acc = 15

# rectangle
gap = 1.1
rect_image = pygame.image.load("./assets/pipe.png").convert_alpha()
flipped_rect_image = pygame.transform.flip(rect_image, flip_x=False, flip_y=True)
rectangle_width_half = rect_image.get_rect().w / 2
spawn_width_offset = 500  # pixels
spawn_location_x = screen_width + spawn_width_offset
spawn_time = 3 * 1000
rectangle_queue = deque(maxlen=20)
last_rect_spawn = pygame.time.get_ticks()
rectangle_cut_off_top = 100
rectangle_cut_off_bottom = int(screen_height - 100 - ground - (gap * distance_scaler))
rectangle_speed = ground_scroll_speed
r_u = rectangle_speed
rect_id = 0


def draw_background():
    blits = []
    pos = background_pos.copy()
    while pos.x <= screen_width + 100:
        background_rect = background_image.get_rect(bottomleft=(pos.x, pos.y))
        pos.x += background_rect.width
        blits.append((background_image, background_rect))
    screen.blits(blits)


def draw_and_get_pipes():
    rects = []
    blits = []
    for _, (top, bottom) in rectangle_queue:
        top_rect = rect_image.get_rect(midbottom=(top.x, top.y))
        bottom_rect = flipped_rect_image.get_rect(midtop=(bottom.x, bottom.y))
        blits.extend([(rect_image, top_rect), (flipped_rect_image, bottom_rect)])
        rects.extend([top_rect, bottom_rect])
    screen.blits(blits)
    return rects


def draw_and_get_ground():
    rects = []
    blits = []
    pos = ground_pos.copy()
    while pos.x <= screen_width + 100:
        ground_rect = ground_image.get_rect(topleft=(pos.x, pos.y))
        pos.x += ground_rect.width
        blits.append((ground_image, ground_rect))
        rects.append(ground_rect)
    screen.blits(blits)
    return rects


def draw_and_get_bird():
    bird_image = bird_states[bird_state]
    bird_rect = bird_image.get_rect(center=(player_pos.x, player_pos.y))
    bird_image = pygame.transform.scale_by(bird_image, 1.2)
    screen.blit(bird_image, bird_rect)
    return bird_rect


def update_score():
    for rect_id, (top, _) in rectangle_queue:
        global score
        if rect_id == score + 1 and (
            (player_pos.x) - (h / 2) > top.x + rectangle_width_half
        ):
            score = rect_id


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
    global_vars["player_pos"] = pygame.Vector2(screen_width / 2, screen_height / 2)
    global_vars["rectangle_queue"].clear()
    global_vars["rect_id"] = 0
    global_vars["score"] = 0
    global_vars["u"] = 0
    global_vars["r_u"] = rectangle_speed
    global_vars["bird_acc"] = a
    global_vars["bird_state"] = 1
    global_vars["animate_flap"] = True
    global_vars["g_u"] = ground_scroll_speed
    global_vars["bg_u"] = background_scroll_speed


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
                    animate_flap = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in [pygame.BUTTON_LEFT, pygame.BUTTON_RIGHT]:
                if BIRD_DIE_EVENT:
                    reset_game()
                else:
                    flap, start_event_triggered = game_start_action(
                        start_event_triggered
                    )
                    animate_flap = True

    # Calculate bird motion
    g = gravity if game_start else 0

    if not start_event_triggered:
        if pygame.time.get_ticks() % (prestart_flip_time * 2) < prestart_flip_time:
            player_pos.y += (-prestart_speed) * distance_scaler * dt
        else:
            player_pos.y += (prestart_speed) * distance_scaler * dt

    if (
        animate_flap
        and pygame.time.get_ticks() - last_flap_animation >= flap_animation_time
    ):
        bird_state = (bird_state + 1) % 3
        last_flap_animation = pygame.time.get_ticks()

    if flap and (pygame.time.get_ticks() - last_flap >= flap_cooldown):
        u += -bird_acc * flap_time
        last_flap = pygame.time.get_ticks()

    u += g * dt
    player_pos.y += (u * dt) * distance_scaler

    # Limits
    if player_pos.y + (player_rect.h / 2) < skybox:
        player_pos.y = skybox - (player_rect.h / 2)
    if player_pos.y + (player_rect.h / 2) > screen_height - ground:
        player_pos.y = screen_height - ground - (player_rect.h / 2)

    if player_pos.y <= cut_off_line_top:
        bird_acc = min(bird_acc, min_bird_acc)
    elif player_pos.y >= cut_off_line_bottom:
        bird_acc = max(bird_acc, max_bird_acc)
    if (
        bird_acc
        and player_pos.y >= cut_off_line_top
        and player_pos.y <= cut_off_line_bottom
    ):
        bird_acc = a

    # Spawn Rectangles
    if (
        not BIRD_DIE_EVENT
        and game_start
        and pygame.time.get_ticks() - last_rect_spawn >= spawn_time
    ):
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

    # scroll background and ground
    background_pos.x -= (bg_u * dt) * distance_scaler
    if abs(background_pos.x) >= background_image.get_rect().w:
        background_pos.x = 0
    ground_pos.x -= (g_u * dt) * distance_scaler
    if abs(ground_pos.x) >= ground_image.get_rect().w:
        ground_pos.x = 0

    # Render Game
    screen.fill(color="lightblue")
    draw_background()
    pipes = draw_and_get_pipes()
    grounds = draw_and_get_ground()
    bird = draw_and_get_bird()

    update_score()

    # Handle Collisions
    if game_start and len(bird.collidelistall(pipes)) >= 1:
        r_u = 0
        bird_acc = 0
        u = max(u, 0)
        animate_flap = False
        g_u = 0
        bg_u = 0

    if len(bird.collidelistall(grounds)) >= 1:
        r_u = 0
        BIRD_DIE_EVENT = True
        animate_flap = False
        g_u = 0
        bg_u = 0

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
            score_surface.get_rect(midtop=(screen_width / 2, cut_off_line_top)),
        )

    # Update Game
    pygame.display.flip()
    clock.tick(framerate)

pygame.quit()
