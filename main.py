from collections import deque
import random
import time
import pygame
import math

# game
pygame.init()
pygame.display.set_caption("flappybird++")
screen = pygame.display.set_mode((1280, 720))
screen_width = screen.get_width()
screen_height = screen.get_height()
center_screen_vec = pygame.Vector2(screen_width / 2, screen_height / 2)
clock = pygame.time.Clock()
framerate = 144

game_start = False
prestart_speed = 0.2
prestart_flip_time = 2000  # slowly move up and down when idle
start_delay_ms = 100
GAMESTART_EVENT = pygame.USEREVENT + 1
start_event_triggered = False
BIRD_DIE_EVENT = False
score_font = pygame.font.Font("./assets/pixelify_sans.ttf", 38)

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

retry_screen_pos = center_screen_vec.copy()
retry_screen_surf = pygame.Surface((screen_width / 3, screen_height / 3))

background_image = pygame.transform.scale2x(
    pygame.image.load("./assets/background.png").convert_alpha()
)
background_scroll_speed = 0.5
bg_u = background_scroll_speed
background_pos = pygame.Vector2(0, screen_height - ground)

# player
h = 0.27 * distance_scaler
player_pos = center_screen_vec.copy()

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
# Headstart
HEAD_START_EVENT = False
head_start_image = pygame.image.load("./assets/headstart.png").convert_alpha()
head_start_image_anim = pygame.transform.scale(
    pygame.image.load("./assets/headstart_anim.png").convert_alpha(), (100, 100)
)
head_start_last_trigger = pygame.time.get_ticks()
head_start_time = 5 * 1000
rect_spawn_time_headstart = 0.5 * 1000
head_start_id = 1
player_head_start_pos = player_pos.copy()
head_start_anim_offset = (-10, 5)
head_start_anim_scale = 0

# Pew pew start event
PEW_PEW_START_EVENT = False
pew_pew_image = pygame.image.load("./assets/gun.png").convert_alpha()
pew_pew_image_anim = pygame.transform.scale(pew_pew_image, (60, 60))
gun_last_trigger = pygame.time.get_ticks()
gun_time = 12 * 1000
rect_spawn_time_gun = 0.75 * 1000
gun_offset = (50, 10)
gun_pos = pygame.Vector2(player_pos.x + gun_offset[0], player_pos.y + gun_offset[1])
player_pew_pew_pos = player_pos.copy()
player_pew_pew_pos_expected = player_pos.copy()
secret_ending_last_trigger = pygame.time.get_ticks()


bullet_surf = pygame.Surface((10, 10))
bullet_speed = 2
bullet_cooldown = 0.5 * 1000
last_bullet_fired = pygame.time.get_ticks()
fire_bullet = False
bullet_queue = deque(maxlen=20)

pipes_to_fall = []
pew_pew_id = 2

# Feather Ending
FEATHER_EVENT_START = False
feather_image = pygame.image.load("./assets/feather.png").convert_alpha()
feather_image_anim = pygame.transform.scale(feather_image, (30, 30))
feather_last_trigger = pygame.time.get_ticks()
feather_cooldown = 0.1 * 1000
feather_bump = 1
feather_id = 3
feather_queue = deque(maxlen=10)
SECRET_ENDING_EVENT = False
SECRET_ENDING_EVENT_TRIGGERED = False
secret_ending_pos = player_pos.copy()
secret_ending_pos_expected = pygame.Vector2(screen_width, 0)

# Power UP general
collide = True
powerups_spawned = deque(maxlen=20)
powerup_dim = 60
powerup_images = {
    head_start_id: pygame.transform.scale(head_start_image, (powerup_dim, powerup_dim)),
    pew_pew_id: pygame.transform.scale(pew_pew_image, (powerup_dim, powerup_dim)),
    feather_id: pygame.transform.scale(feather_image, (powerup_dim, powerup_dim)),
}
powerup_counts = {
    head_start_id: 0,
    pew_pew_id: 0,
    feather_id: 0,
}
powerup_keys = {
    head_start_id: "Q",
    pew_pew_id: "W",
    feather_id: "E",
}
powerup_ui_surf_dim = 100
powerup_ui_surface = pygame.Surface((powerup_ui_surf_dim, powerup_ui_surf_dim))
powerup_ui_font = pygame.font.Font("./assets/pixelify_sans.ttf", 30)


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
        powerup_image = powerup_images[powerup_id]
        powerup_rect = powerup_image.get_rect(center=powerup_pos)
        powerup_ids.append(powerup_id)
        blits.append((powerup_image, powerup_rect))
        rects.append(powerup_rect)
    screen.blits(blits)
    return powerup_ids, rects


