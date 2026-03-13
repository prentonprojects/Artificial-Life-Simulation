import math
import random
import pygame

# =========================
# Config
# =========================
WIDTH, HEIGHT = 1200, 800
FPS = 60

INITIAL_ORGANISMS = 25
INITIAL_FOOD = 120
MAX_FOOD = 180

FOOD_ENERGY = 22
FOOD_SPAWN_CHANCE = 0.18  # per frame chance

BACKGROUND = (18, 18, 24)
FOOD_COLOR = (80, 220, 120)
TEXT_COLOR = (230, 230, 230)

# =========================
# Pygame setup
# =========================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Artificial Life Simulation")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 20)
small_font = pygame.font.SysFont("consolas", 16)

# =========================
# Helpers
# =========================
def clamp(value, low, high):
    return max(low, min(high, value))

def random_position():
    return random.uniform(30, WIDTH - 30), random.uniform(30, HEIGHT - 30)

# =========================
# Food
# =========================
class Food:
    def __init__(self):
        self.x, self.y = random_position()
        self.radius = 4

    def draw(self, surface):
        pygame.draw.circle(surface, FOOD_COLOR, (int(self.x), int(self.y)), self.radius)

# =========================
# Organism
# =========================
class Organism:
    def __init__(self, x=None, y=None, genes=None, generation=1):
        self.x, self.y = (random_position() if x is None or y is None else (x, y))
        self.generation = generation

        if genes is None:
            self.genes = {
                "size": random.uniform(6, 13),
                "speed": random.uniform(0.8, 2.2),
                "vision": random.uniform(40, 130),
                "efficiency": random.uniform(0.7, 1.3),
                "reproduction_threshold": random.uniform(90, 145),
            }
        else:
            self.genes = genes

        self.energy = random.uniform(55, 95)
        self.direction = random.uniform(0, math.pi * 2)
        self.turn_rate = random.uniform(0.02, 0.08)
        self.alive = True
        self.age = 0

    @property
    def size(self):
        return self.genes["size"]

    @property
    def speed(self):
        return self.genes["speed"]

    @property
    def vision(self):
        return self.genes["vision"]

    @property
    def efficiency(self):
        return self.genes["efficiency"]

    @property
    def reproduction_threshold(self):
        return self.genes["reproduction_threshold"]

    def mutate_genes(self):
        child_genes = self.genes.copy()
        mutation_strength = 0.12

        for key in child_genes:
            factor = random.uniform(1 - mutation_strength, 1 + mutation_strength)
            child_genes[key] *= factor

        child_genes["size"] = clamp(child_genes["size"], 4, 18)
        child_genes["speed"] = clamp(child_genes["speed"], 0.5, 3.2)
        child_genes["vision"] = clamp(child_genes["vision"], 20, 200)
        child_genes["efficiency"] = clamp(child_genes["efficiency"], 0.4, 1.8)
        child_genes["reproduction_threshold"] = clamp(child_genes["reproduction_threshold"], 70, 190)

        return child_genes

    def find_nearest_food(self, food_list):
        nearest = None
        nearest_dist = float("inf")

        for food in food_list:
            dx = food.x - self.x
            dy = food.y - self.y
            dist = math.hypot(dx, dy)

            if dist < nearest_dist and dist <= self.vision:
                nearest = food
                nearest_dist = dist

        return nearest, nearest_dist

    def move(self, food_list):
        target, dist = self.find_nearest_food(food_list)

        if target:
            angle_to_target = math.atan2(target.y - self.y, target.x - self.x)
            self.direction += clamp(angle_to_target - self.direction, -self.turn_rate, self.turn_rate)
        else:
            self.direction += random.uniform(-self.turn_rate, self.turn_rate)

        self.x += math.cos(self.direction) * self.speed
        self.y += math.sin(self.direction) * self.speed

        # bounce from walls
        if self.x < self.size:
            self.x = self.size
            self.direction = math.pi - self.direction
        elif self.x > WIDTH - self.size:
            self.x = WIDTH - self.size
            self.direction = math.pi - self.direction

        if self.y < self.size:
            self.y = self.size
            self.direction = -self.direction
        elif self.y > HEIGHT - self.size:
            self.y = HEIGHT - self.size
            self.direction = -self.direction

    def consume_energy(self):
        base_cost = 0.035
        movement_cost = (self.speed * 0.045 + self.size * 0.02 + self.vision * 0.0009) / self.efficiency
        self.energy -= (base_cost + movement_cost)
        self.age += 1

        if self.energy <= 0:
            self.alive = False

    def eat(self, food_list):
        for food in food_list[:]:
            if math.hypot(self.x - food.x, self.y - food.y) <= self.size + food.radius:
                self.energy += FOOD_ENERGY * self.efficiency
                food_list.remove(food)

    def reproduce(self):
        if self.energy >= self.reproduction_threshold:
            self.energy *= 0.52
            child_genes = self.mutate_genes()

            child = Organism(
                x=self.x + random.uniform(-12, 12),
                y=self.y + random.uniform(-12, 12),
                genes=child_genes,
                generation=self.generation + 1
            )
            child.energy = self.energy * 0.7
            return child
        return None

    def update(self, food_list):
        if not self.alive:
            return None

        self.move(food_list)
        self.consume_energy()
        self.eat(food_list)

        if not self.alive:
            return None

        return self.reproduce()

    def get_color(self):
        # Color reflects genes for visual diversity
        r = int(clamp(90 + self.speed * 50, 50, 255))
        g = int(clamp(80 + self.efficiency * 90, 50, 255))
        b = int(clamp(100 + self.vision * 0.8, 50, 255))
        return (r, g, b)

    def draw(self, surface, selected=False):
        color = self.get_color()
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(self.size))

        # direction indicator
        dx = math.cos(self.direction) * self.size
        dy = math.sin(self.direction) * self.size
        pygame.draw.line(
            surface,
            (255, 255, 255),
            (int(self.x), int(self.y)),
            (int(self.x + dx), int(self.y + dy)),
            1
        )

        if selected:
            pygame.draw.circle(surface, (255, 255, 120), (int(self.x), int(self.y)), int(self.vision), 1)

