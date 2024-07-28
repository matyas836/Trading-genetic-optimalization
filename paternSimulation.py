import pandas as pd
import numpy as np
import re
import random
import time
import math
import yfinance as yf
import matplotlib.pyplot as plt
#
class PaternsSimulation:

    def __init__(self,data,fixedPositionSize,populationSize,generations,mutationRate,holdTime):
        self.marketData =  data
        self.fixedPositionSize = fixedPositionSize
        self.populationSize = populationSize
        self.generations = generations
        self.mutationRate = mutationRate
        self.holdTime = holdTime
        self.tradeHistory = pd.DataFrame(columns=['pnl','profit','date'])
        self.lastFitnessValues = []
        self.averageGen = []
        self.topFitness = []
        self.genCompleted = 0
        self.genTime = None
    
    def generatePatern(self):
            all_attributes = ['Close', 'Low', 'High', 'Volume']
            comparators = ['>', '<', '>=', '<=']
            index_range = range(-5, 0)  
        
            num_conditions = random.randint(2, 5)  # Number of conditions per pattern
            conditions = []

            for _ in range(num_conditions):
                attr1 = random.choice(all_attributes)
                
                if attr1 == 'Volume':
                    attr2 = 'Volume'  # Ensure Volume is only compared to Volume
                else:
                    attr2 = random.choice(all_attributes)
                    # Ensure non-volume attributes do not compare to Volume
                    while attr2 == 'Volume':
                        attr2 = random.choice(all_attributes)
                
                comp = random.choice(comparators)
                index1 = random.choice(index_range)
                index2 = random.choice(index_range)

                # Ensure that the comparison is between different indices
                while index1 == index2:
                    index2 = random.choice(index_range)

                condition = f"{attr1}[{index1}] {comp} {attr2}[{index2}]"
                conditions.append(condition)

            pattern = ' and '.join(conditions)

            return pattern

    # Convert pattern to if logic statement function
    def checkPatern(self,pattern, date):
        conditions = pattern.split(' and ')
        eval_conditions = []

        for condition in conditions:
        
            attr1, comp, attr2 = condition.split(' ')  # Extract attributes and comparator
            attr1, index1 = attr1.split('[')
            attr2, index2 = attr2.split('[')
            index1 = int(index1[:-1])
            index2 = int(index2[:-1])
            
            # Get the dates to be used in comparison
            date1 = self.marketData.index.get_loc(date) + index1
            date2 = self.marketData.index.get_loc(date) + index2

            # Ensure indices are within the valid range
            if date1 < 0 or date2 < 0 or date1 >= len(self.marketData) or date2 >= len(self.marketData):
                return False  # Invalid indices, skip this condition

            date1 = self.marketData.index[date1]
            date2 = self.marketData.index[date2]

            eval_condition = f"self.marketData.loc['{date1}', '{attr1}'] {comp} self.marketData.loc['{date2}', '{attr2}']"
            eval_conditions.append(eval_condition)

            full_condition = ' and '.join(eval_conditions)
        
        return eval(full_condition)
    
    def initializePopulation(self):
        population = []
        #initialize population
        while len(population) < self.populationSize:
            patern = self.generatePatern()
            if patern not in population:
                population.append(patern)
        return population
    
    def selectParents(self, population, fitnessValues):
    
        #print(fitnessValues)
        #if the fitness parameter is profit, we have to normalize the number so it is between 0 and 1, 0 meaning the worst profit in the generation and 1 the best in the generation
        min_fitness = np.min(fitnessValues)
        max_fitness = np.max(fitnessValues)
        #if the min_fitness is negative, we shift the value so the worst profit is still positive
        if(min_fitness < 0):
            min_fitness = abs(min_fitness)
            max_fitness = abs(min_fitness) + max_fitness
        
        # If all fitness values are equal, assign equal weights
        if max_fitness == min_fitness:
            normalized_fitness = np.ones_like(fitnessValues)

        else:
            # Normalize to range [0, 1]
            if max_fitness != 0:
                normalized_fitness = (fitnessValues + min_fitness) / (max_fitness)
            else:
                #if maximum fitness is 0, the parents will be random 
                return random.choices(population,k=2)
            
       # print("normalized fitness",normalized_fitness)
        parents = random.choices(population, weights=normalized_fitness, k=2)
        return parents


    # Function to split patterns at logical operators and generate new child patterns
    def crossChildren(self,pattern1, pattern2):
        # Find all split points in the patterns
        split_points1 = [i for i, token in enumerate(pattern1.split()) if token in ['and']]
        split_points2 = [i for i, token in enumerate(pattern2.split()) if token in ['and']]
        
        # If no split points are found in either pattern, return the original patterns
        if not split_points1 or not split_points2:
            return pattern1, pattern2
        
        # Randomly select split points from both patterns
        split_point1 = random.choice(split_points1)
        split_point2 = random.choice(split_points2)
        
        # Split the patterns at the chosen split points
        part1_pattern1 = ' '.join(pattern1.split()[:split_point1])
        part2_pattern1 = ' '.join(pattern1.split()[split_point1:])
        
        part1_pattern2 = ' '.join(pattern2.split()[:split_point2])
        part2_pattern2 = ' '.join(pattern2.split()[split_point2:])
        
        # Generate child patterns by combining the parts
        child_pattern1 = part1_pattern1 + ' ' + part2_pattern2
        child_pattern2 = part1_pattern2 + ' ' + part2_pattern1
        
        return child_pattern1, child_pattern2

    def mutatePattern(self,pattern):
        # Tokenize the pattern into components
        tokens = pattern.split()
        
        # Define possible mutations for each token type
        operators = ['>', '<', '>=', '<=', '==']
        logical_ops = ['and']
        
        # Traverse each token and apply mutation based on the mutation rate
        for i, token in enumerate(tokens):
            if random.random() < self.mutationRate:
                # Randomly mutate comparison operators
                if token in operators:
                    tokens[i] = random.choice(operators)
                # Randomly mutate logical operators
                elif token in logical_ops:
                    tokens[i] = random.choice(logical_ops)
                # Randomly mutate numerical values within conditions (e.g., [-4], [5])
                elif re.match(r'\[.*\]', token):
                    num = int(re.findall(r'-?\d+', token)[0])
                    tokens[i] = f'[{num + random.choice([-1, 1])}]'
        
        # Reassemble the pattern
        mutated_pattern = ' '.join(tokens)
        return mutated_pattern
    
    def fitness(self, patern):
        
        start = time.perf_counter()
        #create a simulation object with the input
        result = self.runSimulation(3,patern)
        #
        end = time.perf_counter()
        #
        self.genTime += end-start

        return result
    
    
    def runSimulation(self,holdCandles,patern):

        results = pd.DataFrame(columns=['pnl','profit','date'])
        datalen = len(self.marketData.index)
        #loop through each candle in market data and check if patern is there
        for i in range(holdCandles,datalen-holdCandles):
            date = self.marketData.index[i]
            #if we found a patern we open a position
            if(self.checkPatern(patern,date)):
                #
                nextDate = self.marketData.index[i+holdCandles]
                pnl = round((math.log(self.marketData.loc[nextDate,'Close']) - math.log(self.marketData.loc[date,'Close'])),3)
                profit = pnl*self.fixedPositionSize
                results.loc[len(results.index)] = [pnl*100,profit,date]
        
        #print(len(self.tradeHistory.index))
        return results['profit'].sum()
    
    
    def optimize(self):

        population = self.initializePopulation()
        bestIndividual = None
        bestFitness = -float('inf')
        seen_individuals = set()  # Set to track seen individuals
        # List to store the best 10 fitness values and corresponding individuals of one generations
        bestFitnessList = []
        
      
        #main loop to go through generations
        for generation in range(self.generations):

            self.genTime = 0
            fitnessValues = []
            #run the simulation for each individual in population
            for patern in population:
                fitnessValues.append(self.fitness(patern))
                #print(f"Simulation result: {fitnessValues[len(fitnessValues)-1]} ")

            #get the best one
            currentBestFitness = max(fitnessValues)
            
            if self.lastFitnessValues and currentBestFitness <= min(self.lastFitnessValues):
                self.lastFitnessValues.append(currentBestFitness)
            else:
                self.lastFitnessValues = [currentBestFitness]

            bestIndex = fitnessValues.index(currentBestFitness)
            
            #update best fitness and individual in population
            if currentBestFitness > bestFitness:
                bestFitness = currentBestFitness
                bestIndividual = population[bestIndex]
                
            # Get the top 10 fitness values and corresponding paterns in the current generation
            top10Indices = np.argsort(fitnessValues)[-10:]  

            bestPatterns = [item[1] for item in bestFitnessList]

            for index in top10Indices:
                patern = population[index]  # Make sure to get the pattern from the population using the index
                if patern not in bestPatterns:
                    bestFitnessList.append((fitnessValues[index], patern))

            
            #create a new population
            newPopulation = []
            while len(newPopulation) < self.populationSize:
                parent1, parent2 = self.selectParents(population, fitnessValues)
                
                # Create 2 kids
                children = self.crossChildren(parent1,parent2)

                #mutate them
                for kid in children:
                    kid = self.mutatePattern(kid)

                    #check if child is unique       
                    if kid not in seen_individuals:
                        newPopulation.append(kid)
                        seen_individuals.add(kid)
                            
                    #if the child is already in the population we create a new random patern
                    else:
                        
                        newPopulation.append(self.generatePatern())
                    
                    
            population = newPopulation
            self.averageGen.append(round(np.mean(fitnessValues),2))
            self.topFitness.append(round(currentBestFitness,2))
            self.genCompleted += 1
            print(f"\nGeneration {generation}: best result = {round(currentBestFitness,2)} generation average:{round(np.mean(fitnessValues),2)}")
            print(f"Generation processing time {round(self.genTime,2)} s, average simulation processing time {round(self.genTime/self.populationSize,2)} s")
            #we wait one second for the GUI to catch up
            time.sleep(1)
           
    
        bestFitnessDF = pd.DataFrame(bestFitnessList, columns=['Result', 'Patern'])
        # sort the DataFrame by fitness values in descending order
        self.resultsdataframe = bestFitnessDF.sort_values(by='Result', ascending=False)
        return bestIndividual, bestFitness
            
