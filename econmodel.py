'''
Small business lifecycle modeling based on individual consumer needs

Written by Dan Morris. 9/27/14 -

Overview:
  We create a city which contains people and small businesses. People generate
    needs each cycle and go to nearby businesses to fulfill those needs. If a
    person cannot find a business close by to fulfill their needs, those needs
    accumulate and their search radius expands. Businesses spend cash each
    cycle, and must take in enough revenue to stay afloat. If a business's cash
    drops below zero, that business dies and can be replaced by a new startup.

  Each cycle represents approximately one earth-week.

Objects:
  City
  Person
  Business
  BusinessLocation
  BusinessType
  DemandType

Helper Files:
  functions.py - contains non-object functions
  business_types.json - contains reference of business types
  demand_types.json - contains reference of demand types
'''

import numpy as np
from scipy.stats import poisson, norm
from random import sample, choice
import functions as f
import plotting as plots

class City(object):
  def __init__(self, name, size, n_people):
    self.name = name
    self.size = float(size) # radius of the city
    self.age = 0 # number of cycles

    self.dtypes = self.compile_dtypes()
    self.btypes = self.compile_btypes()
    self.people = []
    self.populate(n_people)
    self.businesses = []
    self.business_locations = self.generate_business_locations()
    self.business_populate(ratio = .75)
    self.failed_businesses = []

    self.pophistory = [self.popreport()]
    self.bizhistory = [self.bizreport()]

  def compile_dtypes(self):
    '''
    Create a dict of demand type information, keyed by type-name
    '''
    dtraw = f.get_demand_types() # dict of demand types from json
    dt = {}
    for t in dtraw:
      dt[t] = DemandType(t,
                         dtraw[t]['dlambda'],
                         dtraw[t]['dprice'])
    return dt

  def compile_btypes(self):
    '''
    Create a dict of business type information, keyed by type-name
    '''
    btraw = f.get_business_types()
    bt = {}
    for t in btraw:
      bt[t] = BusinessType(t, btraw[t]['init_cash'],
                           btraw[t]['init_need_threshold'],
                           btraw[t]['init_need_radius'],
                           btraw[t]['burnrate'])
    return bt

  def populate(self, n):
    '''
    Adds n people to the city
    '''
    for i in range(n):
      self.people.append(Person(self, f.generate_person_name()))

  def generate_business_locations(self):
    '''
    Simplified: Create a business location at every (int, int) location in
      the city limits.
    '''
    bl = []
    for x in range(-int(self.size), int(self.size) + 1):
      for y in range(-int(self.size), int(self.size) + 1):
        if f.inside((x, y), (0, 0), self.size):
          bl.append(BusinessLocation(self, (x, y)))
    return bl

  def business_populate(self, ratio):
    '''
    Fills the city with businesses. The ratio specifies what percentage of the
      business locations will be filled initially.
    '''
    nl = len(self.business_locations)
    fill_indices = sample(range(nl), int(nl * ratio))
    for i in fill_indices:
      bt = choice(self.btypes.keys())
      self.btypes[bt].startup(self, self.business_locations[i],
                 f.generate_business_name())

  def pop_density_rand(self):
    '''
    Returns a location tuple for a new person in the city
    Samples randomly based on population density
    Currently: normal distribution in both X and Y directions
    '''
    loc = (self.size + 1, 0)
    while f.distance(loc, (0, 0)) > self.size:
      loc = (norm(scale = self.size).rvs(), norm(scale = self.size).rvs())
    return loc

  def bizfail(self, business):
    '''
    Clean up a dead business
    '''
    self.failed_businesses.append(business)
    self.businesses.remove(business)
    business.blocation.free()

  def city_cycle(self):
    '''
    Runs one life-cycle for the whole city
    1) People generate needs
    2) Empty business locations try to fill
    3) People fulfill needs
    4) Businesses pay billz and maybe die
    '''
    self.age += 1
    for p in self.people:
      p.generate()
    for bl in self.business_locations:
      if bl.available:
        best = 0
        best_type = None
        for bname, b_obj in self.btypes.iteritems():
          s = b_obj.startup_score(self, bl)
          if s > best:
            best = s
            best_type = b_obj
        if best >= 1:
          best_type.startup(self, bl, f.generate_business_name())
    for p in self.people:
      p.fulfill()
    for b in self.businesses:
      b.burn()
    self.pophistory.append(self.popreport())
    self.bizhistory.append(self.bizreport())

  def life(self, ncycles):
    '''
    The main module! Runs n cycles of life in the city.
    Add statistical or plotting functions as desired.
    '''
    for i in xrange(ncycles):
      self.city_cycle()

  def bizreport(self):
    '''
    Creates a dictionary of current business status in the city.
    Use for time-series plots or something.
    '''
    bd = {}
    for b_type, bt_obj in self.btypes.iteritems():
      bd[b_type] = {'count': 0, 'totalcash': 0.0}
    for b in self.businesses:
      bd[b.type]['count'] += 1
      bd[b.type]['totalcash'] += b.cash
    return bd

  def popreport(self):
    '''
    Creates a dictionary of current people status in the city.
    Use for time-series plots or something.
    '''
    pd = {}
    for d_type, dt_obj in self.dtypes.iteritems():
      pd[d_type] = {'demand_count': 0, 'total_demand': 0.0}
    for p in self.people:
      for n_type, n_amt in p.needs.iteritems():
        if n_amt > 0:
          pd[n_type]['demand_count'] += 1
          pd[n_type]['total_demand'] += n_amt
    return pd

