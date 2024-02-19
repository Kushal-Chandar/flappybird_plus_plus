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
f_u = flap_animation_time
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
spawn_time_normal = 3 * 1000
spawn_time = spawn_time_normal
rectangle_queue = deque(maxlen=20)
last_rect_spawn = pygame.time.get_ticks()
rectangle_cut_off_top = 100
rectangle_cut_off_bottom = int(screen_height - 100 - ground - (gap * distance_scaler))
rectangle_speed = ground_scroll_speed
r_u = rectangle_speed
rect_id = 0

# Power Ups
collide = True
powerups_spawned = deque(maxlen=20)
powerup_width = 64
powerup_height = 64
powerup_image = pygame.Surface((powerup_width, powerup_height))


# Headstart
HEAD_START_EVENT = False
head_start_last_trigger = pygame.time.get_ticks()
head_start_time = 5 * 1000
rect_spawn_time_headstart = 0.5 * 1000
head_starts_count = 0
head_start_id = 1

# Pew pew start event
PEW_PEW_START_EVENT = False
gun_last_trigger = pygame.time.get_ticks()
gun_time = 20 * 1000
rect_spawn_time_gun = 0.75 * 1000

bullet_surf = pygame.Surface((10, 10))
bullet_speed = 2
bullet_cooldown = 0.5 * 1000
last_bullet_fired = pygame.time.get_ticks()
fire_bullet = False
bullet_queue = deque(maxlen=20)

pipes_to_fall = []
pew_pew_count = 0
pew_pew_id = 2

# Feather Ending
FEATHER_EVENT_START = False
feather_last_trigger = pygame.time.get_ticks()
feather_cooldown = 0.1 * 1000
feather_bump = 1
feather_count = 0
feather_id = 3


def draw_background():
    blits = []
    pos = background_pos.copy()
    while pos.x <= screen_width + 100:
        background_rect = background_image.get_rect(bottomleft=pos)
        pos.x += background_rect.width
        blits.append((background_image, background_rect))
    screen.blits(blits)


def draw_and_get_pipes():
    rects = []
    blits = []
    rect_ids = []
    for rect_id, (top, bottom) in rectangle_queue:
        top_rect = rect_image.get_rect(midbottom=top)
        bottom_rect = flipped_rect_image.get_rect(midtop=bottom)
        blits.extend([(rect_image, top_rect), (flipped_rect_image, bottom_rect)])
        rects.extend([top_rect, bottom_rect])
        rect_ids.extend([(rect_id, 0), (rect_id, 1)])
    screen.blits(blits)
    return rect_ids, rects


def draw_and_get_bullets():
    rects = []
    blits = []
    for bullet_pos in bullet_queue:
        bullet_rect = bullet_surf.get_rect(center=bullet_pos)
        rects.append(bullet_rect)
        blits.append((bullet_surf, bullet_rect))
    screen.blits(blits)
    return rects


def draw_and_get_ground():
    rects = []
    blits = []
    pos = ground_pos.copy()
    while pos.x <= screen_width + 100:
        ground_rect = ground_image.get_rect(topleft=pos)
        pos.x += ground_rect.width
        blits.append((ground_image, ground_rect))
        rects.append(ground_rect)
    screen.blits(blits)
    return rects


def draw_and_get_bird():
    bird_image = bird_states[bird_state]
    bird_rect = bird_image.get_rect(center=player_pos)
    bird_image = pygame.transform.scale_by(bird_image, 1.2)
    screen.blit(bird_image, bird_rect)
    return bird_rect


def draw_and_get_powerups():
    blits = []
    rects = []
    powerup_ids = []
    for powerup_id, powerup_pos in powerups_spawned:
        powerup_rect = powerup_image.get_rect(center=powerup_pos)
        powerup_ids.append(powerup_id)
        blits.append((powerup_image, powerup_rect))
        rects.append(powerup_rect)
    screen.blits(blits)
    return powerup_ids, rects


def update_score():
    for rect_id, (top, _) in rectangle_queue:
        global score
        if rect_id == score + 1 and (
            (player_pos.x) - (h / 2) > top.x + rectangle_width_half
        ):
            score = rect_id


