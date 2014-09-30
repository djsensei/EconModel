import matplotlib.pyplot as plt
import seaborn as sns

def basic_population(city):
  plocs = [p.location for p in city.people]
  x = [p[0] for p in plocs]
  y = [p[1] for p in plocs]
  plt.scatter(x, y, color = 'blue')
  plt.Circle((0,0), radius = city.size, color = 'black')
  plt.title('Population of ' + city.name)
  plt.xlabel('X')
  plt.ylabel('Y')
  plt.show()

def basic_business(city):
  blocs = [b.location for b in city.businesses]
  x = [b[0] for b in blocs]
  y = [b[1] for b in blocs]
  plt.scatter(x, y, color = 'red')
  plt.Circle((0,0), radius = city.size, color = 'black')
  plt.title('Businesses of ' + city.name)
  plt.xlabel('X')
  plt.ylabel('Y')
  plt.show()

def population_and_business(city):
  plocs = [p.location for p in city.people]
  px = [p[0] for p in plocs]
  py = [p[1] for p in plocs]
  plt.scatter(px, py, color = 'blue', label = "People")
  plt.Circle((0,0), radius = city.size, color = 'black')
  blocs = [b.location for b in city.businesses]
  bx = [b[0] for b in blocs]
  by = [b[1] for b in blocs]
  plt.scatter(bx, by, color = 'red', label = "Businesses")
  plt.title('Population and Businesses of ' + city.name)
  plt.xlabel('X')
  plt.ylabel('Y')
  plt.show()

def business_history(city):
  f, (ax1, ax2) = plt.subplots(211)
  for d_type, dt_obj in city.dtypes.iteritems():
    cash = [b[d_type]['totalcash'] for b in city.bizhistory]
    ax1.plot(cash, label = d_type)
  ax1.title('Business cash over time')
  ax1.ylabel('Cashish')
  ax1.legend()
  for d_type, dt_obj in city.dtypes.iteritems():
    count = [b[d_type]['count'] for b in city.bizhistory]
    ax2.plot(count, label = d_type)
  ax2.title('Business count over time')
  ax2.xlabel('Cycles')
  ax2.ylabel('# Businesses')
  ax2.legend()
  plt.show()
