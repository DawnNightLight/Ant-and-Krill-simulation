import csv
import math
import random

import cv2
import numpy as np
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

MAP_SIZE = 50
ANTS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
CENTRE = MAP_SIZE // 2

class Ant:
    def __init__(self, foodspots, label, **kwargs):
        self.label = label
        self.foodspots = foodspots
        self.state = "scouting"
        self.path = []
        self.food_collected = 0
        self.eaten = 0
        self.sight = 3
        self.coordinates = (random.randint(0, MAP_SIZE // 4), random.randint(0, MAP_SIZE // 4))
        self.spot_counter = 0
        self.mainspot = []
        self.path_progress = None
        self.going_to = None
        self.trail_spot = None


    def scout(self):
        x, y = self.coordinates
        max_pos = (x, y)
        max_value = food_map[x][y]
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                cx = x + dx
                cy = y + dy
                # Wrap around the edges of the grid
                if cx < 0:
                    cx = 0
                elif cx > MAP_SIZE - 1:
                    cx = MAP_SIZE - 1
                if cy < 0:
                    cy = 0
                elif cy > MAP_SIZE - 1:
                    cy = MAP_SIZE - 1

                if food_map[cx][cy] > max_value:
                    max_value = food_map[cx][cy]
                    max_pos = (cx, cy)

        if food_map[max_pos[0]][max_pos[1]] > 0:
            self.start_trail(max_pos)
        else:
            x, y = self.coordinates
            dx, dy = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)])
            x += dx
            y += dy
            # Wrap around the edges of the grid
            if x < 0:
                x = 0
            elif x > MAP_SIZE - 1:
                x = MAP_SIZE - 1
            if y < 0:
                y = 0
            elif y > MAP_SIZE - 1:
                y = MAP_SIZE - 1
            self.coordinates = (x, y)

    def start_trail(self, max_pos):
        global obstacle_map, food_map
        x, y = max_pos
        self.trail_spot = max_pos
        self.mainspot = [x, y]
        grid = Grid(matrix=obstacle_map)
        start = grid.node(5, 5)
        end = grid.node(x, y)
        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        self.path, runs = finder.find_path(start, end, grid)
        ants[this_ant_name].path_progress = len(self.path) - 1
        ants[this_ant_name].going_to = False
        self.state = "trailing"

    def trail(self, path):
        global food_store, food_map, empty
        max_food_x, max_food_y = self.mainspot[0], self.mainspot[1]
        if self.going_to:
            if self.path_progress < len(path) - 1:
                self.coordinates = path[self.path_progress]
                self.path_progress += 1
            elif self.path_progress == len(path) - 1:
                self.coordinates = path[self.path_progress]
                if food_map[max_food_x][max_food_y] > 0:
                    food_map[max_food_x][max_food_y] -= 1
                    food_store += 1
                    self.food_collected += 1
                    self.going_to = False
                else:
                    if [self.mainspot[0], self.mainspot[1]] not in empty:
                        empty.append([self.mainspot[0], self.mainspot[1]])
                    self.mainspot = []
                    self.state = "scouting"
        else:
            if 0 < self.path_progress < len(path):
                self.coordinates = path[self.path_progress]
                self.path_progress -= 1
            elif self.path_progress == 0:
                self.coordinates = path[self.path_progress]
                self.going_to = True
            else:
                print("ERROR")


