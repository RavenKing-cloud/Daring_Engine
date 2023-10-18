import pygame
import sys
import random
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 8  # Adjust this to your grid size
FPS = 120
PUCK_RADIUS = 8
COLLISION_RADIUS = 7  # Set your desired collision radius here
PUCK_COUNT = 50
MAX_LIVES = 100  # Maximum number of lives

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (255, 0, 0)
PINK = (255, 0, 200)
PURPLE = (120, 0, 200)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)  # Blue color for walls

# Calculate the border thickness based on grid size
GRID_BORDER = GRID_SIZE  # You can adjust this to control the border thickness

# Pygame setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Puck-Wall Collision Simulation")
clock = pygame.time.Clock()

# Minimum velocity threshold (you can adjust this value)
MIN_VELOCITY_THRESHOLD = 1.33

# Modify the entity_collision function
def entity_collision(entity1, entity2):
    offset = (int(entity2.x - entity1.x), int(entity2.y - entity1.y))

    if entity1.mask.overlap(entity2.mask, offset):
        distance = math.sqrt((entity2.x - entity1.x) ** 2 + (entity2.y - entity1.y) ** 2)

        if distance < 2 * entity1.collision_radius:
            dx = entity2.x - entity1.x
            dy = entity2.y - entity1.y
            norm = math.sqrt(dx ** 2 + dy ** 2)
            if norm != 0:
                dx /= norm
                dy /= norm

            nudging_distance = (2 * entity1.collision_radius - distance) / 4
            entity1.x -= dx * nudging_distance
            entity1.y -= dy * nudging_distance
            entity2.x += dx * nudging_distance
            entity2.y += dy * nudging_distance

        dx = entity2.x - entity1.x
        dy = entity2.y - entity1.y
        normal = math.sqrt(dx ** 2 + dy ** 2)
        nx = dx / normal
        ny = dy / normal
        relative_vel_x = entity1.vx - entity2.vx
        relative_vel_y = entity1.vy - entity2.vy
        dot_product = relative_vel_x * nx + relative_vel_y * ny
        impulse = (2 * dot_product) / (entity1.mass + entity2.mass)

        slipperiness = 0.9  # You can adjust this value
        impulse *= slipperiness

        # Check if the collision is from the outside
        if dot_product > 0:
            entity1.vx -= impulse * entity2.mass * nx
            entity1.vy -= impulse * entity2.mass * ny
            entity2.vx += impulse * entity1.mass * nx
            entity2.vy += impulse * entity1.mass * ny

