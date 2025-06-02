import math
import random
from collections import namedtuple

Dimensions = namedtuple('Dimensions', 'width height')
City = namedtuple('City', 'x y')

class Route:

    def __init__(self, cities = []):
        self.cities = cities
        self.distance = math.inf

    def generate(self, cities, start):
        self.cities = cities[:]
        random.shuffle(self.cities)
        self.cities.insert(0, start)
        self.cities.append(start)

    def calculate_distance(self):
        self.distance = 0
        i = 0
        while i < len(self.cities) - 1:
            origin = self.cities[i]
            destination = self.cities[i+1]
            self.distance += math.hypot(destination[0]-origin[0], destination[1]-origin[1])
            i += 1

    def mutate(self):
        start_city = self.cities[0]
        cities = [city for city in self.cities if city != start_city]
        c1 = random.randint(0, len(cities)-1)
        c2 = random.randint(0, len(cities)-1)
        cities[c2], cities[c1] = cities[c1], cities[c2]
        self.cities = [start_city] + cities + [start_city]

class GeneticAlgorithm:

    def __init__(self, size, muta, tour, nr_of_cities, map_dimensions):
        self.population_size = size
        self.mutation_rate = muta
        self.tournament_size = tour
        self.nr_of_cities = nr_of_cities
        self.map_dimensions = map_dimensions
        self.routes = []
        self.cities = []
        self.start_city = None
        self.generation = 0

        self._initialize()
    
    def _initialize(self):
        self._generate_random_cities()
        self.start_city = self.cities.pop(random.randint(0, len(self.cities)-1))
        self._generate_random_population()

    def _generate_random_cities(self):
        for i in range(0, self.nr_of_cities-2):
            self.cities.append((random.randrange(0, self.map_dimensions.width),
                                random.randrange(0, self.map_dimensions.height - 80)))

    def _generate_random_population(self):
        self.routes = [Route() for i in range(self.population_size)]

        for route in self.routes:
            route.generate(self.cities, self.start_city)
            route.calculate_distance()

    def select_route(self):
        tournament = []
        winner = Route()
        for i in range(0, self.tournament_size):
            R = random.randint(0, self.population_size - 1)
            tournament.append(self.routes[R])
        for route in tournament:
            if route.distance < winner.distance: winner = route
        return winner

    def breed(self):
        new_population = []

        for i in range(0, self.population_size - 1):
            father = self.select_route()
            mother = self.select_route()

            z = random.randint(1, self.nr_of_cities-2)
            father_part = father.cities[0:z]
            mother_part = [x for x in mother.cities if x not in father_part]

            child = Route(cities = [self.start_city] + mother_part + father_part + [self.start_city])

            rnd = random.randint(0, 100)
            if rnd < (self.mutation_rate*100):
                child.mutate()

            new_population.append(child)

        new_population.append(self.get_best_route())

        self.routes = new_population
    
    def update(self):
        self.breed()
        for route in self.routes:
            route.calculate_distance()
        self.generation += 1

    def get_best_route(self):
        return min(self.routes, key=lambda r: r.distance)