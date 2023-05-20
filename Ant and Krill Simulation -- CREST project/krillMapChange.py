import csv
import random
import math

import cv2
import numpy as np
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

# CONSTANTS
KRILL = [100, 125, 150, 175, 200]
MAP_SIZES = [10, 20, 30, 40, 50]
KRILL = 100

# creates a circle of values that decrease the further they get from the main spot
def generate_food():
    food_map = [[random.randint(1, 15) for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
    for i in range(0, 3):
        foodspot_x = random.randrange(0, 10)
        foodspot_y = random.randrange(0, 10)
        food_map[foodspot_x][foodspot_y] = random.randrange(50, 60)
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


for MAP_SIZE in MAP_SIZES:
    # results
    run = 1
    results = {}
    average_total = 0
    average_time = 0
    time_cache = []
    total_cache = []

    for run in range(3):
        # Initialize the memory for empty tiles
        empty = []

        dead_krill = 0

        # Initialize timer
        time = 0

        # Create a 10x10 grid of random values between 1 and 50 and 10x10 grid which is empty
        foodspots = []
        food_map = generate_food()
        obstacle_map = [[1 for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]

        # Spawn KRILL krill at random locations on the food_map
        krill = {}
        for i in range(KRILL):
            krill[i] = {"dead": False, "time": 0, "coordinates": (random.randint(0, MAP_SIZE // 4), random.randint(0, MAP_SIZE // 4)),
                        "state": "scouting", "mainspot": None, "path": [], "going_to": False, "path_progress": 0, "trail_spot": (0, 0),
                        "food_collected": 0}

        # Initialize the food store
        food_store = 0


        def draw_food(img, food_map, thickness=-1, grid_shape=(MAP_SIZE, MAP_SIZE)):
            h, w, _ = img.shape
            rows, cols = grid_shape
            dy, dx = h / rows, w / cols
            for i in range(len(food_map)):
                for j in range(len(food_map[i])):
                    g = int(food_map[i][j]) * 2
                    start_point = (int(i * dx), int(j * dy))
                    end_point = (int((i + 1) * dx), int((j + 1) * dy))
                    color = (0, g, 0)
                    g = max(255, g)
                    img = cv2.rectangle(img, start_point, end_point, color, thickness)



        def draw_grid(img, grid_shape=(MAP_SIZE, MAP_SIZE), color=(0, 0, 255), thickness=1):
            h, w, _ = img.shape
            rows, cols = grid_shape
            dy, dx = h / rows, w / cols
            # draw vertical lines
            for x in np.linspace(start=dx, stop=w - dx, num=cols - 1):
                x = int(round(x))
            # draw horizontal lines
            for y in np.linspace(start=dy, stop=h - dy, num=rows - 1):
                y = int(round(y))
            return img


        def draw_map(food_map, ants, grid_shape=(MAP_SIZE, MAP_SIZE)):
            img = np.full((700, 700, 3), (255, 255, 255), dtype=('uint8'))
            img.fill(255)
            draw_food(img, food_map)
            img = draw_grid(img, grid_shape)

            for ant in ants.values():
                draw_ant(img, ant)
            cv2.imshow('tmp', img)
            cv2.waitKey(1)


        def draw_ant(img, ant, grid_shape=(MAP_SIZE, MAP_SIZE)):
            h, w, _ = img.shape
            rows, cols = grid_shape
            dy, dx = h / rows, w / cols
            i, j = ant["coordinates"]
            offset = int(dx / 4)
            start_point = (int(i * dx) + offset, int(j * dy) + offset)
            end_point = (int((i + 1) * dx) - offset, int((j + 1) * dy) - offset)
            img = cv2.rectangle(img, start_point, end_point, (255, 0, 0), -1)

        def food_empty():
            global food_map
            for tmp in food_map:
                for t in tmp:
                    if t > 0:
                        return False
            return True


        while (not food_empty()):
            # For each krill, check the surrounding 3x3 grid for the highest value
            draw_map(food_map, krill)
            for i in range(len(krill.keys())):
                chance = random.randrange(1, 3)
                if krill[i]["state"] == "scouting":
                    x, y = krill[i]["coordinates"]
                    max_value = food_map[x][y]
                    max_pos = (x, y)
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
                        krill[i]["trail_spot"] = max_pos
                        grid = Grid(matrix=obstacle_map)
                        start = grid.node(5, 5)
                        max_food_x, max_food_y = krill[i]["trail_spot"]
                        end = grid.node(max_food_x, max_food_y)
                        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
                        path, runs = finder.find_path(start, end, grid)
                        krill[i]["path"] = path
                        krill[i]["path_progress"] = len(path) - 1
                        krill[i]["going_to"] = False
                        krill[i]["state"] = "trailing"
                    else:
                        x, y = krill[i]["coordinates"]
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
                        krill[i]["coordinates"] = (x, y)

                elif krill[i]["state"] == "trailing":
                    max_food_x, max_food_y = krill[i]["trail_spot"][0], krill[i]["trail_spot"][1]
                    if krill[i]["going_to"]:
                        if krill[i]["path_progress"] < len(krill[i]["path"]) - 1:
                            krill[i]["coordinates"] = krill[i]["path"][krill[i]["path_progress"]]
                            krill[i]["path_progress"] += 1
                        elif krill[i]["path_progress"] == len(krill[i]["path"]) - 1:
                            krill[i]["coordinates"] = krill[i]["path"][krill[i]["path_progress"]]
                            if food_map[max_food_x][max_food_y] > 0:
                                food_map[max_food_x][max_food_y] -= 1
                                food_store += 1
                                krill[i]["food_collected"] += 1
                                krill[i]["going_to"] = False
                            else:
                                if [krill[i]["trail_spot"][0], krill[i]["trail_spot"][1]] not in empty:
                                    pass
                                krill[i]["trail_spot"] = []
                                krill[i]["state"] = "scouting"
                    else:
                        if 0 < krill[i]["path_progress"] < len(krill[i]["path"]):
                            krill[i]["coordinates"] = krill[i]["path"][krill[i]["path_progress"]]
                            krill[i]["path_progress"] -= 1
                        elif krill[i]["path_progress"] == 0:
                            krill[i]["coordinates"] = krill[i]["path"][krill[i]["path_progress"]]
                            krill[i]["going_to"] = True
                        else:
                            print("ERROR", krill[i]["path_progress"], krill[i]["coordinates"], len(krill[i]["path"]), krill[i]["path"])
            time += 1

            if len(empty) == 100:
                break
            if dead_krill == KRILL:
                break

        # Prints results
        print("")
        print(f"{len(krill.keys())} krill collected {food_store} units of food.")
        print(
            f"The total elapsed time was {time}s, or {int(time / 60)}m {time - int(time / 60) * 60}s, or {int(time / 60 / 60)}h {int(time / 60) - int(time / 60 / 60) * 60}m {time - int(time / 60) * 60}s.")
        print(
            f"The amount of values recorded as empty is {len(empty)}, meaning that there are {len(empty) - sum(len(sub_array) for sub_array in food_map)} unchecked tiles remaining.")
        print(f"There are {dead_krill} dead krill.")

        # Initialize the minimum value to the first number in the list
        min_value = krill[0]["food_collected"]
        max_value = krill[0]["food_collected"]
        # Use a for loop to find the minimum value
        for krill in krill.values():
            # Update the minimum value if a smaller number is found
            if krill["food_collected"] < min_value:
                min_value = krill["food_collected"]
            elif krill["food_collected"] > max_value:
                max_value = krill["food_collected"]

        print(
            f"The average amount of food each krill collected was {food_store // len(krill.keys())}. The least collected was {min_value} and the most collected was {max_value}.")


        total_cache.append(food_store)
        time_cache.append(time)
        results[run] = {"krillnum": MAP_SIZE, "time": time, "total": food_store, "min": min_value, "max": max_value}
        run += 1

    for i in total_cache:
        average_total += i
    average_total // len(total_cache)

    for i in time_cache:
        average_time += i
    average_time // len(time_cache)

    # open a file for writing
    with open(f"Results\VaryingMapsize\Krill\100Krill.csv", "a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["krillnum", "time", "total", "min", "max"])
        # write the data
        for result in results.values():
            writer.writerow(result)