# Simulation
class Simulation:
    def __init__(self):
        self.organisms = [Organism() for _ in range(INITIAL_ORGANISMS)]
        self.food = [Food() for _ in range(INITIAL_FOOD)]
        self.paused = False
        self.selected = None
        self.tick = 0

    def spawn_food(self):
        if len(self.food) < MAX_FOOD and random.random() < FOOD_SPAWN_CHANCE:
            self.food.append(Food())

    def update(self):
        if self.paused:
            return

        self.tick += 1
        self.spawn_food()

        new_organisms = []

        for organism in self.organisms:
            child = organism.update(self.food)
            if child:
                new_organisms.append(child)

        self.organisms = [o for o in self.organisms if o.alive]
        self.organisms.extend(new_organisms)

        # ensure simulation doesn't die too early
        if len(self.organisms) == 0:
            self.organisms = [Organism() for _ in range(INITIAL_ORGANISMS // 2)]
            self.food.extend(Food() for _ in range(50))

    def draw(self, surface):
        surface.fill(BACKGROUND)

        for food in self.food:
            food.draw(surface)

        for organism in self.organisms:
            organism.draw(surface, selected=(organism == self.selected))

        self.draw_hud(surface)

    def draw_hud(self, surface):
        pop = len(self.organisms)
        food_count = len(self.food)

        if pop > 0:
            avg_speed = sum(o.speed for o in self.organisms) / pop
            avg_size = sum(o.size for o in self.organisms) / pop
            avg_vision = sum(o.vision for o in self.organisms) / pop
            max_gen = max(o.generation for o in self.organisms)
        else:
            avg_speed = avg_size = avg_vision = max_gen = 0

        lines = [
            f"Population: {pop}",
            f"Food: {food_count}",
            f"Max Generation: {max_gen}",
            f"Avg Speed: {avg_speed:.2f}",
            f"Avg Size: {avg_size:.2f}",
            f"Avg Vision: {avg_vision:.2f}",
            f"Paused: {'Yes' if self.paused else 'No'}",
            "",
            "Controls:",
            "SPACE = pause",
            "R = reset",
            "Left click = inspect organism",
        ]

        panel = pygame.Surface((280, 260), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        surface.blit(panel, (10, 10))

        y = 18
        for line in lines:
            text = font.render(line, True, TEXT_COLOR)
            surface.blit(text, (20, y))
            y += 22

        if self.selected and self.selected in self.organisms:
            o = self.selected
            inspect_panel = pygame.Surface((360, 170), pygame.SRCALPHA)
            inspect_panel.fill((0, 0, 0, 160))
            surface.blit(inspect_panel, (10, HEIGHT - 180))

            inspect_lines = [
                "Selected Organism",
                f"Generation: {o.generation}",
                f"Energy: {o.energy:.1f}",
                f"Size: {o.size:.2f}",
                f"Speed: {o.speed:.2f}",
                f"Vision: {o.vision:.2f}",
                f"Efficiency: {o.efficiency:.2f}",
                f"Reproduction Threshold: {o.reproduction_threshold:.2f}",
            ]

            y = HEIGHT - 170
            for i, line in enumerate(inspect_lines):
                text_surface = (font if i == 0 else small_font).render(line, True, TEXT_COLOR)
                surface.blit(text_surface, (20, y))
                y += 20

    def reset(self):
        self.__init__()

    def select_organism(self, mouse_pos):
        mx, my = mouse_pos
        closest = None
        closest_dist = float("inf")

        for organism in self.organisms:
            dist = math.hypot(mx - organism.x, my - organism.y)
            if dist < organism.size + 6 and dist < closest_dist:
                closest = organism
                closest_dist = dist

        self.selected = closest

# Main loop
def main():
    sim = Simulation()
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    sim.paused = not sim.paused
                elif event.key == pygame.K_r:
                    sim.reset()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    sim.select_organism(event.pos)

        sim.update()
        sim.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

