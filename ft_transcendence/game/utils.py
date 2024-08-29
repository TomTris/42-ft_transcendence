
import random
import math

from .models import width, height, pwidth, pheight, radius, distance, speed

class Player:
    
    def __init__(self, x, y, width, height, play_ground_width, playground_height, direction, speed=40) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.play_ground_width = play_ground_width
        self.playground_height = playground_height
        self.speed = speed
        self.direction = direction

    def update_pos(self, dt):
        if self.direction == 0:
            return
        self.y = self.y + dt * self.speed * self.direction
        if self.y < 0:
            self.y = 0
        if self.y > self.playground_height - self.height:
            self.y = self.playground_height - self.height


def generate_random_angle():
    while True:
        angle = random.uniform(0, 1) * 2.0 * math.pi
        if abs(math.cos(angle)) > 0.5 and abs(math.cos(angle)) < 0.9:
            break
    return angle

def randomize(dx, dy, time_passed):
    if time_passed == 0:
        return dx, dy
    n = random.randint(0, 2)
    f = get_factor(time_passed)
    dx = dx / f
    dy = dy / f
    fac_dx = 1 if dx > 0 else -1
    fac_dy = 1 if dy > 0 else -1
    angle = math.atan(abs(dy / dx))
    new_angle = angle
    if n == 0:
        new_angle += math.pi / 60.0 * random.uniform(0, 1)

    if n == 1:
        new_angle -= math.pi / 60.0 * random.uniform(0, 1)

    if abs(math.cos(new_angle)) > 0.5 and abs(math.cos(new_angle)) < 0.9:
        angle = new_angle
    dx = speed * math.cos(angle) * fac_dx
    dy = speed * math.sin(angle) * fac_dy
    dx *= f
    dy *= f
    return dx, dy


def simulate_ball_position(x, y, dx, dy, dt, players, dts, time_passed=0):
    new_x = x + dx * dt
    new_y = y + dy * dt
    p = 0
    
    if new_x - radius <= 0:  # Left wall collision
        new_x = 2 * radius - new_x
        dx = -dx
        p = 2
    elif new_x + radius >= width:  # Right wall collision
        new_x = 2 * (width - radius) - new_x
        dx = -dx
        p = 1

    if new_y - radius <= 0:  # Bottom wall collision
        new_y = 2 * radius - new_y
        dy = -dy
        dx, dy = randomize(dx, dy, time_passed)
    elif new_y + radius >= height:  # Top wall collision
        new_y = 2 * (height - radius) - new_y
        dy = -dy
        dx, dy = randomize(dx, dy, time_passed)
    
    for ind, player in enumerate(players):

        player.update_pos(dts[ind])

        if (new_x + radius > player.x and new_x - radius < player.x + player.width and
        new_y + radius > player.y and new_y - radius < player.y + player.height):
        

            overlap_x = min(new_x + radius - player.x, player.x + player.width - new_x + radius)
            overlap_y = min(new_y + radius - player.y, player.y + player.height - new_y + radius)

            if overlap_x < overlap_y:

                dx = -dx 
                if new_x < player.x:
                    new_x = player.x - radius  # Adjust position to the left
                else:
                    new_x = player.x + player.width + radius  # Adjust position to the right
            else:
                dy = -dy 
                if new_y < player.y:
                    new_y = player.y - radius  # Adjust position to the top
                else:
                    new_y = player.y + player.height + radius  # Adjust position to the bottom

    return new_x, new_y, dx, dy, p

def get_factor(time):
    return 1 + (((time + 1) ** 0.5) * 0.2)

def update_speed(vecx, vecy, total, delta):
    f1 = get_factor(total)
    f2 = get_factor(total + delta)
    return vecx / f1 * f2, vecy / f1 * f2