def draw_ui():
    ui_pos = pygame.Vector2(100, screen_height - 100)
    blits = []
    for powerup_id, count in powerup_counts.items():
        if count > 0:
            surface_rect = powerup_ui_surface.get_rect(center=ui_pos)
            pygame.draw.rect(screen, "#ded895", surface_rect, border_radius=10)
            pygame.draw.rect(screen, "black", surface_rect, width=5, border_radius=10)
            powerup_image = powerup_images[powerup_id]
            powerup_rect = powerup_image.get_rect(center=(ui_pos.x - 10, ui_pos.y - 10))
            count_pos = pygame.Vector2(
                ui_pos.x + (powerup_ui_surf_dim / 2),
                ui_pos.y - (powerup_ui_surf_dim / 2),
            )
            count_surface = powerup_ui_font.render(f"{count}", True, "White")
            count_rect = count_surface.get_rect(center=count_pos)
            key_surf = powerup_ui_font.render(
                f"{powerup_keys[powerup_id]}", True, "#fc7858"
            )
            key_rect = key_surf.get_rect(
                center=(count_pos.x - 30, count_pos.y + powerup_ui_surf_dim - 30)
            )
            pygame.draw.circle(screen, "black", count_pos, radius=20)
            pygame.draw.circle(screen, "#ded895", count_pos, radius=16)
            blits.extend(
                [
                    (powerup_image, powerup_rect),
                    (count_surface, count_rect),
                    (key_surf, key_rect),
                ]
            )
            ui_pos.x += powerup_ui_surf_dim + 20
    screen.blits(blits)


def draw_headstart_amin():
    anim_image = pygame.transform.scale_by(head_start_image_anim, head_start_anim_scale)
    screen.blit(
        anim_image,
        anim_image.get_rect(
            midright=(
                player_pos.x + head_start_anim_offset[0],
                player_pos.y + head_start_anim_offset[1],
            )
        ),
    )


def draw_feather_amin():
    blits = []
    for feather_pos, _ in feather_queue:
        blits.append(
            (feather_image_anim, feather_image_anim.get_rect(center=feather_pos))
        )
    screen.blits(blits)


def draw_gun_amin():
    screen.blit(
        pew_pew_image_anim,
        pew_pew_image_anim.get_rect(center=gun_pos),
    )


def parabola(a: float, t: float, k: float):
    return math.pow(a * t * (1.0 - t), k)


def smoothstep(t: float):
    t1 = math.pow(t, 2)
    t2 = 1 - math.pow(1 - t, 2)
    return pygame.math.lerp(t1, t2, t)


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


def reset_rectangles(game_end: bool = False):
    global_vars = globals()
    global_vars["rectangle_queue"].clear()
    global_vars["rect_id"] = 0 if game_end else global_vars["score"]


def bird_reset(modify_pos: bool = True):
    global_vars = globals()
    if modify_pos:
        global_vars["player_pos"].update(screen_width / 2, screen_height / 2)
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


