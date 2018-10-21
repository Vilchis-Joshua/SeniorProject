import random
import sc2
import numpy as np
from sc2 import run_game, maps, Race, Difficulty, Result
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.player import Bot, Computer, Human
from sc2.ids.unit_typeid import UnitTypeId
from typing import List
from sc2.helpers import ControlGroup
import time


# Maybe I will end up using these later
#import tensorflow as tf
#from tensorflow import keras as ks
import cv2

import os
#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
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
      9) Create x number of marauder and y number of helion
      10) When 200 supply cap reached, it will then attack in full force
      11) Repeat strategy
   """
   # Initialize
   def __init__(self):
      self.combinedActions = []
      self.attack_group = set()
      self.ITERATIONS_PER_MINUTE = 165
      self.train_data = []
      self.do_something_after = 0

   def on_end(self, game_result):
      """
      Trying to figure out the benefit of this
      """
      print('--on_end called')
      print(game_result)

      if game_result == Result.Victory:
         np.save("train_data/{}.npy".format(str(int(time.time()))), np.array(self.train_data))

   async def do_actions(self, actions: List["UnitCommand"]):
      """
      This function is for controlling the units. I'm not sure that I will use it quite
      yet, but it is something that seems available
      """
      for action in actions:
         cost = self._game_data.calculate_ability_cost(action.ability)
         self.minerals -= cost.minerals
         self.vespene -= cost.vespene
      r = await self._client.actions(actions, game_data=self._game_data)
      return r

   async def create_supply_depots(self, cc):
      """
      This part will create the supply depots
      """
      if self.can_afford(SUPPLYDEPOT) and not self.units(SUPPLYDEPOT).exists:
         await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))
      elif self.units(SUPPLYDEPOT).exists:
         if self.units(BARRACKS).ready.exists and self.supply_left < 8 and self.can_afford(SUPPLYDEPOT):
            if not self.already_pending(SUPPLYDEPOT):
               await self.build(SUPPLYDEPOT, near=cc)
      return

   async def build_workers(self, cc):
      """
      Get up to the 18 miners.  This seems to not count the SCV being used to
      build something.
      """


      if not self.already_pending(UnitTypeId.SCV):
         if self.units(UnitTypeId.SCV).amount < 20:
            if self.can_afford(UnitTypeId.SCV) and self.units(SUPPLYDEPOT).amount == 1:
               if self.units(UnitTypeId.SCV).amount < 19 and not self.already_pending(UnitTypeId.SCV):
                  await self.do(cc.train(UnitTypeId.SCV))
      return

   async def put_miners_to_work(self, cc):
      """
      Put idle miners back to work
      """
      for scv in self.units(SCV).idle:
         await self.do(scv.gather(self.state.mineral_field.closest_to(cc)))
      return

   async def create_barracks(self, cc):
      """
      Create barracks
      """
      if self.can_afford(BARRACKS) and self.units(BARRACKS).amount < 2:
         await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 10))
      return

   async def build_refinery(self):
      """
      Just build 2 refineries for now. I can worry about building more later
      """
      for cc in self.units(UnitTypeId.COMMANDCENTER).ready:
         if self.units(UnitTypeId.REFINERY).amount < 2:
            refineries = self.state.vespene_geyser.closer_than(15.0, cc)
            for refinery in refineries:
               if not self.can_afford(UnitTypeId.REFINERY):
                  break
               worker = self.select_build_worker(refinery.position)
               if worker is None:
                  break
               if not self.units(UnitTypeId.REFINERY).closer_than(1.0, refinery).exists:
                  await self.do(worker.build(UnitTypeId.REFINERY, refinery))
      return

   async def build_offensive_force(self):
      """
      Create marines for now. I Need to try and create the other units here too.
      """
      for rax in self.units(UnitTypeId.BARRACKS).ready.noqueue:
         if not self.can_afford(UnitTypeId.MARINE):
            break
         if self.supply_left > 4:
            await self.do(rax.train(UnitTypeId.MARINE))
      return

   async def lower_supply_depots(self):
      """
      This will raise the supply depots when necessary
      for depo in self.units(UnitTypeId.SUPPLYDEPOT).ready:
         for unit in self.known_enemy_units.not_structure:
            if unit.position.to2.distance_to(depo.position.to2) < 15:
               break
            else:
               await self.do(depo(MORPH_SUPPLYDEPOT_LOWER))
      """
      for depot in self.units(UnitTypeId.SUPPLYDEPOT).ready:
         self.combinedActions.append(depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER))
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
      if self.units(UnitTypeId.COMMANDCENTER).amount < 2 and self.can_afford(NEXUS):
         await self.expand_now()
      #if self.units(UnitTypeId.COMMANDCENTER).amount < (self.iteration / self.ITERATIONS_PER_MINUTE) and self.can_afford(UnitTypeId.COMMANDCENTER):
      #   await self.expand_now()
      return

   async def upgrade_to_orbital(self):
      """
      This function is for the purpose of creating the orbital command post
      """
      pass

   async def attack(self):
      """
      The function for attacking. Need to work on it a little bit
      """
      #if self.units(UnitTypeId.MARINE).amount > 3:
      #   if len(self.known_enemy_units) > 0:
      #      for marine in self.units(UnitTypeId.MARINE).idle:
      #         await
      #         self.do(marine.attack(random.choice(self.known_enemy_units)))
      #   elif self.units(UnitTypeId.MARINE).amount > 3:
      #      if len(self.known_enemy_units) > 3:
      #         for marine in self.units(UnitTypeId.MARINE).idle:
      #            await
      #            self.do(marine.attack(random.choice(self.known_enemy_units)))
       # {UNIT: [n to fight, n to defend]}
      aggressive_units = {MARINE: [2, 2]}
      
      if self.units(UnitTypeId.MARINE).amount > 20:
         for UNIT in aggressive_units:
            if self.units(UNIT).amount > aggressive_units[UNIT][0] and self.units(UNIT).amount > aggressive_units[UNIT][1]:
               for s in self.units(UNIT).idle:
                  await self.do(s.attack(self.find_target(self.state)))
                  #self.find_target(self.state)

            elif self.units(UNIT).amount > aggressive_units[UNIT][1]:
               if len(self.known_enemy_units) > 0:
                  for s in self.units(UNIT).idle:
                     await self.do(s.attack(random.choice(self.known_enemy_units)))
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

      draw_dict = {
                  COMMANDCENTER: [15, (0, 255, 0)],
                  SUPPLYDEPOT: [3, (20, 235, 0)],
                  #MINER: [1, (55, 200, 0)],
                  MARINE: [1, (55, 200, 0)]
                  }
      for unit_type in draw_dict:
         for unit in self.units(unit_type).ready:
            pos = unit.position
            cv2.circle(game_data, (int(pos[0]), int(pos[1])), draw_dict[unit_type][0], draw_dict[unit_type][1], -1)
      game_data = np.zeros((self.game_info.map_size[1], self.game_info.map_size[0], 3), np.uint8)
      for command_center in self.units(UnitTypeId.COMMANDCENTER):
         command_center_pos = command_center.position
         print(command_center_pos)
         cv2.circle(game_data, (int(command_center_pos[0]), int(command_center_pos[1])), 10, (0, 255, 0), -1)
         flipped = cv2.flip(game_data, 0)
         resized = cv2.resize(flipped, dsize=None, fx=2, fy=2)
         cv2.imshow('Intel', resized)
         cv2.waitKey(1)


      main_base_names = ['commandcenter', 'hatchery', 'nexus']
      for enemy_building in self.known_enemy_structures:
         pos = enemy_building.position
         if enemy_building.name.lower() not in main_base_names:
            cv2.circle(game_data, (int(pos[0]), int(pos[1])), 5, (200, 50, 212), -1)
      for enemy_building in self.known_enemy_structures:
         pos = enemy_building.position
         if enemy_building.name.lower() in main_base_names:
            cv2.circle(game_data, (int(pos[0]), int(pos[1])), 15, (0, 0, 255), -1)

      for enemy_unit in self.known_enemy_units:
         if not enemy_unit.is_structure:
            worker_names = ['probe',
               'scv',
               'drone']
            pos = enemy_unit.position
            if enemy_unit.name.lower() in worker_names:
               cv2.circle(game_data, (int(pos[0]), int(pos[1])), 1, (55, 0, 155), -1)
            else:
               cv2.circle(game_data, (int(pos[0]), int(pos[1])), 3, (50, 0, 215), -1)

              # flip horizontally to make our final fix in visual
              # representation:
      flipped = cv2.flip(game_data, 0)
      resized = cv2.resize(flipped, dsize=None, fx=2, fy=2)

      cv2.imshow('Intel', resized)
      cv2.waitKey(1)

   async def scout(self):
      #if len(self.units(UnitTypeId.))
      pass

   async def on_step(self, iteration):
      #self.combinedActions = []
      #self.attack_group = set()
      cc = self.units(UnitTypeId.COMMANDCENTER)
      if not cc.exists:
         target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
         for unit in self.workers | self.units(MARINE):
            await self.do(unit.attack(target))
         return
      else:
         cc = cc.first

      self.iteration = iteration

      await self.create_supply_depots(cc)
      await self.build_workers(cc)
      await self.put_miners_to_work(cc)
      await self.create_barracks(cc)
      await self.build_refinery()
      await self.distribute_workers()
      await self.build_offensive_force()
      await self.intel()
      await self.attack()
      await self.lower_supply_depots()              #Only works on one supplydepot
      await self.expand()                           
      #await self.do_actions(self.combinedActions)
      

          

def main():
    run_game(sc2.maps.get("Sequencer LE"), [Bot(Race.Terran, MyBot()),
        Computer(Race.Protoss, Difficulty.Easy)], realtime = False)

if __name__ == '__main__':
    main()