class Person(object):
  def __init__(self, city, name):
    self.city = city
    self.name = name
    self.location = city.pop_density_rand()
    self.needs = self.init_needs()

  def init_needs(self):
    needs = {}
    for n in self.city.dtypes:
      needs[n] = 0
    return needs

  def cycle(self):
    '''
    Runs one life-cycle for the person
    '''
    self.generate()
    self.fulfill()

  def generate(self):
    '''
    Randomly generates this cycle's demand based on needs
    '''
    for n in self.city.dtypes:
      self.needs[n] += poisson.rvs(self.city.dtypes[n].dlambda) * \
                               self.city.dtypes[n].dprice

  def fulfill(self):
    '''
    Tries to fulfill needs at nearby businesses. Currently chooses randomly
      from businesses inside the demand radius.
    '''
    for need, amt in self.needs.iteritems():
      r = self.city.dtypes[need].demand_radius(amt)
      pos_biz = [] # potential businesses
      for b in self.city.businesses:
        if f.distance(b.location, self.location) < r:
          pos_biz.append(b)
      if len(pos_biz) > 0:
        # choose a random business to win
        self.give_biz(need, choice(pos_biz))

  def give_biz(self, need, business):
    '''
    Gives the business to that business. Empties need, pays the loots.
    '''
    payment = self.needs[need] * self.city.dtypes[need].dprice
    business.cash += payment
    self.needs[need] = 0

class Business(object):
  def __init__(self, city, name, blocation, btype):
    self.city = city
    self.name = name
    self.blocation = blocation
    self.blocation.fill()
    self.location = self.blocation.location
    self.btype = btype
    self.type = btype.bname
    self.cash = btype.initial_cash
    self.birthday = city.age
    self.deathday = None
    self.lifespan = None

  def __repr__(self):
    return self.name + ' [type: ' + self.btype.bname + '] [age: ' + \
           str(self.age) + '] [cash: $' + str(self.cash) + ']'

  def age(self):
    if self.deathday == None:
      return self.city.age - self.birthday
    return self.deathday - self.birthday

  def burn(self):
    '''
    Pay the billz for this cycle.
    '''
    self.cash -= self.btype.burnrate
    if self.cash < 0:
      self.die()

  def die(self):
    '''
    Clear location for some other business to take over
    '''
    self.deathday = self.city.age
    self.lifespan = self.deathday - self.birthday
    self.city.bizfail(self)

class BusinessLocation(object):
  def __init__(self, city, location):
    self.city = city
    self.location = location
    self.available = True

  def free(self):
    self.available = True

  def fill(self):
    self.available = False

class BusinessType(object):
  def __init__(self, bname, init_cash, init_need_threshold,
               init_need_radius, burnrate):
    self.bname = bname
    self.initial_cash = init_cash
    self.initial_need_threshold = init_need_threshold
    self.initial_need_radius = init_need_radius
    self.burnrate = burnrate

  def startup_score(self, city, blocation):
    '''
    Determines how good this location would be to start a business of this type
    Must be >= 1 to trigger a startup.
    '''
    local_demand = 0.
    for p in city.people:
      if f.inside(p.location, blocation.location, self.initial_need_radius):
        local_demand += p.needs[self.bname]
    return local_demand / self.initial_need_threshold

  def startup(self, city, blocation, name):
    '''
    Starts a business of this type in that location!
    '''
    city.businesses.append(Business(city, name, blocation, self))

class DemandType(object):
  def __init__(self, dname, dlambda, dprice):
    self.dname = dname
    self.dlambda = dlambda
    self.dprice = dprice

  def demand_radius(self, need_amount):
    '''
    Determines the radius that a person will go to fulfill this type of need
      given the quantity of need
    '''
    return 1. + need_amount / self.dlambda


def main():
  city = City("Dmotopia", 10, 1000)
  city.life(200)
  plots.business_history(city)

if __name__ == '__main__':
  main()
