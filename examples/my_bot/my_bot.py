import sc2
import random
import numpy as np
import math
from sc2 import game_state
from sc2 import run_game, maps, Race, Difficulty, Result
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.player import Bot, Computer, Human
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units
from sc2.helpers.control_group import ControlGroup
from typing import List
import time
import cv2
import os
import tensorboard as tf
import keras 
from keras import models

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ["SC2PATH"] = 'C:\Program Files (x86)\StarCraft II'
class MyBot(sc2.BotAI):

   """   
   It will go through a proper build order
     X 1) Create 2 miners
     X 2) Create a supply depot
     X 3) As minerals come, it will then create more miners until 18
     X 4) During this time, around miner 16, it will create a barracks
     X 5) From the barracks, it will cap the supply with marines
     X 6) After the supply cap, several more supply depots will be created.
     X 7) It will send these marines for a preemptive strike
     X 8) Create a factory <-------------------- This is still not done
                  though.  I need to figure out a better way to get it working in sync.  I
                  can just build the factory I think.
      9) Create x number of marauder and y number of hellion
      10) When 200 supply cap reached, it will then attack in full force
      11) Repeat strategy
   """
   # Initialize
   def __init__(self, use_model=False):
      self.train_data = []
      self.use_model = use_model
      self.total_tech = 0

      self.do_something_after = 0
      self.supply_cap = 200
      self.scouts_and_spots = {}
      self.scv_scout = []
      self.enemy_expansions = []
      self.build_another_barrack = False

      #self.practice_group = ControlGroup()
      self.can_harass = True
      self.hellion_harass_ids = []
      self.harass_force_ids = []
      self.main_force_ids = []
      self.defence_unit_ids = []
      self.units_to_be_removed = []

      self.choices = { 0: self.do_nothing, 
                       1: self.attack_closest_to_cc,
                       2: self.attack_enemy_structure,
                       3: self.attack_enemy_start,
                       4: self.harass,
                       5: self.build_marine,
                       6: self.build_hellion,
                       7: self.create_barracks,
                       8: self.create_factory,
                       9: self.build_refinery,
                       10: self.build_supply_depots,}

      if self.use_model:
         print('USING MODEL')
         self.model = keras.models.load_model("BasicCNN-1000-epochs-0.001-LR-STAGE2")
      return

   def on_end(self, game_result):
      """
      Trying to figure out the benefit of this
      """
      print('--on_end called')
      print(game_result)

       #This is for training
      if game_result == Result.Victory:
         np.save("train_data/easy/{}.npy".format(str(int(time.time())))),
         np.array(self.train_data)
         
   # =======================================================================================
   # This is for saving model results
      #with open('gameout-random-vs-easy1.txt', 'a') as f:
      #   if self.use_model:
      #      f.writelines('Model {}\n'.format(game_result))
      #   else:
      #      f.write('Random {}\n'.format(game_result))
      return

   def is_first_barracks_built(self):
      if self.units(UnitTypeId.BARRACKS).ready:
         if self.units(UnitTypeId.BARRACKS).amount == 1:
            return True
         else:
            return False
      return

   async def build_supply_depots(self):
      """
      This part will create the supply depots
      """
      cc = self.units(UnitTypeId.COMMANDCENTER)
      if not cc.exists:
         target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
         for unit in self.workers | self.units(UnitTypeId.MARINE):
            await self.do(unit.attack(target))
         return
      else:
         cc = cc.first
      if self.iteration % 50 == 0 and self.units(UnitTypeId.SUPPLYDEPOTLOWERED).ready.amount < 30:
         if self.can_afford(UnitTypeId.SUPPLYDEPOT) and not self.units(UnitTypeId.SUPPLYDEPOT).exists:
            await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))
         elif self.units(UnitTypeId.SUPPLYDEPOT).exists:
            if self.units(UnitTypeId.BARRACKS).ready.exists and self.supply_left < 8 and self.can_afford(UnitTypeId.SUPPLYDEPOT):
               if not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                  await self.build(UnitTypeId.SUPPLYDEPOT, near=cc)
      return

   async def build_workers(self, cc):
      """
      Get up to the 18 miners.  This seems to not count the SCV being used to
      build something.
      """
      if not self.already_pending(UnitTypeId.SCV):
         if self.units(UnitTypeId.SCV).amount < 48:
            if self.can_afford(UnitTypeId.SCV) and self.units(UnitTypeId.SUPPLYDEPOTLOWERED).amount >= 1:
               if not self.already_pending(UnitTypeId.SCV) and self.units(UnitTypeId.COMMANDCENTER).ready.noqueue:
                  await self.do(cc.train(UnitTypeId.SCV))
      return

   async def create_barracks(self):
      """
      Create barracks
      """
      cc = self.units(UnitTypeId.COMMANDCENTER)
      if not cc.exists:
         target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
         for unit in self.workers | self.units(UnitTypeId.MARINE):
            await self.do(unit.attack(target))
         return
      else:
         cc = cc.first
      if self.units(UnitTypeId.SUPPLYDEPOT).exists:
         if self.can_afford(UnitTypeId.BARRACKS) and self.units(UnitTypeId.BARRACKS).amount < 3:
            await self.build(UnitTypeId.BARRACKS, near=cc.position.towards(self.game_info.map_center, 10))
         elif self.units(UnitTypeId.BARRACKS).ready.amount == 3:
            if self.units(UnitTypeId.BARRACKS).ready.amount < 7:
               if self.build_another_barrack:
                  self.build_another_barrack = False
                  await self.build(UnitTypeId.BARRACKS, near=cc.position.towards(self.game_info.map_center, 10))
               else:
                  return

      #elif self.fill_harass_force == False:
      #   if self.can_afford(UnitTypeId.BARRACKS) and
      #   self.units(UnitTypeId.BARRACKS).amount < 5:
      #      await self.build(UnitTypeId.BARRACKS, near =
      #      cc.position.towards(self.game_info.map_center, 15))
      return

   async def build_refinery(self):
      """
      Just build 2 refineries for now. I can worry about building more later
      """
      for cc in self.units(UnitTypeId.COMMANDCENTER).ready:
         if self.units(UnitTypeId.REFINERY).amount < 2:
            refineries = self.state.vespene_geyser.closer_than(15.0, cc)
            #if self.units(UnitTypeId.SUPPLYDEPOT).amount >= 2:
            if self.units(UnitTypeId.SUPPLYDEPOTLOWERED).amount >= 2:
               for refinery in refineries:
                  if not self.can_afford(UnitTypeId.REFINERY):
                     break
                  worker = self.select_build_worker(refinery.position)
                  if worker is None:
                     break
                  if not self.units(UnitTypeId.REFINERY).closer_than(1.0, refinery).exists:
                     await self.do(worker.build(UnitTypeId.REFINERY, refinery))
      return

   async def build_marine(self):
      """
      Create marines for now. I Need to try and create the other units here too.
      """
      for rax in self.units(UnitTypeId.BARRACKS).ready.noqueue:
         while self.supply_left > 4:
            if not self.can_afford(UnitTypeId.MARINE):
               break
            else:
               await self.do(rax.train(UnitTypeId.MARINE))
      return

   async def lower_supply_depots(self):
      """
      This will raise the supply depots when necessary
      """
      if self.units(UnitTypeId.SUPPLYDEPOT).exists: 
         for depot in self.units(UnitTypeId.SUPPLYDEPOT).ready:
            await self.do(depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER))
      return

   async def raise_supply_depot(self):
      """
      This will lower the supply depots when necessary
      """
      for depo in self.units(UnitTypeId.SUPPLYDEPOT).ready:
         for unit in self.known_enemy_units.not_structure:
               if unit.position.to2.distance_to(depo.position.to2) < 10:
                  await self.do(depo(MORPH_SUPPLYDEPOT_RAISE))
                  break
      return
   
   async def expand(self):
      try:
         if self.units(UnitTypeId.COMMANDCENTER).amount < 2 and self.can_afford(UnitTypeId.COMMANDCENTER) and not self.already_pending(UnitTypeId.COMMANDCENTER):
            if self.units(UnitTypeId.BARRACKS).amount >= 2:
               await self.expand_now()
         elif self.units(UnitTypeId.COMMANDCENTER).amount == 2 and self.can_afford(UnitTypeId.COMMANDCENTER) and not self.already_pending(UnitTypeId.COMMANDCENTER):
            if self.units(UnitTypeId.BARRACKS).amount > 4:
               await self.expand_now()
         elif self.units(UnitTypeId.COMMANDCENTER).amount >= 3:
            return
         else:
            return
      except Exception as e:
         print(str(e))
      return

   async def upgrade_to_orbital(self):
      """
      This function is for the purpose of creating the orbital command post
      """
      if self.can_afford(UnitTypeId.ORBITALCOMMAND) and self.units(UnitTypeId.MARINE).amount >= 10:
         if self.units(UnitTypeId.ORBITALCOMMAND).idle:
            await self.do(cc.first(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))
      return

   def find_target(self, state):
      """
      This is not part of the asynchronous tasks
      """
      if len(self.known_enemy_units) > 0:
         return random.choice(self.known_enemy_units)
      elif len(self.known_enemy_units) > 0:
         return random.choice(self.known_enemy_structures)
      else:
         return self.enemy_start_locations[0]
      return

   async def intel(self):
      game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)

      for unit in self.units().ready:
         pos = unit.position
         cv2.circle(game_data, (int(pos[0]), int(pos[1])), int(unit.radius * 8), (255, 255, 255), math.ceil(int(unit.radius * 0.5)))


      main_base_names = ['commandcenter', 'hatchery', 'nexus']
      for enemy_building in self.known_enemy_structures:
         pos = enemy_building.position
         if enemy_building.name.lower() not in main_base_names:
            cv2.circle(game_data, (int(pos[0]), int(pos[1])), int(enemy_building.radius * 8), (255, 255, 255), math.ceil(int(enemy_building.radius * 0.5)))
      for enemy_building in self.known_enemy_structures:
         pos = enemy_building.position
         if enemy_building.name.lower() in main_base_names:
            cv2.circle(game_data, (int(pos[0]), int(pos[1])), int(enemy_building.radius * 8), (255, 255, 255), math.ceil(int(enemy_building.radius * 0.5)))

      for enemy_unit in self.known_enemy_units:
         if not enemy_unit.is_structure:
            worker_names = ['probe',
                            'scv',
                            'drone']
            pos = enemy_unit.position
            if enemy_unit.name.lower() in worker_names:
               cv2.circle(game_data, (int(pos[0]), int(pos[1])), int(enemy_unit.radius * 8), (255, 255, 255), math.ceil(int(enemy_unit.radius * 0.5)))
            else:
               cv2.circle(game_data, (int(pos[0]), int(pos[1])), int(enemy_unit.radius * 8), (255, 255, 255), math.ceil(int(enemy_unit.radius * 0.5)))

         line_max = 50
         mineral_ratio = self.minerals / 1500
         if mineral_ratio > 1.0:
            mineral_ratio = 1.0

         vespene_ratio = self.vespene / 1500
         if vespene_ratio > 1.0:
            vespene_ratio = 1.0

         population_ratio = self.supply_left / self.supply_cap
         if population_ratio > 1.0:
            population_ratio = 1.0

         plausible_supply = self.supply_cap / 200.0

         if self.supply_cap - self.supply_left != 0:
            worker_weight = len(self.units(PROBE)) / (self.supply_cap - self.supply_left)
            if worker_weight > 1.0:
               worker_weight = 1.0

         cv2.line(game_data, (0, 19), (int(line_max * worker_weight), 19), (250, 250, 200), 3)  # worker/supply ratio
         cv2.line(game_data, (0, 15), (int(line_max * plausible_supply), 15), (220, 200, 200), 3)  # plausible supply (supply/200.0)
         cv2.line(game_data, (0, 11), (int(line_max * population_ratio), 11), (150, 150, 150), 3)  # population ratio (supply_left/supply)
         cv2.line(game_data, (0, 7), (int(line_max * vespene_ratio), 7), (210, 200, 0), 3)  # gas / 1500
         cv2.line(game_data, (0, 3), (int(line_max * mineral_ratio), 3), (0, 255, 25), 3)  # minerals minerals/1500

      # flip horizontally to make our final fix in visual
      # representation:
      self.flipped = cv2.flip(game_data, 0)
      resized = cv2.resize(self.flipped, dsize=None, fx=2, fy=2)

      if self.use_model:
         cv2.imshow('Model Intel', resized)
         cv2.waitKey(1)
      else:
         cv2.imshow('Random', resized)
         cv2.waitKey(1)
      return

   async def scout(self):

      self.expand_dis_dir = {}

      for el in self.expansion_locations:
         distance_to_enemy_start = el.distance_to(self.enemy_start_locations[0])
         self.expand_dis_dir[distance_to_enemy_start] = el
         
      self.ordered_exp_distances = sorted(k for k in self.expand_dis_dir)

      # Periodically go and scout.  This needs to be improve upon.  Except I
      # can't get self.state.game_loop equation to work for me.....
      if len(self.scv_scout) > 0:
         for scv in self.units(UnitTypeId.SCV):
            if not len(self.scv_scout) == 1:
               self.scv_scout.append(scv.tag)

      if self.iteration % 100 == 0:
         isDone = False
      
      # For the moment, I am only checking for the first initial base
      self.enemy_expansions.append(self.enemy_start_locations[0])
      
      # I will only send the scout when the first barracks is built.
      if self.units(UnitTypeId.BARRACKS).ready.amount >= 1:
         # If there is already an SCV scout, I will not send another to die
         if not len(self.scv_scout) == 1: 
            isDone = True
            scout = self.units(UnitTypeId.SCV)[0]
            if isDone:
               self.scv_scout.append(scout)
               isDone = False
               await self.do(scout.move(self.enemy_expansions[0]))

      for dist in self.ordered_exp_distances:
         try:
            location = next(value for key, value in self.expand_dis_dir.items() if key == dist)
            active_locations = [k for k in self.scouts_and_spots]

            if location not in active_locations:
               if unit_type == PROBE:
                     for unit in self.units(PROBE):
                        if unit.tag in self.scouts_and_spots:
                           continue

               await self.do(obs.move(location))
               self.scouts_and_spots[obs.tag] = location
               break
         except Exception as e:
            pass

      return

   def random_location_variance(self, location):
      x = location[0]
      y = location[1]

      x += random.randrange(-5, 5)
      y += random.randrange(-5, 5)

      if x < 0:
         x = 0
      if y < 0:
         y = 0
      if x > self.game_info.map_size[0]:
         x = self.game_info.map_size[0]
      if y > self.game_info.map_size[1]:
         y = self.game_info.map_size[1]

      go_to = position.Point2(position.Pointlike((x,y)))
      return go_to

   async def defend(self):
      if len(self.known_enemy_units) > 0 and len(self.defence_unit_ids) >= 1:
         target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
         for marine in self.units(UnitTypeId.MARINE):
            if marine.tag in self.defence_unit_ids:
               await self.do(marine.attack(target))
      #elif len(self.known_enemy_units) > 0:
      #   target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
      #   count = 0
      #   for marine in self.units(UnitTypeId.MARINE):
      #      if count <= 6:
      #         count += 1
      #         print('count: {}'.format(count))
      #         await self.do(marine.attack(target))

      return

   async def split_army(self):
      if self.units(UnitTypeId.MARINE).exists:
         for marine in self.units(UnitTypeId.MARINE):
            if not marine.tag in self.harass_force_ids:
               if not marine.tag in self.defence_unit_ids:
                  if not marine.tag in self.main_force_ids:
                     if len(self.harass_force_ids) <= 10:
                        self.harass_force_ids.append(marine.tag)
                     elif len(self.main_force_ids) <= 30:
                        self.main_force_ids.append(marine.tag)
                     else:
                        self.defence_unit_ids.append(marine.tag)
      if self.units(UnitTypeId.HELLION).exists:
         for hellion in self.units(UnitTypeId.HELLION):
            if not hellion.tag in self.main_force_ids:
               if not hellion.tag in self.hellion_harass_ids:
                  if len(self.hellion_harass_ids) < 5:
                     self.hellion_harass_ids.append(hellion.tag)
                  else:
                     self.main_force_ids.append(hellion.tag)

      if self.units(UnitTypeId.MARAUDER).exists:
         for m in self.units(UnitTypeId.MARAUDER):
            if not m.tag in self.main_force_ids:
               self.main_force_ids.append(m.tag)
      return

   async def clean_up(self):
      temp_array = []
      temp_harass_array = self.harass_force_ids
      for marine in self.units(UnitTypeId.MARINE):
         temp_array.append(marine.tag)
      #temp_array = [m.tag in m for ]

      if len(self.harass_force_ids) > 0:
         for unit_tag in temp_harass_array:
            if unit_tag not in temp_array:
               self.harass_force_ids.remove(unit_tag)
      del temp_array
      del temp_harass_array

      temp_array = []
      temp_main_array = self.main_force_ids
      for marine in self.units(UnitTypeId.MARINE):
         temp_array.append(marine.tag)

      if len(self.main_force_ids) > 0:
         for unit_tag in temp_main_array:
            if unit_tag not in temp_array:
               self.main_force_ids.remove(unit_tag)
      del temp_array

      temp_array = []
      temp_harass_array = self.hellion_harass_ids
      for hellion in self.units(UnitTypeId.HELLION):
         temp_array.append(hellion.tag)

      if len(self.hellion_harass_ids) > 0:
         for unit_tag in temp_harass_array:
            if unit_tag not in temp_harass_array:
               self.hellion_harass_ids.remove(unit_tag)
     
      del temp_array
      temp_array = []
      temp_main_array = self.main_force_ids
      for m in self.units(UnitTypeId.MARAUDER):
         temp_array.append(m.tag)

      if len(self.main_force_ids) > 0:
         for unit_tag in temp_main_array:
            if unit_tag not in temp_array:
               self.main_force_ids.remove(unit_tag)
      del temp_array

      del temp_harass_array
      del temp_main_array
      return

   async def perform_task(self):
      if self.current_time > self.do_something_after:
         if self.use_model:
               marine_weight = 2.2
               hellion_weight = 1.1
               factory_weight = 1.1
               barracks_weight = 1.5
               supply_depot_weight = 2
               refinery_weight = 1.3
               supply_depot_weight = 2.5

               prediction = self.model.predict([self.flipped.reshape([-1, 184, 208, 3])])
               weights = [1, 1, 1, 1, 1, marine_weight, hellion_weight, barracks_weight, factory_weight, refinery_weight, supply_depot_weight]
               weighted_prediction = prediction[0]*weights
               choice = np.argmax(weighted_prediction)
               print('Choice:',self.choices[choice])
         else:
               marine_weight = 13
               hellion_weight = 14
               barracks_weight = 8
               supply_depot_weight = 10
               refinery_weight = 5
               factory_weight = 9
               supply_depot_weight = 20

               choice_weights = 1*[0] + 1*[1] + 1*[2] + 1*[3] + 1*[4] + marine_weight*[5] + hellion_weight*[6] + barracks_weight*[7]+factory_weight*[8]+refinery_weight*[9]+supply_depot_weight*[10]
               choice = random.choice(choice_weights)

         try:
            await self.choices[choice]()
         except Exception as e:
            print(str(e))
         
         y = np.zeros(11)
         y[choice] = 1
         self.train_data.append([y, self.flipped])   
      return

   async def do_nothing(self):
      wait = random.randrange(10, 90) / 100
      self.do_something_after = self.current_time + wait
      return

   async def attack_closest_to_cc(self):
      if len(self.known_enemy_units) > 0 and len(self.main_force_ids) >= 30:
         target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
         for marine in self.units(UnitTypeId.MARINE):
            if marine.tag in self.main_force_ids:
               await self.do(marine.attack(target))
         for unit in self.units(UnitTypeId.HELLION):
            if unit.tag in self.main_force_ids:
               await self.do(unit.attack(target))
      return

   async def attack_enemy_structure(self):
      if len(self.known_enemy_structures) > 0 and len(self.main_force_ids) >= 30:
         target = random.choice(self.known_enemy_structures)
         for marine in self.units(UnitTypeId.MARINE):
            if marine.tag in self.main_force_ids:
               await self.do(marine.attack(target))
         for unit in self.units(UnitTypeId.HELLION):
            if unit.tag in self.main_force_ids:
               await self.do(unit.attack(target))
      return

   async def attack_enemy_start(self):
      if len(self.known_enemy_units) > 0 and len(self.main_force_ids) >= 30:
         target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
         for marine in self.units(UnitTypeId.MARINE):
            for unit_tag in self.main_force_ids:
               if marine.tag == unit_tag:
                  await self.do(marine.attack(target))
         for unit in self.units(UnitTypeId.HELLION):
            if unit.tag in self.main_force_ids:
               await self.do(unit.attack(target))
      return

   async def harass(self):
      if len(self.harass_force_ids) >= 10 and self.can_harass == True:
         self.can_harass = False
         target = self.enemy_start_locations[0]
         
         for marine in self.units(UnitTypeId.MARINE):
            if marine.tag in self.harass_force_ids:
               await self.do(marine.attack(target))
          # Hellions attack
         for hel in self.units(UnitTypeId.HELLION):
            if hel.tag in self.hellion_harass_ids:
               await self.do(hel.attack(target))
      return

   async def position_defensive_units(self):
      for marine in self.units(UnitTypeId.MARINE):
         if marine.tag in self.defence_unit_ids:
            await self.do(marine.move(self.start_location[1]).position)
      return

   async def create_factory(self):
      cc = self.units(UnitTypeId.COMMANDCENTER)
      if not cc.exists:
         target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
         for unit in self.workers | self.units(UnitTypeId.MARINE):
            await self.do(unit.attack(target))
         return
      else:
         cc = cc.first
      if self.units(UnitTypeId.BARRACKS).ready.amount >= 2:
         if self.units(UnitTypeId.FACTORY).amount < 2:
            await self.build(UnitTypeId.FACTORY, near=cc.position.towards(self.game_info.map_center, 10))
      return

   async def build_hellion(self):
      for f in self.units(UnitTypeId.FACTORY).ready.noqueue:
         while self.supply_left > 4:
            if not self.can_afford(UnitTypeId.HELLION):
               break
            else:
               await self.do(f.train(UnitTypeId.HELLION))
      return

   async def morph_barracks(self):
      for rax in self.units(UnitTypeId.BARRACKS).idle:
         if self.total_tech < 2 and not self.already_pending(UnitTypeId.BARRACKSTECHLAB):
            self.total_tech += 1
            await self.do(rax.build(UnitTypeId.BARRACKSTECHLAB))
      return

   async def create_marauder(self):
      print('')
      print('1')
      print('')
      if self.can_afford(UnitTypeId.MARAUDER):
         print('')
         print('3')
         print('')
         for rax in self.units(UnitTypeId.BARRACKS):
            print('')
            print('4')
            print('')
            if rax.has_add_on:
               print('')
               print('SUCCESS------------------------------------------------------------------')
               await self.do(rax.train(UnitTypeId.MARAUDER))
      return

   async def on_step(self, iteration):
      cc = self.units(UnitTypeId.COMMANDCENTER)
      if not cc.exists:
         target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
         for unit in self.workers | self.units(UnitTypeId.MARINE):
            await self.do(unit.attack(target))
         return
      else:
         cc = cc.first
      self.current_time = self.time
      self.iteration = iteration

      await self.split_army()
      await self.clean_up()
      if self.iteration % 60 == 0:
         await self.distribute_workers()
      await self.scout()
      await self.expand()
      await self.perform_task()
      await self.morph_barracks()

      await self.build_supply_depots()
      await self.build_workers(cc)
      await self.lower_supply_depots()
      await self.intel()

      if self.iteration % 500 == 0:
         await self.defend()
      if self.iteration % 50 == 0:
         self.can_harass = True
         await self.create_marauder()

      return
          
def main():
   count = 0
   while count != 10:
      run_game(sc2.maps.get("Sequencer LE"), 
               [Bot(Race.Terran, MyBot(use_model=False)),
                Computer(Race.Protoss, Difficulty.Easy)],
               realtime = False)
      count += 1
      print('---The count is: {}'.format(str(count)))

if __name__ == '__main__':
    main()