def game_start_action(start_event_triggered):
    if not start_event_triggered:
        pygame.time.set_timer(GAMESTART_EVENT, start_delay_ms, 1)
        return False, True
    if game_start:
        return True, True


def reset_rectangles(game_end: bool):
    global_vars = globals()
    global_vars["rectangle_queue"].clear()
    global_vars["rect_id"] = 0 if game_end else global_vars["score"]


def bird_reset(modify_pos: bool = True):
    global_vars = globals()
    if modify_pos:
        global_vars["player_pos"] = pygame.Vector2(screen_width / 2, screen_height / 2)
    global_vars["f_u"] = flap_animation_time
    global_vars["bird_acc"] = a
    global_vars["bird_state"] = 1
    global_vars["animate_flap"] = True


def powerup_reset(modify_bird_pos: bool = True):
    global_vars = globals()
    global_vars["spawn_time"] = spawn_time_normal
    global_vars["r_u"] = min(r_u, rectangle_speed)
    global_vars["g_u"] = min(r_u, ground_scroll_speed)
    global_vars["rect_id"] = global_vars["score"]
    bird_reset(modify_bird_pos)


def reset_game():
    global_vars = globals()
    global_vars["BIRD_DIE_EVENT"] = False
    global_vars["start_event_triggered"] = False
    global_vars["game_start"] = False
    global_vars["score"] = 0
    global_vars["u"] = 0
    global_vars["r_u"] = rectangle_speed
    global_vars["g_u"] = ground_scroll_speed
    global_vars["bg_u"] = background_scroll_speed
    global_vars["bullet_queue"].clear()
    global_vars["HEAD_START_EVENT"] = False
    global_vars["PEW_PEW_START_EVENT"] = False
    global_vars["pipes_to_fall"].clear()
    global_vars["powerups_spawned"].clear()
    reset_rectangles(True)
    bird_reset()


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
            if (
                event.key == pygame.K_q
                and head_starts_count > 0
                and game_start
                and not BIRD_DIE_EVENT
            ):
                head_starts_count -= 1
                HEAD_START_EVENT = True
                head_start_last_trigger = pygame.time.get_ticks()
            if (
                event.key == pygame.K_w
                and pew_pew_count > 0
                and game_start
                and not BIRD_DIE_EVENT
            ):
                pew_pew_count -= 1
                PEW_PEW_START_EVENT = True
                gun_last_trigger = pygame.time.get_ticks()
            if event.key == pygame.K_e and game_start and not BIRD_DIE_EVENT:
                if feather_count > 0 and feather_count < 10:
                    feather_count -= 1
                    FEATHER_EVENT_START = True
                    feather_last_trigger = pygame.time.get_ticks()
                elif feather_count == 10:
                    feather_count = 0
                    SECRET_ENDING_EVENT = True
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

    # Head start
    if HEAD_START_EVENT:
        if pygame.time.get_ticks() - head_start_last_trigger <= head_start_time:
            dt = dt * 2
            g = 0
            flap = False
            player_pos = pygame.Vector2(screen_width / 2, screen_height / 2)
            collide = False
            spawn_time = rect_spawn_time_headstart
            r_u = rectangle_speed * 3
            g_u = ground_scroll_speed * 2
            f_u = flap_animation_time / 2
            if (
                pygame.time.get_ticks() - head_start_last_trigger
                > head_start_time - 500
            ):
                if (
                    len(rectangle_queue) > 0
                    and rectangle_queue[-1][1][1].x >= player_pos.x
                ):
                    rectangle_queue.pop()
        else:
            HEAD_START_EVENT = False
            collide = True
            powerup_reset()

    # Pew pew
    if PEW_PEW_START_EVENT:
        if pygame.time.get_ticks() - gun_last_trigger <= gun_time:
            player_pos = pygame.Vector2(100, player_pos.y)
            spawn_time = rect_spawn_time_gun
            r_u = rectangle_speed * 3
            g_u = ground_scroll_speed * 2
            f_u = flap_animation_time / 2
            if pygame.time.get_ticks() - gun_last_trigger <= 100:
                reset_rectangles(False)
            if pygame.time.get_ticks() - last_bullet_fired <= bullet_cooldown:
                fire_bullet = False
            else:
                fire_bullet = True
                last_bullet_fired = pygame.time.get_ticks()
            if pygame.time.get_ticks() - gun_last_trigger > gun_time - 500:
                if (
                    len(rectangle_queue) > 0
                    and rectangle_queue[-1][1][1].x >= player_pos.x
                ):
                    rectangle_queue.pop()
        else:
            PEW_PEW_START_EVENT = False
            pipes_to_fall.clear()
            powerup_reset(modify_bird_pos=False)
            player_pos = pygame.Vector2(screen_width / 2, player_pos.y)

    if FEATHER_EVENT_START:
        if (
            pygame.time.get_ticks() - feather_last_trigger >= feather_cooldown
            and not BIRD_DIE_EVENT
        ):
            u = 0
            player_pos.y -= feather_bump * distance_scaler
            FEATHER_EVENT_START = False

    if not start_event_triggered:
        if pygame.time.get_ticks() % (prestart_flip_time * 2) < prestart_flip_time:
            player_pos.y += (-prestart_speed) * distance_scaler * dt
        else:
            player_pos.y += (prestart_speed) * distance_scaler * dt

    if animate_flap and pygame.time.get_ticks() - last_flap_animation >= f_u:
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

    # Spawn Rectangles and powerups
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
        powerup_y = (gap_start + gap_start + (gap * distance_scaler)) / 2
        spawn_random_powerup = random.randint(0, 7)
        # 0, (1, 2, 3), 4, 5, 6, 7 (only spawns at 1, 2, 3)
        if spawn_random_powerup in [1, 2, 3]:
            powerups_spawned.append(
                (spawn_random_powerup, pygame.Vector2(spawn_location_x, powerup_y))
            )
        if len(powerups_spawned) > 0 and powerups_spawned[0][1].x <= -100:
            powerups_spawned.popleft()

    # Move Rectangles:
    for _, (top, bottom) in rectangle_queue:
        top.x -= (r_u * dt) * distance_scaler
        bottom.x -= (r_u * dt) * distance_scaler

    for pipe, speed in pipes_to_fall:
        speed += g * dt
        for rect_id, rect in rectangle_queue:
            if pipe[0] == rect_id:
                rect[pipe[1]].y += (speed * dt) * distance_scaler

    # Move powerups
    for _, power_up in powerups_spawned:
        power_up.x -= (r_u * dt) * distance_scaler

    # Spawn bullets
    if PEW_PEW_START_EVENT:
        if fire_bullet:
            bullet_queue.append(player_pos.copy())
        # Move bullets:
        for bullet in bullet_queue:
            bullet.x += (bullet_speed * dt) * distance_scaler
    else:
        if len(bullet_queue) > 0:
            bullet_queue.clear()

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
    bullets = draw_and_get_bullets()
    pipe_ids, pipes = draw_and_get_pipes()
    grounds = draw_and_get_ground()
    bird = draw_and_get_bird()
    powerup_ids, powerups = draw_and_get_powerups()

    if animate_flap:
        update_score()

    # Handle Collisions
    if collide:
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

        for id, pipe in zip(pipe_ids, pipes):
            collide_list = pipe.collidelistall(bullets)
            if len(collide_list) >= 1:
                pipes_to_fall.append((id, 0))

        if game_start and len(bird.collidelistall(powerups)) >= 1:
            if powerup_ids[0] == head_start_id:
                head_starts_count += 1
            elif powerup_ids[0] == pew_pew_id:
                pew_pew_count += 1
            elif powerup_ids[0] == feather_id:
                feather_count += 1
            powerups_spawned.popleft()

    print(head_starts_count, pew_pew_count, feather_count)

    # Display Score
    if BIRD_DIE_EVENT:
        HEAD_START_EVENT = False
        PEW_PEW_START_EVENT = False
        powerup_reset(modify_bird_pos=False)
        best_score = max(score, best_score)
        score_surface = score_font.render(f"{score}", True, "White")
        score_text_surface = score_font.render("SCORE", True, "orange1")
        best_score_surface = score_font.render(f"{best_score}", True, "White")
        best_score_text_surface = score_font.render("BEST", True, "orange1")
        space_to_restart = score_font.render("Restart??", True, "White")
        retry_screen_rect = retry_screen_surf.get_rect(center=(retry_screen_pos))
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