def common_collide_action():
    global_vars = globals()
    global_vars["r_u"] = 0
    global_vars["animate_flap"] = False
    global_vars["g_u"] = 0
    global_vars["bg_u"] = 0


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
    global_vars["feather_queue"].clear()
    global_vars["SECRET_ENDING_EVENT_TRIGGERED"] = False
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
                and powerup_counts[head_start_id] > 0
                and game_start
                and not BIRD_DIE_EVENT
                and not HEAD_START_EVENT
            ):
                powerup_counts[head_start_id] -= 1
                HEAD_START_EVENT = True
                head_start_last_trigger = pygame.time.get_ticks()
                player_head_start_pos = player_pos.copy()
            if (
                event.key == pygame.K_w
                and powerup_counts[pew_pew_id] > 0
                and game_start
                and not BIRD_DIE_EVENT
                and not PEW_PEW_START_EVENT
            ):
                powerup_counts[pew_pew_id] -= 1
                PEW_PEW_START_EVENT = True
                gun_last_trigger = pygame.time.get_ticks()
                player_pew_pew_pos_expected = pygame.Vector2(100, player_pos.y)
                player_pew_pew_pos = player_pos.copy()
            if event.key == pygame.K_e and game_start and not BIRD_DIE_EVENT:
                if powerup_counts[feather_id] > 0:
                    feather_trigger_pos = player_pos.copy()
                    powerup_counts[feather_id] -= 1
                    FEATHER_EVENT_START = True
                    feather_last_trigger = pygame.time.get_ticks()
            if event.key == pygame.K_r and game_start and not BIRD_DIE_EVENT:
                if powerup_counts[feather_id] >= 10:
                    feather_trigger_pos = player_pos.copy()
                    powerup_counts[feather_id] = 0
                    SECRET_ENDING_EVENT = True
                    secret_ending_pos = player_pos.copy()
                    secret_ending_last_trigger = pygame.time.get_ticks()
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
        head_start_anim_scale = 0
        time_since_trigger_h = pygame.time.get_ticks() - head_start_last_trigger
        if time_since_trigger_h <= head_start_time:
            dt = dt * 2
            u = 0
            flap = False
            player_pos = player_head_start_pos.lerp(
                center_screen_vec,
                smoothstep(min((time_since_trigger_h / 500), 1)),
            )
            head_start_anim_scale = pygame.math.lerp(
                0, 1.5, parabola(4, (time_since_trigger_h / (head_start_time + 400)), 1)
            )
            collide = False
            spawn_time = rect_spawn_time_headstart
            r_u = rectangle_speed * 3
            g_u = ground_scroll_speed * 2
            f_u = flap_animation_time / 2
            if time_since_trigger_h > head_start_time - 500:
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
        time_since_trigger_p = pygame.time.get_ticks() - gun_last_trigger
        if time_since_trigger_p <= gun_time:
            if (
                time_since_trigger_p <= 1000
                or player_pos.x != player_pew_pew_pos_expected.x  # handle powerups
            ):
                u = 0
                player_pos = player_pew_pew_pos.lerp(
                    player_pew_pew_pos_expected,
                    smoothstep(min((time_since_trigger_p / 1000), 1)),
                )
            gun_pos.update(player_pos.x + gun_offset[0], player_pos.y + gun_offset[1])
            spawn_time = rect_spawn_time_gun
            r_u = rectangle_speed * 3
            g_u = ground_scroll_speed * 2
            f_u = flap_animation_time / 2
            if time_since_trigger_p <= 100:
                reset_rectangles(False)
            if pygame.time.get_ticks() - last_bullet_fired <= bullet_cooldown:
                fire_bullet = False
            else:
                fire_bullet = True
                last_bullet_fired = pygame.time.get_ticks()
            if time_since_trigger_p > gun_time - 500:
                if (
                    len(rectangle_queue) > 0
                    and rectangle_queue[-1][1][1].x >= player_pos.x
                ):
                    rectangle_queue.pop()
        else:
            PEW_PEW_START_EVENT = False
            pipes_to_fall.clear()
            powerup_reset(modify_bird_pos=False)
            player_pos.update(screen_width / 2, player_pos.y)

    if SECRET_ENDING_EVENT:
        if not BIRD_DIE_EVENT:
            FEATHER_EVENT_START = False
            SECRET_ENDING_EVENT_TRIGGERED = True
            reset_rectangles()
            player_pos.y -= feather_bump * distance_scaler
            feather_bump = 0
            if pygame.time.get_ticks() - feather_last_trigger >= feather_cooldown:
                feather_queue.append(
                    (
                        pygame.Vector2(
                            feather_trigger_pos.x,
                            (feather_trigger_pos.y + player_pos.y) / 2,
                        ),
                        0,
                    )
                )
                feather_last_trigger = pygame.time.get_ticks()
            if len(feather_queue) == 10:
                SECRET_ENDING_EVENT = False
                feather_bump = 1

    if FEATHER_EVENT_START:
        if (
            pygame.time.get_ticks() - feather_last_trigger >= feather_cooldown
            and not BIRD_DIE_EVENT
        ):
            u = 0
            player_pos.y -= feather_bump * distance_scaler
            FEATHER_EVENT_START = False
            feather_queue.append(
                (
                    pygame.Vector2(
                        feather_trigger_pos.x,
                        (feather_trigger_pos.y + player_pos.y) / 2,
                    ),
                    0,
                )
            )

    if SECRET_ENDING_EVENT_TRIGGERED:
        FEATHER_EVENT_START = False
        PEW_PEW_START_EVENT = False
        head_start_anim_scale = 1
        g = 0
        r_u = 0
        lerp_offset = smoothstep(
            min((pygame.time.get_ticks() - secret_ending_last_trigger) / 5000, 1)
        )
        player_pos = secret_ending_pos.lerp(secret_ending_pos_expected, lerp_offset)
        if lerp_offset == 1:
            BIRD_DIE_EVENT = True
            common_collide_action()

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
        spawn_random_powerup = random.randint(0, 10)
        # 0, (1, 2, 3), 4, 5, 6, 7, 8, 9, 10 (only spawns at 1, 2, 3)
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
            bullet_queue.append(pygame.Vector2(gun_pos.x + 30, gun_pos.y))
        # Move bullets:
        for bullet in bullet_queue:
            bullet.x += (bullet_speed * dt) * distance_scaler
    else:
        if len(bullet_queue) > 0:
            bullet_queue.clear()

    for i, (feather, speed) in enumerate(feather_queue):
        speed += (g - 7) * dt  # feather are lighter
        feather.x -= (g_u * dt) * distance_scaler
        if feather.y <= screen_height - ground:
            feather.y += (speed * dt) * distance_scaler
        feather_queue[i] = (feather, speed)

    if len(feather_queue) and feather_queue[0][0].x <= 0:
        feather_queue.popleft()

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

    if HEAD_START_EVENT or SECRET_ENDING_EVENT_TRIGGERED:
        draw_headstart_amin()
    if PEW_PEW_START_EVENT:
        draw_gun_amin()
    draw_feather_amin()

    bird = draw_and_get_bird()
    powerup_ids, powerups = draw_and_get_powerups()
    if not BIRD_DIE_EVENT:
        draw_ui()

    if animate_flap:
        update_score()

    # Handle Collisions
    for id, pipe in zip(pipe_ids, pipes):
        collide_list = pipe.collidelistall(bullets)
        if len(collide_list) >= 1:
            pipes_to_fall.append((id, 0))

    if collide:
        if game_start and len(bird.collidelistall(pipes)) >= 1:
            bird_acc = 0
            u = max(u, 0)
            common_collide_action()

        if len(bird.collidelistall(grounds)) >= 1:
            BIRD_DIE_EVENT = True
            common_collide_action()

        if game_start and len(bird.collidelistall(powerups)) >= 1:
            powerup_counts[powerup_ids[0]] += 1
            powerups_spawned.popleft()

    # Display Score
    if BIRD_DIE_EVENT:
        HEAD_START_EVENT = False
        PEW_PEW_START_EVENT = False
        feather_queue.clear()
        powerup_reset(modify_bird_pos=False)
        best_score = max(score, best_score)
        score_surface = score_font.render(f"{score}", True, "White")
        score_text_surface = score_font.render("SCORE", True, "#fc7858")
        best_score_surface = score_font.render(f"{best_score}", True, "White")
        best_score_text_surface = score_font.render("BEST", True, "#fc7858")
        space_to_restart = score_font.render(
            "Restart??" if not SECRET_ENDING_EVENT_TRIGGERED else "Congratulations",
            True,
            "White",
        )
        secret_ending_bonus = score_font.render(
            "You beat it.",
            True,
            "White",
        )
        secret_ending_bonus1 = score_font.render(
            "Now go outside and touch grass.",
            True,
            "White",
        )
        if SECRET_ENDING_EVENT_TRIGGERED:
            retry_screen_surf_scaled = pygame.transform.scale_by(retry_screen_surf, 1.5)
            retry_screen_rect = retry_screen_surf_scaled.get_rect(
                center=(retry_screen_pos)
            )
        else:
            retry_screen_rect = retry_screen_surf.get_rect(center=(retry_screen_pos))

        pygame.time.delay(150)
        pygame.draw.rect(screen, "#ded895", retry_screen_rect, border_radius=10)
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
                            (retry_screen_rect.centery + retry_screen_rect.h / 4)
                            if not SECRET_ENDING_EVENT_TRIGGERED
                            else retry_screen_rect.centery,
                        )
                    ),
                ),
            ]
        )
        if SECRET_ENDING_EVENT_TRIGGERED:
            screen.blits(
                [
                    (
                        secret_ending_bonus,
                        secret_ending_bonus.get_rect(
                            center=(
                                retry_screen_rect.centerx,
                                retry_screen_rect.centery + 40,
                            )
                        ),
                    ),
                    (
                        secret_ending_bonus1,
                        secret_ending_bonus1.get_rect(
                            center=(
                                retry_screen_rect.centerx,
                                retry_screen_rect.centery + 80,
                            )
                        ),
                    ),
                ],
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
