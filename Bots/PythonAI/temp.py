from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
import math


class PlayerAI:
    def __init__(self):
        pass

    def do_move(self, world, enemy_units, friendly_units):
        """
        This method will get called every turn; Your glorious AI code goes here.
        
        :param World world: The latest state of the world.
        :param list[EnemyUnit] enemy_units: An array of all 4 units on the enemy team. Their order won't change.
        :param list[FriendlyUnit] friendly_units: An array of all 4 units on your team. Their order won't change.
        """

        "weights"

        "repair kit, shield, blaster, scatter, laser, rail"
        pickup_bonuses = [1000, 0, 1000, 1000, 1000, 1000]
        combat_bonus = {"dmg": 10,
                "rng": 10,
                "hp": 10}
        bonus = {"friend": 1,
                "objective": 1000,
                "health": 10,
                "enemy": 1000,
                "dist": 10}
        vectors = []
        cursor = None
        move_vector = None
        move_magnitude = None
        pickup_weight = None
        target_enemy = []
       

        "calculate moves for each unit"
        for i in range(4):
            cursor = friendly_units[i]
            for p in world.pickups:
                if (not p.pickedUp):
                    vectors.append(calculate_vector(cursor.position, p.position, pickup_bonuses[p.pickup_type.value]))
            for p in world.control_points:
                vectors.append(calculate_vector(cursor.position, p.position, bonus['objective']))
            for p in enemy_units:
                hp = cursor.health - p.health
                rng = cursor.current_weapon_type.get_range() - p.current_weapon_type.get_range()
                dmg = cursor.current_weapon_type.get_damage() - p.current_weapon_type.get_damage()
                mag = hp*combat_bonus['hp'] + rng*combat_bonus['rng'] + dmg*combat_bonus['dmg']
                vectors.append(calculate_vector(cursor.position, p.position, mag))
            for k in range(4):
                if (k != i):
                    f_bonus = friendly_units[k].health * combat_bonus['hp']
                    f_bonus += friendly_units[k].current_weapon_type.get_damage() * combat_bonus['dmg']
                    f_bonus += friendly_units[k].current_weapon_type.get_range() * combat_bonus['rng']
                    f_bonus *= bonus['friend']
                    if (float(chebyshev_distance(cursor.position, friendly_units[k].position)) * bonus['dist'] != 0):
                        f_bonus /= float(chebyshev_distance(cursor.position, friendly_units[k].position)) * bonus['dist']
                    vectors.append(calculate_vector(cursor.position, friendly_units[k].position ,f_bonus))
            move_vector = agg_vectors(vectors)
            move_magnitude = calculate_magnitude(move_vector[0], move_vector[1])
            n_x = move_vector[0]
            n_y = move_vector[1]
            if (move_magnitude != 0):
                n_x = move_vector[0]/float(move_magnitude)
                n_y = move_vector[1]/float(move_magnitude)
            vectors = []
            if (cursor.check_pickup_result() == PickupResult.PICK_UP_VALID):
                if (world.get_pickup_at_position(cursor.position).pickup_type == PickupType.REPAIR_KIT):
                    pickup_weight = (100/float(cursor.health))*bonus['health']
                else:
                    pickup_weight = pickup_bonuses[world.get_pickup_at_position(cursor.position).pickup_type.value]
            else:
                pickup_weight = 0
            for n in range(4):
                p = enemy_units[n]
                if (cursor.check_shot_against_enemy(enemy_units[n]) == ShotResult.CAN_HIT_ENEMY):
                    t_weight = (cursor.health - p.health) * combat_bonus['hp']
                    t_weight += (cursor.current_weapon_type.get_range() - p.current_weapon_type.get_range()) * combat_bonus['rng']
                    t_weight += (cursor.current_weapon_type.get_damage() - p.current_weapon_type.get_damage()) * combat_bonus['dmg']
                    for r in range(4):
                        if (r != i):
                            t_weight += bonus['friend']*(chebyshev_distance(cursor.position, friendly_units[r].position))
                    t_weight += bonus['enemy']
                    target_enemy.append(t_weight)
                else:
                    target_enemy.append(0)

            target_enemy.append(move_magnitude) 
            target_enemy.append(pickup_weight)

            best_move = target_enemy[0]
            best_enemy = max(target_enemy[0:4])
            best_enemy_index = 0
            best_move_index = 0

            for n in range(1, 6):
                if (target_enemy[n] > best_move):
                    best_move = target_enemy[n]
                    best_move_index = n
                    if ((best_enemy == target_enemy[n]) and n < 4):
                        best_enemy_index = n
                    
            if((target_enemy[0] != 0) or (target_enemy[1] != 0) or (target_enemy[2] != 0) or (target_enemy[3] != 0)):
                print(target_enemy)
            if (best_move_index == 5):
                "Best option is pickup an item. Do so."
                cursor.pickup_item_at_position()
            elif (best_move_index == 4):
                "Best option is to move, calculate the move"
                #print("elected to move")
                #print(int(cursor.position[0] + move_vector[0]), int(cursor.position[1] + move_vector[1]))
                #print(cursor.move_to_destination((int(cursor.position[0] + (move_vector[0]/move_magnitude), int(cursor.position[1] + (move_vector[1]/move_magnitude))))))
                temp = (cursor.position[0] + math.ceil(n_x),cursor.position[1] + math.ceil(n_y))


                if (cursor.check_move_to_destination((cursor.position[0] + math.ceil(n_x),cursor.position[1] + math.ceil(n_y))) == MoveResult.MOVE_VALID):
                    cursor.move_to_destination((cursor.position[0] + math.ceil(n_x),cursor.position[1] + math.ceil(n_y)))
                    print('spacing move')
                else:
                    cursor.move_to_destination(enemy_units[i].position)
                    print('approach')
            else:       
                "Best option is to shoot."
                cursor.shoot_at(enemy_units[best_enemy_index])
            target_enemy = []
            cursor = None




   
def calculate_vector(home, away, weight):
    n_away = (home[0] - away[0], home[1] - away[1])
    n_home = (0,0)
    magnitude = calculate_magnitude(n_away[0], n_away[1])
    if (magnitude == 0):
        magnitude = 1
    return ((n_away[0]*weight/float(magnitude)), n_away[1]*weight/float(magnitude))

def agg_vectors(vectors):
    N = len(vectors)
    x = 0
    y = 0
    for i in range(N):
        x += vectors[i][0]
        y += vectors[i][0]
    x /= float(N)
    y /= float(N)
    return (x,y)

def calculate_magnitude(x,y):
    return math.sqrt((x)**2 + (y)**2)

def compute_direction(vector):
    x=0
    y=0
    if (vector[0] != 0):
        if (vector[0] > 0):
            x = 1
        else:
            x = -1
    if (vector[1] != 0):
        if (vector[1] > 0):
            y = 1
        else:
            y = -1
    

        
    
















