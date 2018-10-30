import sc2
import random
import numpy as np
import time
import math
from sc2 import run_game, maps, Race, Difficulty, Result
from sc2.constants import *
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.player import Bot, Computer, Human
from sc2.ids.unit_typeid import UnitTypeId
from typing import List
import time
import cv2
import os

#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
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
      # Gather the data
      self.train_data = []
      #use the model to train the bot
      self.use_model = use_model

      self.do_something_after = 0
      self.supply_cap = 200
      self.do_something_after = 0
      self.scouts_and_spots = {}
      self.scv_scout = []
      self.enemy_expansions = []

      self.build_two_more_barracks = False
      self.wasHarrassed = True

      # Trying to set up the attack force
      #self.main_force = {}
      #self.existing_main_ids = []
      #self.harass_force = {}
      #self.existing_harass_ids = []

      self.harass_force_ids = []
      self.main_force_ids = []

      #choices = { 0: self.build_supply_depots,
      #           1: self.build_marine,
      #           2: self.do_nothing,
      #           3: self.expand_now,
      #           }

      self.train_data = []
      if self.use_model:
         print('USING MODEL')
         self.model = keras.models.load_model("BasicCNN-10-epochs-0.0001-LR-STAGE1")
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
      return

   # ======================================================================================= THIS MAY BE IMPORTANT 
      #with open('gameout-random-vs-easy.txt', 'a') as f:
      #   if self.use_model:
      #      f.writelines('Model {}\n'.format(game_result))
      #   else:
      #      f.write('Random {}\n'.format(game_result))
      #return

   #def on_building_construction_complete(self, unit: UNIT):
   #   if (unit.ready)
   def is_first_barracks_built(self):
      if self.units(UnitTypeId.BARRACKS).amount == 1:
         return True
      else:
         return False
 
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

   async def build_supply_depots(self, cc):
      """
      This part will create the supply depots
      """
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
         if self.units(UnitTypeId.SCV).amount < 20:
            if self.can_afford(UnitTypeId.SCV) and self.units(UnitTypeId.SUPPLYDEPOT).amount >= 1:
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
      if self.can_afford(UnitTypeId.BARRACKS) and self.units(UnitTypeId.BARRACKS).amount < 2:
         await self.build(UnitTypeId.BARRACKS, near=cc.position.towards(self.game_info.map_center, 10))
      elif self.build_two_more_barracks:
         if self.can_afford(UnitTypeId.BARRACKS) and self.units(UnitTypeId.BARRACKS).amount < 5:
            await self.build(UnitTypeId.BARRACKS, near = cc.position.towards(self.game_info.map_center, 15))
      return

   def upgrade_barracks(self, unit: Unit):
      pass

      pass

   async def build_marauder(self):
      pass

   async def build_refinery(self):
      """
      Just build 2 refineries for now. I can worry about building more later
      """
      for cc in self.units(UnitTypeId.COMMANDCENTER).ready:
         if self.units(UnitTypeId.REFINERY).amount < 2:
            refineries = self.state.vespene_geyser.closer_than(15.0, cc)
            if self.units(UnitTypeId.SUPPLYDEPOT).amount >= 2:
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
      """
      if self.units(UnitTypeId.SUPPLYDEPOT).exists and self.units(UnitTypeId.SUPPLYDEPOT).amount < 15:
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

   async def attack(self):
      if len(self.units(UnitTypeId.MARINE).idle) > 0:
         target = False
         if self.iteration > self.do_something_after:
            if self.use_model:
               prediction = self.model.predict([self.flipped.reshape([-1, 176, 200, 3])])
               choice = np.argmax(prediction[0])

               choice_dict = {0: "No Attack!",
                              1: "Attack close to our nexus!",
                              2: "Attack Enemy Structure!",
                              3: "Attack Eneemy Start!"
                              }
               print('Choice #{}:{}'.format(choice, choice_dict[choice]))
            else:
               choice = random.randrange(0,5)

            # no attack
            if choice == 0:
               print('choice 1')
               wait = random.randrange(65, 165)
               self.do_something_after = self.iteration + wait

            # Attack unit closest to our command center
            elif choice == 1:
               print('choice 2')
               if len(self.known_enemy_units) > 0:
                  target = self.known_enemy_units.closest_to(random.choice(self.units(UnitTypeId.COMMANDCENTER)))
                  print('choic 2 target: {}'.format(target))
               
            
            # attack enemy structures
            elif choice == 2:
               print('choice 3')
               if len(self.known_enemy_structures) > 0:
                  target = random.choice(self.known_enemy_structures)
                  print('choic 3 target: {}'.format(target))

            # attack enemy start
            elif choice == 3:
               print('choice 4')
               target = self.enemy_start_locations[0]
               print('choic 4 target: {}'.format(target))

            elif choice == 4:
               print('choice 5')
               # For now, if the harass list is full, send them in. Later I need to come back and send them with more thought
               if len(self.harass_force_ids) >= 10:
                  target = self.enemy_start_locations[0]
                  for unit_id in self.harass_force_ids:
                     for unit in self.units(UnitTypeId.MARINE):
                        if unit_id == unit.tag:
                           await self.do(unit.attack(target))
                           



            if target:
               if len(self.harass_force_ids) >= 10:
                  for marine in self.units(UnitTypeId.MARINE):
                     if marine.tag in self.harass_force_ids:
                        print('harass tag is there')
                        await self.do(marine.attack(target))
            if target:
               if len(self.harass_force_ids) == 10 and len(self.main_force_ids) >= 50:
                  for marine in self.units(UnitTypeId.MARINE):
                     if marine.tag in self.main_force_ids:
                        print('main tag is there')
                        await self.do(marine.attack(target))

            y = np.zeros(5)
            y[choice] = 1
            self.train_data.append([y, self.flipped])
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
      # Periodically go and scout. This needs to be improve upon. Except I can't get self.state.game_loop equation to work for me.....
      if self.iteration % 10 == 0:
         isDone = False
      
      # For the moment, I am only checking for the firs initial base
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
      # After this, I would like to add a different unit as a scout, or use the orbital command if I can get that to work
      return
   
   def random_location_variance(self, enemy_start_location):
      x = enemy_start_location[0]
      y = enemy_start_location[1]

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

   async def harass(self):
      if len(self.units(UnitTypeId.MARINE)) and len(self.harass_force) == 10:
         for hu in self.units(UnitTypeId.MARINE).idle:
            self.harass_force.append(hu)
         self.build_two_more_barracks = True
      return

   async def split_army(self):
      if self.units(UnitTypeId.MARINE).exists:
         for marine in self.units(UnitTypeId.MARINE): 
            if len(self.harass_force_ids) < 10:
               if not marine.tag in self.harass_force_ids:
                  if not marine.tag in self.main_force_ids:
                     self.harass_force_ids.append(marine.tag)
            else:
               if not marine.tag in self.harass_force_ids:
                  if not marine.tag in self.main_force_ids:
                     self.main_force_ids.append(marine.tag)
      return

   async def clean_up(self):  
      if self.units(UnitTypeId.MARINE).exists:
         for marine in self.units(UnitTypeId.MARINE):
            if marine.tag in self.harass_force_ids:
               if marine.health < 1:
                  print('one of them died')
              

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
      #self.time = (self.state.game_loop / 22.4) / 60
      #print('Time:',self.time)

      await self.split_army()
      await self.upgrade_to_orbital()
      await self.build_supply_depots(cc)
      await self.build_workers(cc)
      await self.put_miners_to_work(cc)
      await self.create_barracks(cc)
      await self.build_refinery()
      await self.distribute_workers()
      await self.build_offensive_force()
      await self.attack()
      await self.lower_supply_depots()              #Only works on one supplydepot
      await self.expand()
      if not self.wasHarrassed:
         await self.harass()
      await self.scout()
      await self.intel()
      await self.clean_up()
      print('main army: {}'.format(len(self.main_force_ids)))
      print('harass army: {}'.format(len(self.harass_force_ids)))

          
def main():
   count = 0
   while count != 1:
      run_game(sc2.maps.get("Sequencer LE"), 
               [Bot(Race.Terran, MyBot(use_model=False)),
                Computer(Race.Protoss, Difficulty.Easy)],
               realtime = False)
      count += 1
      print('---The count is: {}'.format(str(count)))
   #run_game(sc2.maps.get("Sequencer LE"), [Bot(Race.Terran, MyBot()),
   #   Bot(Race.Protoss, CannonRushBot())],
   #        realtime = False)
if __name__ == '__main__':
    main()











      #async def scout(self):
      ## {Distance to enmy start: expansion logic}
      #self.expand_dis_dir = {}
      #for el in self.expansion_locations:
      #   distance_to_enemy_start = el.distance_to(self.enemy_start_location[0])
      #   self.expand_dis_dir[distance_to_enemy_start] = el
      #self.ordered_exp_distances = sorted(k for k in self.expand_dis_dir)

      #existing_ids = [unit.tag for unit in self.units]
      #to_be_removed = []
      #for noted_scout in self.scouts_and_spots:
      #   if noted_scout not in existing_ids:
      #      to_be_removed.append(noted_scout)
      #for scout in to_be_removed:
      #   del self.scouts_and_spots[scout]

      #if len(self.units(UnitTypeId.BARRACKS).ready) == 0:
      #   UNIT_TYPE = UnitTypeId.SCV
      #   unit_limit = 1
      #else:
      #   unit_type = UnitTypeId.MARINE
      #   unit_limit = 5

      #assign_scout = True

      #if Unit_type == UnitTypeId.SCV:
      #   for unit in self.units(UnitTypeId.SCV):
      #      if unit.tag in self.scoutgs_and_spots:
      #         assign_scout = False

      #if assign_scout:
      #   if len(self.units(unit_type).idle) > 0:
      #      for su in self.units(unit_type).idle[:unit_limit]:
      #         if su.tag not in self.scouts_and_spots:
      #            for dist in self.ordered_exp_distances:
      #               try:
      #                  #location = next(value for KeyboardInterrupt, value in self.expand_dis_dir.items if key == dist)
      #                  location = self.expand_dis_dir[dist]
      #                  active_locations = [self.scounts_and_spots[k] for k in self.scouts_and_spots]
      #                  if location not in active_locations:
      #                     if unit_type == UnitTypeid.SCV:
      #                        for unit in self.units(UnitTypeId.SCV):
      #                           if unit.tag in self.scouts_and_spots:  
      #                              continue
      #                     await self.do_actions(su.move(location))
      #                     self.scounts_and_spots[su.tag] = location
      #                     break
                              
      #               except Exception as e:
      #                  print(str(e))
      #for su in self.units(unit_type):
      #   if su.tag in self.scouts_and_spots:
      #      if obs in [scv for scv in self.units(UnitTypeId.SCV)]:
      #         await self.do(su.move(self.random_location_variance(self.scounts_and_spots[su.tag])))
      #return