import simplejson as json
import numpy as np

def get_demand_types(dfile = 'demand_types.json'):
  with open(dfile) as df:
    dt = json.loads(df.read())
  return dt

def get_business_types(bfile = 'business_types.json'):
  with open(bfile) as bf:
    bt = json.loads(bf.read())
  return bt


def generate_person_name():
  # Returns a random name for a person
  return "Dmo"
def generate_business_name():
  # Returns a random name for a business
  return "Dmo's Chicken and Waffles"

def distance(loc1, loc2):
  # returns distance between two location tuples
  return np.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2)

def inside(loc1, loc2, radius):
  # returns boolean: is loc2 within radius distance of loc1?
  if loc2[0] - loc1[0] > radius or loc2[0] - loc1[0] < -radius:
    return False
  if loc2[1] - loc1[1] > radius or loc2[1] - loc1[1] < -radius:
    return False
  if distance(loc1, loc2) < radius:
    return True
  return False
