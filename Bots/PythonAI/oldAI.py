from PythonClientAPI.libs.Game import PointUtils
from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.Entities import *
from PythonClientAPI.libs.Game.World import *
import math
import random


class PlayerAI:
    def __init__(self):
        "repair kit, shield, blaster, scatter, laser, rail"
        self.pickup_bonuses = [random.randint(1,100), random.randint(1,100), random.randint(1,100), random.randint(1,100), random.randint(1,100), random.randint(1,100) ]
        self.combat_bonus = {"dmg": random.randint(1,100),
                "rng": random.randint(1,100),
                "hp": random.randint(1,100)}
        self.bonus = {"friend": random.randint(1,100),
                "objective":random.randint(1,100) ,
                "health": random.randint(1,100),
                "enemy": random.randint(1,100),
                "dist": random.randint(1,100)}

        self.bonus = {'friend': 68 , 'objective': 9, 'health': 99, 'enemy': 91 , 'dist': 80 }
        self.combat_bonus = {'dmg': 71, 'rng': 17, 'hp': 34}
        self.pickup_bonuses = [18, 0, 3, 51, 47, 98]
        print('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')
        self.data = [self.bonus['friend'], self.bonus['objective'], self.bonus['health'], self.bonus['enemy'], self.bonus['dist'], self.combat_bonus['dmg'],
                self.combat_bonus['rng'], self.combat_bonus['hp']] + self.pickup_bonuses
        self.data_string = ""
        for item in self.data:
            self.data_string += str(item) + "," 
        print(self.data_string)


    def do_move(self, world, enemy_units, friendly_units):
        """
        This method will get called every turn; Your glorious AI code goes here.
        
        :param World world: The latest state of the world.
        :param list[EnemyUnit] enemy_units: An array of all 4 units on the enemy team. Their order won't change.
        :param list[FriendlyUnit] friendly_units: An array of all 4 units on your team. Their order won't change.
        """
        bonus = self.bonus
        combat_bonus = self.combat_bonus
        pickup_bonuses = self.pickup_bonuses 


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
                if (p.controlling_team != cursor.team):
                    vectors.append(calculate_vector(cursor.position, p.position, bonus['objective']))
                if (p.is_mainframe):
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
                    
            #if((target_enemy[0] != 0) or (target_enemy[1] != 0) or (target_enemy[2] != 0) or (target_enemy[3] != 0)):
            #print(target_enemy)
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
                elif (cursor.check_move_to_destination(enemy_units[best_enemy_index].position) == MoveResult.MOVE_VALID):
                    cursor.move_to_destination(enemy_units[best_enemy_index].position)
                elif((world.control_points != []) and (cursor.check_move_to_destination(world.get_nearest_control_point(cursor.position).position))):
                    cursor.move_to_destination(world.get_nearest_control_point(cursor.position).position)
                else:
                    directions_list = [(1,0), (0,1), (1,1),(-1,-1),(-1,0),(0,-1),(1,-1),(-1,1)]
                    cursor.move(Direction(directions_list[random.randint(1,8) - 1]))
            else:       
                "Best option is to shoot."
                cursor.shoot_at(enemy_units[best_enemy_index])
            target_enemy = []
            cursor = None
        #print(get_nearest_free_control_point(friendly_units[0], world.control_points))
        #friendly_units[0].move_to_destination(get_nearest_free_control_point(friendly_units[0], world.control_points))
        for i in range(4):
            for j in range(4):
                if(friendly_units[i].check_shot_against_enemy(enemy_units[j]) == ShotResult.CAN_HIT_ENEMY):
                    if (friendly_units[(i+1)%4].check_shot_against_enemy(enemy_units[j]) == ShotResult.CAN_HIT_ENEMY):
                        friendly_units[(i+1)%4].shoot_at(enemy_units[j])
                        friendly_units[i].shoot_at(enemy_units[j])
                        print('check')
                    if (friendly_units[(i+2)%4].check_shot_against_enemy(enemy_units[j]) == ShotResult.CAN_HIT_ENEMY):
                        friendly_units[(i+2)%4].shoot_at(enemy_units[j])
                        friendly_units[i].shoot_at(enemy_units[j])
                        print('these')
                    if (friendly_units[(i+3)%4].check_shot_against_enemy(enemy_units[j]) == ShotResult.CAN_HIT_ENEMY):
                        friendly_units[(i+3)%4].shoot_at(enemy_units[j])
                        friendly_units[i].shoot_at(enemy_units[j])
                        print('quads')

                    #for k in range(4):
                    #    if((i != k) and (friendly_units[k].check_shot_against_enemy(enemy_units[j]) == ShotResult.CAN_HIT_ENEMY)):
                    #        print("doubleshot")
                    #        friendly_units[i].shoot_at(enemy_units[j])
                    #        friendly_units[k].shoot_at(enemy_units[j])



   
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

def get_nearest_free_control_point(cursor, world_cp_list):
    cp_list = []
    for i in world_cp_list:
        print(i.controlling_team)
        print(cursor.team)
        if (i.controlling_team != cursor.team):
            cp_list.append([i.position, chebyshev_distance(i.position, cursor.position)])
    min_dist = cp_list[0][1]
    opt_cp = cp_list[0][0]
    for i in range(len(cp_list) - 1):
        if (min_dist > cp_list[i][1]):
            min_dist = cp_list[i][1]
            opt_cp = cp_list[i][0]
    return opt_cp


