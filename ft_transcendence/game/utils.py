

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