class Entity:
    def __init__(self, x, y, vx, vy, mass, drawn_radius, collision_radius):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.mass = mass
        self.radius = drawn_radius
        self.collision_radius = collision_radius
        self.active = True

        self.rect = pygame.Rect(x - collision_radius, y - collision_radius, collision_radius * 2, collision_radius * 2)
        
        mask_surface = pygame.Surface((collision_radius * 2, collision_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(mask_surface, BLACK, (collision_radius, collision_radius), collision_radius)
        self.mask = pygame.mask.from_surface(mask_surface)

    def entity_collision(self, other_entity):
        offset = (int(other_entity.x - self.x), int(other_entity.y - self.y))
        return self.mask.overlap(other_entity.mask, offset)

class Puck(Entity):
    def __init__(self, x, y, vx, vy, mass, drawn_radius, collision_radius):
        super().__init__(x, y, vx, vy, mass, drawn_radius, collision_radius)

class Zone(Entity):
    def __init__(self, x, y, width, height, drawn_color, collision_color):
        super().__init__(x, y, 0, 0, 0, 0, 0)
        self.width = width
        self.height = height
        self.drawn_color = drawn_color
        self.collision_color = collision_color

        self.rect = pygame.Rect(x, y, width, height)

        drawn_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(drawn_surface, drawn_color, (0, 0, width, height))
        self.drawn_mask = pygame.mask.from_surface(drawn_surface)

        collision_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(collision_surface, collision_color, (0, 0, width, height))
        self.collision_mask = pygame.mask.from_surface(collision_surface)

class SpawnerBoxZone:
    def __init__(self, x, y, width, height, drawn_color, collision_color, spawn_cooldown=1000, initial_spawn_delay=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.drawn_color = drawn_color
        self.collision_color = collision_color
        self.velocity_x = 0
        self.velocity_y = 0
        self.mass = 0
        self.angle = 0
        self.spawn_cooldown = spawn_cooldown  # Cooldown time between puck spawns in milliseconds
        self.initial_spawn_delay = initial_spawn_delay  # Delay before the first spawn in milliseconds
        self.last_spawn_time = pygame.time.get_ticks()
        self.has_spawned_initial_puck = False

    def set_parameters(self, velocity_x, velocity_y, mass, angle):
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.mass = mass
        self.angle = angle

    def spawn_puck(self, pucks, dt):
        current_time = pygame.time.get_ticks()
        
        if not self.has_spawned_initial_puck and current_time >= self.initial_spawn_delay:
            # Initial puck spawn after the initial delay
            x = self.rect.centerx
            y = self.rect.centery
            angle_rad = math.radians(self.angle)
            vx = self.velocity_x * math.cos(angle_rad)
            vy = self.velocity_y * math.sin(angle_rad)
            pucks.append(Puck(x, y, vx, vy, self.mass, PUCK_RADIUS, COLLISION_RADIUS))
            self.last_spawn_time = current_time
            self.has_spawned_initial_puck = True
        elif current_time - self.last_spawn_time >= self.spawn_cooldown:
            # Regular puck spawn after the cooldown period
            x = self.rect.centerx
            y = self.rect.centery
            angle_rad = math.radians(self.angle)
            vx = self.velocity_x * math.cos(angle_rad)
            vy = self.velocity_y * math.sin(angle_rad)
            pucks.append(Puck(x, y, vx, vy, self.mass, PUCK_RADIUS, COLLISION_RADIUS))
            self.last_spawn_time = current_time

class FrictionZone(Zone):
    def __init__(self, x, y, width, height, friction):
        super().__init__(x, y, width, height, RED, GREEN)
        self.friction = friction

    def apply_friction(self, puck):
        puck_left = puck.x - puck.radius
        puck_right = puck.x + puck.radius
        puck_top = puck.y - puck.radius
        puck_bottom = puck.y + puck.radius

        box_left = self.rect.left
        box_right = self.rect.right
        box_top = self.rect.top
        box_bottom = self.rect.bottom

        puck_overlap_x = max(0, min(puck_right, box_right) - max(puck_left, box_left))
        puck_overlap_y = max(0, min(puck_bottom, box_bottom) - max(puck_top, box_top))

        puck_overlap_area = puck_overlap_x * puck_overlap_y
        puck_area = math.pi * (puck.radius ** 2)

        if puck_overlap_area >= 0.33 * puck_area:
            # Apply friction to the puck's velocities
            puck.vx *= self.friction
            puck.vy *= self.friction

class KillBox(Zone):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, BLACK, WHITE)

    def check_collision(self, puck):
        puck_left = puck.x - puck.radius
        puck_right = puck.x + puck.radius
        puck_top = puck.y - puck.radius
        puck_bottom = puck.y + puck.radius

        box_left = self.rect.left
        box_right = self.rect.right
        box_top = self.rect.top
        box_bottom = self.rect.bottom

        puck_overlap_x = max(0, min(puck_right, box_right) - max(puck_left, box_left))
        puck_overlap_y = max(0, min(puck_bottom, box_bottom) - max(puck_top, box_top))

        puck_overlap_area = puck_overlap_x * puck_overlap_y
        puck_area = math.pi * (puck.radius ** 2)

        if puck_overlap_area >= 0.60 * puck_area:
            puck.active = False

class Booster(Zone):
    def __init__(self, x, y, width, height, boost_velocity):
        super().__init__(x, y, width, height, YELLOW, BLUE)
        self.boost_velocity = boost_velocity
        self.pucks_passed = set()

    def apply_boost(self, puck):
        puck_left = puck.x - puck.radius
        puck_right = puck.x + puck.radius
        puck_top = puck.y - puck.radius
        puck_bottom = puck.y + puck.radius

        box_left = self.rect.left
        box_right = self.rect.right
        box_top = self.rect.top
        box_bottom = self.rect.bottom

        puck_overlap_x = max(0, min(puck_right, box_right) - max(puck_left, box_left))
        puck_overlap_y = max(0, min(puck_bottom, box_bottom) - max(puck_top, box_top))

        puck_overlap_area = puck_overlap_x * puck_overlap_y
        puck_area = math.pi * (puck.radius ** 2)

        if puck_overlap_area >= 0.51 * puck_area:
            # Calculate the direction vector of the puck's current velocity
            velocity_magnitude = math.sqrt(puck.vx ** 2 + puck.vy ** 2)
            if velocity_magnitude != 0:
                dx = puck.vx / velocity_magnitude
                dy = puck.vy / velocity_magnitude

                # Apply the boost in the direction of the current velocity
                puck.vx += self.boost_velocity * dx
                puck.vy += self.boost_velocity * dy

                # Mark the puck as boosted
                self.pucks_passed.add(puck)

class Magnet(Zone):
    def __init__(self, x, y, radius, pull_speed, inactivation_threshold, velocity_cap):
        super().__init__(x, y, radius * 2, radius * 2, BLUE, YELLOW)
        self.radius = radius
        self.pull_speed = pull_speed
        self.inactivation_threshold = inactivation_threshold
        self.velocity_cap = velocity_cap  # Maximum velocity allowed inside the magnet zone
        self.magnetized_pucks = set()  # Keep track of magnetized pucks

    def apply_magnetism(self, puck):
        # Calculate the distance between the puck and the center of the magnet
        dx = self.rect.centerx - puck.x
        dy = self.rect.centery - puck.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Check if the puck is inside the magnet's circular area
        if puck not in self.magnetized_pucks and distance <= self.radius + puck.radius:
            self.magnetized_pucks.add(puck)  # Mark the puck as magnetized

        # Apply magnetism to all magnetized pucks
        for magnetized_puck in self.magnetized_pucks.copy():
            dx = self.rect.centerx - magnetized_puck.x
            dy = self.rect.centery - magnetized_puck.y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            # Calculate the direction vector from the puck to the center of the magnet
            if distance != 0:
                dx /= distance
                dy /= distance

            # Calculate the desired distance from the puck to the center of the magnet
            desired_distance = self.radius - magnetized_puck.radius

            # Cap the velocity if it exceeds the velocity_cap
            velocity_magnitude = math.sqrt(magnetized_puck.vx ** 2 + magnetized_puck.vy ** 2)
            if velocity_magnitude > self.velocity_cap:
                scale_factor = self.velocity_cap / velocity_magnitude
                magnetized_puck.vx *= scale_factor
                magnetized_puck.vy *= scale_factor

            # Move the puck towards the center of the magnet with the specified pull_speed
            move_distance = min(self.pull_speed, desired_distance)
            magnetized_puck.x += dx * move_distance
            magnetized_puck.y += dy * move_distance

            # Check if the puck has reached the center of the magnet
            if distance <= magnetized_puck.radius:
                # Check if the puck's velocity is below the inactivation threshold
                velocity_magnitude = math.sqrt(magnetized_puck.vx ** 2 + magnetized_puck.vy ** 2)
                if velocity_magnitude <= self.inactivation_threshold:
                    magnetized_puck.active = False
                    self.magnetized_pucks.remove(magnetized_puck)  # Remove from magnetized pucks set

class Goal(Zone):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, BLACK, WHITE)

    def check_collision(self, puck):
        puck_left = puck.x - puck.radius
        puck_right = puck.x + puck.radius
        puck_top = puck.y - puck.radius
        puck_bottom = puck.y + puck.radius

        box_left = self.rect.left
        box_right = self.rect.right
        box_top = self.rect.top
        box_bottom = self.rect.bottom

        puck_overlap_x = max(0, min(puck_right, box_right) - max(puck_left, box_left))
        puck_overlap_y = max(0, min(puck_bottom, box_bottom) - max(puck_top, box_top))

        puck_overlap_area = puck_overlap_x * puck_overlap_y
        puck_area = math.pi * (puck.radius ** 2)

        if puck_overlap_area >= 0.99 * puck_area:
            puck.active = False

# Function to reset the simulation
def reset_simulation(pucks):
    pucks.clear()
    for _ in range(PUCK_COUNT):
        while True:
            x = random.randint(PUCK_RADIUS + GRID_BORDER, WIDTH - PUCK_RADIUS - GRID_BORDER)
            y = random.randint(PUCK_RADIUS + GRID_BORDER, HEIGHT - PUCK_RADIUS - GRID_BORDER)
            valid_spawn = True
            for puck in pucks:
                if math.sqrt((puck.x - x) ** 2 + (puck.y - y) ** 2) < 2 * COLLISION_RADIUS:
                    valid_spawn = False
                    break
            if valid_spawn:
                break
        vx = random.uniform(-200, 200)
        vy = random.uniform(-200, 200)
        if abs(vx) < MIN_VELOCITY_THRESHOLD:
            vx = MIN_VELOCITY_THRESHOLD if vx < 0 else -MIN_VELOCITY_THRESHOLD

        if abs(vy) < MIN_VELOCITY_THRESHOLD:
            vy = MIN_VELOCITY_THRESHOLD if vy < 0 else -MIN_VELOCITY_THRESHOLD

        mass = 6
        pucks.append(Puck(x, y, vx, vy, mass, PUCK_RADIUS, COLLISION_RADIUS))

# Initialize lives
lives = MAX_LIVES

# Initial reset
pucks = []
reset_simulation(pucks)

friction_zone = FrictionZone(100, 100, 200, 100, 0.965)
kill_box = KillBox(8, 468, 124, 124)
booster = Booster(600, 200, 50, 250, 6.25)
magnet = Magnet(300, 400, 50, 0.12, 1.0, 10.0)
spawner_box_zone1 = SpawnerBoxZone(225, 200, 24, 24, PURPLE, PURPLE, spawn_cooldown=2500, initial_spawn_delay=2500)
spawner_box_zone1.set_parameters(velocity_x=325, velocity_y=325, mass=6, angle=45)
spawner_box_zone2 = SpawnerBoxZone(250, 200, 24, 24, PURPLE, PURPLE, spawn_cooldown=2500, initial_spawn_delay=2500)
spawner_box_zone2.set_parameters(velocity_x=325, velocity_y=325, mass=6, angle=45)
spawner_box_zone3 = SpawnerBoxZone(275, 200, 24, 24, PURPLE, PURPLE, spawn_cooldown=2500, initial_spawn_delay=2500)
spawner_box_zone3.set_parameters(velocity_x=325, velocity_y=325, mass=6, angle=45)
# Add these spawner boxes to a list if needed
spawner_boxes = [spawner_box_zone1, spawner_box_zone2, spawner_box_zone3]

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    dt = clock.tick(FPS) / 120.0

    # Handle puck collisions using entity_collision
    for i in range(len(pucks)):
        for j in range(i + 1, len(pucks)):
            if pucks[i].active and pucks[j].active:
                entity_collision(pucks[i], pucks[j])

    # Apply friction from FrictionZone
    for puck in pucks:
        friction_zone.apply_friction(puck)

    # Check for collisions with KillBox
    for puck in pucks:
        kill_box.check_collision(puck)

    # Apply boost from Booster
    for puck in pucks:
        booster.apply_boost(puck)

    # Apply magnetism from Magnet
    for puck in pucks:
        magnet.apply_magnetism(puck)

    for spawner_box in spawner_boxes:
        spawner_box.spawn_puck(pucks, dt)

    # Move and update pucks
    for puck in pucks:
        if puck.active:
            puck.vx *= 0.991
            puck.vy *= 0.991

            puck.x += puck.vx * dt
            puck.y += puck.vy * dt

            if (puck.x - puck.radius < GRID_BORDER) and puck.vx < 0:
                puck.vx = -puck.vx
            elif (puck.x + puck.radius > WIDTH - GRID_BORDER) and puck.vx > 0:
                puck.vx = -puck.vx

            if (puck.y - puck.radius < GRID_BORDER) and puck.vy < 0:
                puck.vy = -puck.vy
            elif (puck.y + puck.radius > HEIGHT - GRID_BORDER) and puck.vy > 0:
                puck.vy = -puck.vy

            velocity_magnitude = math.sqrt(puck.vx ** 2 + puck.vy ** 2)
            if velocity_magnitude < MIN_VELOCITY_THRESHOLD:
                puck.active = False

    screen.fill(WHITE)
    pygame.draw.rect(screen, BLUE, (0, 0, WIDTH, GRID_BORDER))
    pygame.draw.rect(screen, BLUE, (0, 0, GRID_BORDER, HEIGHT))
    pygame.draw.rect(screen, BLUE, (0, HEIGHT - GRID_BORDER, WIDTH, GRID_BORDER))
    pygame.draw.rect(screen, BLUE, (WIDTH - GRID_BORDER, 0, GRID_BORDER, HEIGHT))

    pygame.draw.rect(screen, YELLOW, friction_zone.rect, 2)
    pygame.draw.rect(screen, RED, kill_box.rect, 2)
    pygame.draw.rect(screen, GREEN, booster.rect, 2)

    # Draw Magnet
    pygame.draw.circle(screen, PINK, (magnet.rect.centerx, magnet.rect.centery), magnet.radius)

    # Draw SpawnerBox
    pygame.draw.rect(screen, PURPLE, spawner_box_zone1.rect, 2)
    pygame.draw.rect(screen, PURPLE, spawner_box_zone2.rect, 2)
    pygame.draw.rect(screen, PURPLE, spawner_box_zone3.rect, 2)

    for puck in pucks:
        if puck.active:
            pygame.draw.circle(screen, BLACK, (int(puck.x), int(puck.y)), puck.radius)

    pucks = [puck for puck in pucks if puck.active]

    if not pucks:
        lives -= 1
        if lives > 0:
            reset_simulation(pucks)
        else:
            running = False

    pygame.display.flip()

pygame.quit()
sys.exit()