# creates a circle of values that decrease the further they get from the main spot
def generate_food():
    food_map = [[random.randint(1, 15) for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
    for i in range(0, 3):
        foodspot_x = random.randrange(0, 10)
        foodspot_y = random.randrange(0, 10)
        food_map[foodspot_x][foodspot_y] = random.randrange(MAP_SIZE, MAP_SIZE + 10)
        foodspots.append((foodspot_x, foodspot_y))
        x1 = foodspot_x - 5
        y1 = foodspot_y - 5
        x2 = foodspot_x + 5
        y2 = foodspot_y + 5
        if x2 > MAP_SIZE - 1:
            x2 = 9
        if y2 > MAP_SIZE - 1:
            y2 = 9
        if x1 < 0:
            x1 = 0
        if y1 < 0:
            y1 = 0
        for xspot in range(x1, x2 + 1):
            for yspot in range(y1, y2 + 1):
                if -6 < foodspot_x - xspot < 6 or -6 < foodspot_y - yspot > 6:
                    if yspot >= 0 and xspot >= 0:
                        distance = int(math.sqrt(
                            (foodspot_x - xspot) * (foodspot_x - xspot) + (foodspot_y - yspot) * (foodspot_y - yspot)))
                        if not distance == 0 and -6 < distance < 6:
                            food_map[xspot][yspot] = int((1 / distance) * 45)
    return food_map

def food_empty():
    for tmp in food_map:
        for t in tmp:
            if t > 0:
                return False
    return True

def draw_food(img, food_map, thickness = -1, grid_shape=(MAP_SIZE, MAP_SIZE)):
    h, w, _ = img.shape
    rows, cols = grid_shape
    dy, dx = h / rows, w / cols
    for i in range(len(food_map)):
        for j in range(len(food_map[i])):
            g = int(food_map[i][j]) *2
            start_point = (int(i * dx), int(j * dy))
            end_point =(int((i + 1) * dx), int((j + 1) * dy))
            color = (0,g,0)
            g = max(255, g)
            img = cv2.rectangle(img, start_point, end_point, color, thickness)


def draw_grid(img, grid_shape=(MAP_SIZE, MAP_SIZE), color=(0, 0, 255), thickness=1):
    h, w, _ = img.shape
    rows, cols = grid_shape
    dy, dx = h / rows, w / cols
    # draw vertical lines
    for x in np.linspace(start=dx, stop=w-dx, num=cols-1):
        x = int(round(x))
    # draw horizontal lines
    for y in np.linspace(start=dy, stop=h-dy, num=rows-1):
        y = int(round(y))
    return img

def draw_map(food_map, ants, grid_shape=(MAP_SIZE, MAP_SIZE)):
    global videoWriter
    img = np.full((700, 700, 3), (255, 255, 255), dtype=('uint8'))
    img.fill(255)
    draw_food(img, food_map)
    img = draw_grid(img, grid_shape)

    for ant in ants.values():
        draw_ant(img, ant)
    cv2.imshow('tmp', img)
    videoWriter.write(img)
    cv2.waitKey(1)

def draw_ant(img, ant, grid_shape=(MAP_SIZE, MAP_SIZE)):
    h, w, _ = img.shape
    rows, cols = grid_shape
    dy, dx = h / rows, w / cols
    i, j = ant.coordinates
    offset = int(dx/4)
    start_point = (int(i * dx) + offset, int(j * dy) + offset)
    end_point = (int((i + 1) * dx) - offset, int((j + 1) * dy) - offset)
    img = cv2.rectangle(img, start_point, end_point, (255, 0, 0), -1)

for ant_number in ANTS:
    results = {}
    average_total = 0
    average_time = 0
    average_min = 0
    average_max = 0
    time_cache = []
    total_cache = []
    min_cache = []
    max_cache = []
    for run_index in range(1):
        # Initialize the memory for empty tiles
        empty = []
        tmp_empty = empty.copy()
        time = 0
        obstacle_map = [[1 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
        foodspots = []
        food_store = 0
        food_map = generate_food()
        ants = {}

        food_map[5][5] = 0
        for i in range(ant_number):
            ants[f"Ant {i + 1}"] = Ant(foodspots, f"Ant {i + 1}")
        videoWriter = cv2.VideoWriter("Results/ant_video.mp4", cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 24, (700, 700))
        while (not food_empty()):
            if tmp_empty != empty:
                tmp_empty = empty.copy()
            draw_map(food_map, ants)
            for this_ant_name in ants.keys():
                this_ant = ants[this_ant_name]
                if this_ant.state == "scouting":
                    this_ant.scout()
                elif this_ant.state == "trailing":
                    x, y = this_ant.path[len(this_ant.path) - 1]
                    global_change_destination = False
                    for other_ant_name in ants.keys():
                        local_change_destination = False
                        other_ant = ants[other_ant_name]
                        if other_ant_name != this_ant_name and this_ant.coordinates == other_ant.coordinates:
                            if this_ant.mainspot == [] and other_ant.mainspot != []:
                                this_ant.mainspot = other_ant.mainspot
                            elif other_ant.mainspot == [] and this_ant.mainspot != []:
                                other_ant.mainspot = this_ant.mainspot
                            elif this_ant.mainspot != [] and other_ant.mainspot != []:
                                # Find the best spot known to this person
                                [myX, myY] = this_ant.mainspot
                                my_best_spot_food_amount = food_map[myX][myY]
                                # Find the best spot known to the other person
                                if len(other_ant.mainspot) > 0:
                                    otherX, otherY = other_ant.mainspot[0], other_ant.mainspot[1]
                                    other_best_spot_food_amount = food_map[otherX][otherY]
                                    if other_best_spot_food_amount > my_best_spot_food_amount:
                                        # Replace this person's memory of the best spot with the other person's memory of the best spot
                                        this_ant.mainspot = [otherX, otherY]
                                        local_change_destination = True
                                    elif other_best_spot_food_amount < my_best_spot_food_amount:
                                        other_ant.mainspot = [myX, myY]
                                        local_change_destination = True
                                    else:
                                        local_change_destination = False
                                else:
                                    other_ant.mainspot = [myX, myY]
                                    local_change_destination = True
                            if local_change_destination:
                                global_change_destination = True
                    if not global_change_destination:
                        this_ant.trail(this_ant.path)
                else:
                    print("ERROR")
                    exit()
            time += 1

        print("")
        print(f"{len(ants.keys())} ants collected {food_store} units of food.")
        print(f"The total elapsed time was {time}s, or {int(time / 60)}m {time - int(time / 60) * 60}s, or {int(time / 60 / 60)}h {int(time / 60) - int(time / 60 / 60) * 60}m {time - int(time / 60) * 60}s.")

        # Initialize the minimum value to the first number in the list
        min_value = ants["Ant 1"].food_collected
        max_value = ants["Ant 1"].food_collected
        # Use a for loop to find the minimum value
        for this_ant_name in ants.values():
            # Update the minimum value if a smaller number is found
            if this_ant_name.food_collected < min_value:
                min_value = this_ant_name.food_collected
            elif this_ant_name.food_collected > max_value:
                max_value = this_ant_name.food_collected

        total_cache.append(food_store)
        time_cache.append(time)
        min_cache.append(min_value)
        max_cache.append(max_value)
        results[run_index] = {"antnum": ant_number, "time": time, "total": food_store, "min": min_value, "max": max_value}

    videoWriter.release()

    for i in total_cache:
        average_total += i
    average_total = average_total // len(total_cache)

    for i in time_cache:
        average_time += i
    average_time = average_time // len(time_cache)

    for i in min_cache:
        average_min += i
    average_min = average_min // len(min_cache)

    for i in max_cache:
        average_max += i
    average_max = average_max // len(max_cache)

    # open a file for writing
    with open(f"Results\MapSize10\Ants\ChangingAntNum.csv", "a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["antnum","time", "total", "min", "max", "\n"])
        # write the data
        for result in results.values():
            writer.writerow(result)

