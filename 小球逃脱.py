import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 1200, 900
CENTER = (WIDTH // 2, HEIGHT // 2)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("小球逃脱")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)


MIN_RADIUS_INIT = 30
MAX_RADIUS = 400
TOTAL_TIME = 100
BIG_CIRCLES_NUMBER = 30
NUM_CIRCLES = 1
SPREAD_DEG = 35


clock = pygame.time.Clock()
FPS = 60





pygame.font.init()
try:
    font = pygame.font.SysFont("Microsoft YaHei", 36)
    large_font = pygame.font.SysFont("Microsoft YaHei", 72)
except:
    font = pygame.font.SysFont(None, 36)
    large_font = pygame.font.SysFont(None, 72)
    print("微软雅黑字体不可用，已使用默认字体。")

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def normalize(vec):
    mag = math.hypot(vec[0], vec[1])
    if mag == 0:
        return [0, 0]
    return [vec[0] / mag, vec[1] / mag]

class BigCircle:
    def __init__(self, center, radius, notch_width_deg=30, angular_speed_deg_per_sec=30):
        self.center = center
        self.radius = radius
        self.notch_width = math.radians(notch_width_deg)
        self.angular_speed = math.radians(angular_speed_deg_per_sec)
        self.current_angle = 0

    def update(self, dt):
        self.current_angle += self.angular_speed * dt
        self.current_angle %= 2 * math.pi

    def is_within_notch(self, angle):
        angle = angle % (2 * math.pi)
        start_angle = self.current_angle
        end_angle = (self.current_angle + self.notch_width) % (2 * math.pi)
        if start_angle < end_angle:
            return start_angle <= angle <= end_angle
        else:
            return angle >= start_angle or angle <= end_angle

    def draw(self, surface):
        pygame.draw.circle(surface, BLACK, self.center, self.radius, 2)
        notch_points = []
        num_points = 30
        outer_radius = self.radius
        inner_radius = self.radius - 10
        for i in range(num_points + 1):
            angle = self.current_angle + (self.notch_width * i) / num_points
            x = self.center[0] + outer_radius * math.cos(angle)
            y = self.center[1] + outer_radius * math.sin(angle)
            notch_points.append((x, y))
        for i in range(num_points + 1):
            angle = self.current_angle + self.notch_width - (self.notch_width * i) / num_points
            x = self.center[0] + inner_radius * math.cos(angle)
            y = self.center[1] + inner_radius * math.sin(angle)
            notch_points.append((x, y))
        pygame.draw.polygon(surface, WHITE, notch_points)

class SmallCircle:
    def __init__(self, radius=10, color=RED, speed=4):
        self.radius = radius
        self.color = color
        self.speed = speed
        self.pos = list(CENTER)
        self.set_random_velocity()

    def set_random_velocity(self, incoming_angle=None, spread_deg=90):
        if incoming_angle is not None:
            spread_rad = math.radians(spread_deg)
            min_angle = incoming_angle + math.pi - spread_rad
            max_angle = incoming_angle + math.pi + spread_rad
            min_angle %= 2 * math.pi
            max_angle %= 2 * math.pi
            if min_angle < max_angle:
                direction = random.uniform(min_angle, max_angle)
            else:
                direction = random.uniform(min_angle, 2 * math.pi) if random.random() < ((2 * math.pi - min_angle) / (2 * math.pi - min_angle + max_angle)) else random.uniform(0, max_angle)
        else:
            direction = random.uniform(0, 2 * math.pi)

        self.speed = random.randint(1, 10)
        self.vel = [
            self.speed * math.cos(direction),
            self.speed * math.sin(direction)
        ]

    def update(self, big_circles):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        dist = distance(self.pos, self.center())
        angle = math.atan2(self.pos[1] - self.center()[1], self.pos[0] - self.center()[0])
        sorted_big_circles = sorted(big_circles, key=lambda bc: bc.radius, reverse=True)
        for big_circle in sorted_big_circles:
            if dist + self.radius >= big_circle.radius:
                if big_circle.is_within_notch(angle):
                    self.reset_position()
                    big_circles.remove(big_circle)
                else:
                    incoming_angle = math.atan2(self.vel[1], self.vel[0])
                    self.set_random_velocity(incoming_angle, spread_deg=SPREAD_DEG)
                    overlap = dist + self.radius - big_circle.radius
                    normal = normalize([self.pos[0] - self.center()[0], self.pos[1] - self.center()[1]])
                    self.pos[0] -= overlap * normal[0]
                    self.pos[1] -= overlap * normal[1]
                break

    def center(self):
        return CENTER

    def reset_position(self):
        self.pos = list(CENTER)
        self.set_random_velocity()

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius)

def main():
    num_big_circles = BIG_CIRCLES_NUMBER
    big_circles = []
    radius_increment = (MAX_RADIUS - MIN_RADIUS_INIT) / num_big_circles
    current_radius = MIN_RADIUS_INIT
    for _ in range(num_big_circles):
        current_radius += radius_increment
        angular_speed = random.uniform(15, 45)
        notch_width_deg = random.uniform(20, 30)
        big_circle = BigCircle(center=CENTER, radius=current_radius, notch_width_deg=notch_width_deg, angular_speed_deg_per_sec=angular_speed)
        big_circles.append(big_circle)

    big_circles.sort(key=lambda bc: bc.radius, reverse=True)

    num_circles = NUM_CIRCLES
    colors = [RED, BLUE, GREEN]
    small_circles = [
        SmallCircle(radius=10, color=random.choice(colors), speed=4)
        for _ in range(num_circles)
    ]

    remaining_time = TOTAL_TIME

    state = "running"

    while True:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if state == "running":
            remaining_time -= dt
            if remaining_time <= 0:
                remaining_time = 0
                state = "failure"

            for big_circle in big_circles:
                big_circle.update(dt)

            for circle in small_circles:
                circle.update(big_circles)

            if len(big_circles) == 0:
                state = "victory"

        screen.fill(WHITE)

        if state == "running":
            for big_circle in big_circles:
                big_circle.draw(screen)

            for circle in small_circles:
                circle.draw(screen)

            timer_text = font.render(f"剩余时间: {int(remaining_time)}s", True, BLACK)
            screen.blit(timer_text, (10, 10))

        elif state == "victory":
            victory_text = large_font.render("胜利！", True, GREEN)
            text_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(victory_text, text_rect)

            prompt_text = font.render("按任意键退出", True, BLACK)
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            screen.blit(prompt_text, prompt_rect)

        elif state == "failure":
            failure_text = large_font.render("失败！", True, RED)
            text_rect = failure_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(failure_text, text_rect)

            prompt_text = font.render("按任意键退出", True, BLACK)
            prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            screen.blit(prompt_text, prompt_rect)

        if state in ["victory", "failure"]:
            keys = pygame.key.get_pressed()
            if any(keys):
                pygame.quit()
                sys.exit()

        pygame.display.flip()

if __name__ == "__main__":
    main()
