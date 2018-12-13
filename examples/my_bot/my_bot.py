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
HEADLESS = False
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
      9) Create x number of marauder and y number of helion
      10) When 200 supply cap reached, it will then attack in full force
      11) Repeat strategy
   """
   # Initialize
   def __init__(self, use_model=False):
      self.train_data = []
      self.use_model = use_model

      self.do_something_after = 0
      self.supply_cap = 200
      self.scouts_and_spots = {}
      self.scv_scout = []
      self.enemy_expansions = []
      self.build_another_barrack = False

      #self.practice_group = ControlGroup()
      self.can_harass = True
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
                       6: self.build_helion,}

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
         np.save("train_data/easy/{}.npy".format(str(int(time.time()))),
         np.array(self.train_data))
         
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

   async def build_supply_depots(self, cc):
      """
      This part will create the supply depots
      """
      if self.iteration % 50 == 0 and self.units(UnitTypeId.SUPPLYDEPOT).ready.amount < 20:
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

   async def create_barracks(self, cc):
      """
      Create barracks
      """
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
            if self.units(UnitTypeId.BARRACKS).ready.amount > 4:
               await self.expand_now()
      except Exception as e:
         print(str(e))
      #if self.units(UnitTypeId.COMMANDCENTER).amount < (self.iteration /
      #self.ITERATIONS_PER_MINUTE) and
      #self.can_afford(UnitTypeId.COMMANDCENTER):
      #   await self.expand_now()
      return

   async def upgrade_to_orbital(self):
      """
      This function is for the purpose of creating the orbital command post
      """
      if self.can_afford(UnitTypeId.ORBITALCOMMAND) and self.units(UnitTypeId.MARINE).amount >= 10:
      #   for c in self.units(UnitTypeId.COMMANDCENTER).idle:
      #      c(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)
      #return
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

      if not HEADLESS: 
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
      if len(self.known_enemy_units) > 0 and len(self.defence_unit_ids) >= 5:
         target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
         for marine in self.units(UnitTypeId.MARINE):
            await self.do(marine.attack(target))
      return

   async def split_army(self):
      if self.units(UnitTypeId.MARINE).exists:
         for marine in self.units(UnitTypeId.MARINE):
            if not marine.tag in self.harass_force_ids:
               if not marine.tag in self.defence_unit_ids:
                  if not marine.tag in self.main_force_ids:
                     if len(self.harass_force_ids) <= 10:
                        self.harass_force_ids.append(marine.tag)
                        print('harass length: {}'.format(len(self.harass_force_ids)))
                     elif len(self.main_force_ids) <= 30:
                        self.main_force_ids.append(marine.tag)
                        print('main length: {}'.format(len(self.main_force_ids)))
                     else:
                        self.defence_unit_ids.append(marine.tag)
                        print('defensive length: {}'.format(len(self.defence_unit_ids)))


      #if self.units(UnitTypeId.MARINE).exists:
      #   for marine in self.units(UnitTypeId.MARINE):
      #      if len(self.harass_force_ids) < 10:
      #         if not marine.tag in self.harass_force_ids:
      #            if not marine.tag in self.main_force_ids:
      #               self.harass_force_ids.append(marine.tag)
      #      else:
      #         if not marine.tag in self.harass_force_ids:
      #            if not marine.tag in self.main_force_ids:
      #               self.main_force_ids.append(marine.tag)
      #if len(self.harass_force_ids) == 10:
      #   self.fill_harass_force = False
      return

   async def clean_up(self):
      temp_array = []
      temp_harass_array = self.harass_force_ids
      for marine in self.units(UnitTypeId.MARINE):
         temp_array.append(marine.tag)

      if len(self.harass_force_ids) > 0:
         for unit_tag in temp_harass_array:
            if unit_tag not in temp_array:
               self.harass_force_ids.remove(unit_tag)
      del temp_array

      temp_array = []
      temp_main_array = self.main_force_ids
      for marine in self.units(UnitTypeId.MARINE):
         temp_array.append(marine.tag)

      if len(self.main_force_ids) > 0:
         for unit_tag in temp_main_array:
            if unit_tag not in temp_array:
               self.main_force_ids.remove(unit_tag)

      del temp_array
      del temp_harass_array
      del temp_main_array
      return

   async def perform_task(self):
      if self.iteration > self.do_something_after:
         if self.use_model:
            prediction = self.model.predict([self.flipped.reshape([-1, 184, 208, 3])])
            choice = np.argmax(prediction[0])
            print('model choice: {}'.format(choice))
         else:
            choice = random.randrange(0, 7)

         try:
            #print('choice: {}'.format(choice))
            await self.choices[choice]()
         except Exception as e:
            print(str(e))
         
         y = np.zeros(7)
         y[choice] = 1
         self.train_data.append([y, self.flipped])    
      return

   async def do_nothing(self):
      #wait = random.randrange(7, 100)/100
      #self.do_something_after = self.time + wait
      wait = random.randrange(10, 60)
      self.do_something_after = self.iteration + wait

   async def attack_closest_to_cc(self):
      if len(self.known_enemy_units) > 0 and len(self.main_force_ids) >= 30:
         target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
         for marine in self.units(UnitTypeId.MARINE):
            if marine.tag in self.main_force_ids:
               await self.do(marine.attack(target))
      return

   async def attack_enemy_structure(self):
      if len(self.known_enemy_structures) > 0 and len(self.main_force_ids) >= 30:
         target = random.choice(self.known_enemy_structures)
         for marine in self.units(UnitTypeId.MARINE):
            if marine.tag in self.main_force_ids:
               await self.do(marine.attack(target))
      return

   async def attack_enemy_start(self):
      if len(self.known_enemy_units) > 0 and len(self.main_force_ids) >= 30:
         target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
         for marine in self.units(UnitTypeId.MARINE):
            for unit_tag in self.main_force_ids:
               if marine.tag == unit_tag:
                  await self.do(marine.attack(target))
      return

   async def harass(self):
      if len(self.harass_force_ids) >= 10 and self.can_harass == True:
         self.can_harass = False
         target = self.enemy_start_locations[0]
         """
         Marines need to attack
         """
         for marine in self.units(UnitTypeId.MARINE):
            if marine.tag in self.harass_force_ids:
                  await self.do(marine.attack(target))
         # Helions attack
         for hel in self.units(UnitTypeId.HELION):
            if hel.tag in self.harass_force_ids:
               await self.do(hel.attack(target))
      return

   async def position_defensive_units(self):
      for marine in self.units(UnitTypeId.MARINE):
         if marine.tag in self.defence_unit_ids:
            await self.do(marine.move(self.start_location[1]).position)
      return

   async def create_factory(self, cc):
      if self.units(UnitTypeId.BARRACKS).ready.amount >= 2:
         if self.units(UnitTypeId.FACTORY).amount < 2:
            await self.build(UnitTypeId.FACTORY, near=cc.position.towards(self.game_info.map_center, 10))

   async def build_helion(self):
      for f in self.units(UnitTypeId.FACTORY).ready.noqueue:
         while self.supply_left > 4:
            if not self.can_afford(UnitTypeId.HELION):
               break
            else:
               await self.do(f.train(UnitTypeId.HELION))
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

      self.iteration = iteration
      #self.time = (state.game_loop/22.4) /60
      #print('time: {}'.format(self.time))

      await self.split_army()
      await self.clean_up()
      await self.distribute_workers()
      await self.scout()
      await self.expand()
      await self.perform_task()
      #await self.defend()
      await self.create_barracks(cc)
      await self.create_factory(cc)

      #await self.upgrade_to_orbital()
      await self.build_supply_depots(cc)
      await self.build_workers(cc)
      await self.lower_supply_depots()              #Only works on one supplydepot
      await self.intel()

      #await self.position_defensive_units()

      #await self.put_miners_to_work(cc)
      #await self.create_barracks(cc)
      await self.build_refinery()
      #await self.build_offensive_force()
      #await self.attack()

      #if self.iteration % 500 == 0:
      #   self.harass_force_has_attacked = False

      if self.iteration % 400 == 0:
         self.build_another_barrack = True
      if self.iteration % 100 == 0:
         self.can_harass = True
      #if self.iteration % 50 == 0:
      #   print('Number of harass force:
      #   {}'.format(len(self.harass_force_ids)))
      #   print('Number of main force: {}'.format(len(self.main_force_ids)))
      return
          
def main():
   count = 0
   while count != 100:
      run_game(sc2.maps.get("Sequencer LE"), 
               [Bot(Race.Terran, MyBot(use_model=False)),
                Computer(Race.Protoss, Difficulty.Easy)],
               realtime = False)
      count += 1
      print('---The count is: {}'.format(str(count)))

if __name__ == '__main__':
    main()








   #async def put_miners_to_work(self, cc):
   #   """
   #   Put idle miners back to work
   #   """
   #   for scv in self.units(SCV).idle:
   #      await self.do(scv.gather(self.state.mineral_field.closest_to(cc)))
   #   return


      #async def attack(self):
   #   if len(self.units(UnitTypeId.MARINE).idle) > 0:
   #      target = False
   #      if self.iteration > self.do_something_after:
   #         if self.use_model:
   #            prediction = self.model.predict([self.flipped.reshape([-1, 176, 200, 3])])
   #            choice = np.argmax(prediction[0])

   #            choice_dict = {0: "No Attack!",
   #                           1: "Attack close to our cc!",
   #                           2: "Attack Enemy Structure!",
   #                           3: "Attack Eneemy Start!",
   #                           4: "Harass!",
   #                           5: "Build Marine!"
   #                           }
   #            print('Choice #{}:{}'.format(choice, choice_dict[choice]))
   #         else:
   #            choice = random.randrange(0,5)

   #         # no attack
   #         if choice == 0:
   #            #print('choice 1')
   #            wait = random.randrange(65, 165)
   #            self.do_something_after = self.iteration + wait

   #         # Attack unit closest to our command center
   #         elif choice == 1:
   #            #print('choice 2')
   #            if len(self.known_enemy_units) > 0:
   #               target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
   #               #print('choic 2 target: {}'.format(target))
               
            
   #         # attack enemy structures
   #         #elif choice == 2:
   #            #print('choice 3')
   #            if len(self.known_enemy_structures) > 0:
   #               target = random.choice(self.known_enemy_structures)
   #               #print('choic 3 target: {}'.format(target))

   #         # attack enemy start
   #         elif choice == 3:
   #            #print('choice 4')
   #            target = self.enemy_start_locations[0]
   #            #print('choic 4 target: {}'.format(target))

   #         elif choice == 4:
   #            #print('choice 5')
   #            # For now, if the harass list is full, send them in.  Later I
   #            # need to come back and send them with more thought
   #            if len(self.harass_force_ids) >= 10:
   #               target = self.enemy_start_locations[0]
   #               for unit_id in self.harass_force_ids:
   #                  for unit in self.units(UnitTypeId.MARINE):
   #                     if unit_id == unit.tag:
   #                        await self.do(unit.attack(target))

   #         if target:
   #            if len(self.harass_force_ids) >= 10:
   #               for marine in self.units(UnitTypeId.MARINE):
   #                  if marine.tag in self.harass_force_ids:
   #                     await self.do(marine.attack(target))
   #         if target:
   #            if len(self.main_force_ids) >= 30:
   #               for marine in self.units(UnitTypeId.MARINE):
   #                  if marine.tag in self.main_force_ids:
   #                     await self.do(marine.attack(target))
   #               self.main_force_has_attacked = True

   #         #if self.main_force_has_attacked:
   #         #   if len(self.main_force_ids) >= 30:
   #         #      for marine in self.units(UnitTypeId.MARINE):
   #         #         if marine.tag in self.main_force_ids:
   #         #            await
   #         #            self.do(marine.attack(self.enemy_start_locations[1]))

   #         y = np.zeros(5)
   #         y[choice] = 1
   #         self.train_data.append([y, self.flipped])


   #async def do_actions(self, actions: List["UnitCommand"]):
   #   """
   #   This function is for controlling the units. I'm not sure that I will use it quite
   #   yet, but it is something that seems available
   #   """
   #   for action in actions:
   #      cost = self._game_data.calculate_ability_cost(action.ability)
   #      self.minerals -= cost.minerals
   #      self.vespene -= cost.vespene
   #   r = await self._client.actions(actions, game_data=self._game_data)
   #   return r