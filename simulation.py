import pandas as pd
import warnings
import numpy as np
import random
import matplotlib.pyplot as plt
import time

#account class
class Account:
    def __init__(self,data,startingBalance):
        #define dataframe to store information about trades
        self.tradeHistory = pd.DataFrame(columns=['type', 'open', 'entry price', 'sl', 'tp', 'pnl', 'float pnl %', 'max drawdown %', 'position size', 'position value', 'capital used %','balance entry','balance exit'])
        
        self.tradeHistory = self.tradeHistory.astype({
            'open': 'bool',
            'entry price': 'float64',
            'sl': 'float64',
            'tp': 'float64',
            'pnl': 'float64',
            'float pnl %': 'float64',
            'max drawdown %': 'float64',
            'position size': 'float64',
            'position value': 'float64',
            'capital used %': 'float64',
            'balance entry' : 'float64',
            'balance exit': 'float64'
        })
        self.tradeHistory.index.name ="trade id"
        #get and store market data
        self.marketData = data
        # create a dataframe for account based on data time index
        accountData = pd.DataFrame(index=self.marketData.index)
        accountData.insert(0, "Balance", startingBalance)
        accountData.insert(1, "Equity", startingBalance)
        accountData.insert(2, "Float PnL %", 0.0)
        accountData.insert(3, "Profit", 0.0)

        # ensure that the new columns are correct data type
        accountData['Balance'] = accountData['Balance'].astype('float64')
        accountData['Equity'] = accountData['Equity'].astype('float64')
        accountData['Float PnL %'] = accountData['Float PnL %'].astype('float64')
        accountData['Profit'] = accountData['Profit'].astype('float64')
        self.accountData = accountData
        #
       
        

class Simulation:

    def __init__(self,account,shortMA,longMA,rsiFilter,rsiBuy,rsiSell,rsiPeriod,riskType,riskPercent,slChecked,sl,tpChecked,tp,capitalUsage,fixedPosSize):

        self.account = account
        self.marketData = account.marketData

        self.shortMA = shortMA
        self.longMA = longMA
        self.shortMADiff = 0
        self.longMADiff = 0
        self.rsiFilter = rsiFilter
        self.rsiBuy = rsiBuy
        self.rsiSell = rsiSell
        self.rsiPeriod = rsiPeriod
        self.riskType = riskType
        self.riskPercent = riskPercent
        self.slChecked = slChecked
        self.sl = sl
        self.tpChecked = tpChecked
        self.tp = tp
        self.capitalUsage = capitalUsage
        self.fixedPosSize = fixedPosSize
        #calculate strategy data
        self.strategyData = self.calculateStrategyData()
        self.finishedPercent = 0.0
        self.done = False
        


    #calculate moving averages for the trading strategy
    def calculateStrategyData(self):
        #create a dataframe with same indexing as the getData(ticker) returns
        strategyData = pd.DataFrame(index=self.marketData.index)
        #calculate the averages and add them to dataframe
        strategyData['SMAShort'] = self.marketData['Close'].rolling(self.shortMA).mean()
        strategyData['SMALong'] = self.marketData['Close'].rolling(self.longMA).mean()
        strategyData.insert(2, "SMAShortDiff", 0)
        strategyData.insert(3,"SMALongDiff",0)
        
        #calculate the change in the moving average
        for i in range(1,len(strategyData)):
            date = self.marketData.index[i]
            prevDate = self.marketData.index[i-1]
            strategyData.loc[date,'SMALongDiff']  = abs(strategyData.loc[date,'SMALong']-strategyData.loc[prevDate,"SMALong"])
            strategyData.loc[date,'SMAShortDiff']  = abs(strategyData.loc[date,'SMAShort']-strategyData.loc[prevDate,"SMAShort"])
        

        self.shortMADiff = strategyData['SMAShortDiff'].mean()
        self.longMADiff = strategyData['SMALongDiff'].mean()

        if(self.rsiFilter):
            strategyData.insert(4,"RSI",0)
            #now lets calculate rsi indicator
            change = self.marketData["Close"].diff()
            change = change.dropna(inplace=True)
            # create two copies of the Closing price Series
            change_up = change.copy()
            change_down = change.copy()
            # 
            change_up[change_up<0] = 0
            change_down[change_down>0] = 0

            # verify that we did not make any mistakes
            change.equals(change_up+change_down)

            # calculate the rolling average of average up and average down
            avg_up = change_up.rolling(self.rsiPeriod).mean()
            avg_down = change_down.rolling(self.rsiPeriod).mean().abs()
            strategyData['RSI'] = 100 * avg_up / (avg_up + avg_down)
        return strategyData

    
    def calculate_sharpe_ratio(self, risk_free_rate=0.03):

   
        # calculate daily returns
        self.account.accountData['daily_return'] = self.account.accountData['Profit'] / self.account.accountData['Balance'].shift(1)
        # ensure the index is a datetime type
        self.account.accountData.index = pd.to_datetime(self.account.accountData.index)

        # resample the data to daily frequency
        daily_data = self.account.accountData.resample('D').agg({
            'Balance': 'last', 
            'Profit': 'sum'
        }).dropna()
        
        

         # calculate daily returns
        daily_data['daily_return'] = daily_data['Profit'] / daily_data['Balance'].shift(1)

        # frop the first row as it will have NaN for return
        daily_data = daily_data.dropna(subset=['daily_return'])

     # calculate the average daily return
        avg_daily_return = daily_data['daily_return'].mean()
        #print(avg_daily_return)

    # calculate the standard deviation of daily returns
        std_daily_return = daily_data['daily_return'].std()

        # handle case where standard deviation is zero
        if std_daily_return == 0:
            sharpeRatio = 0
            return 0 
            
        else:
            # calculate the Sharpe Ratio
            sharpeRatio = (avg_daily_return - risk_free_rate / 252) / std_daily_return
            # convert annual risk-free rate to daily risk-free rate
            daily_risk_free_rate = risk_free_rate / 252

            # calculate the Sharpe Ratio
            sharpeRatio = (avg_daily_return - daily_risk_free_rate) / std_daily_return

            # annualize the Sharpe Ratio
            #annualizedSharpeRatio = sharpeRatio * np.sqrt(252)
        
        return sharpeRatio

    #check for buy signal
    def buySignal(self,date,previousDate):
        
        #perform trading strategy, check for moving average crossover
        if(self.strategyData.loc[date,"SMAShort"] > self.strategyData.loc[date,"SMALong"] and self.strategyData.loc[previousDate,"SMAShort"] < self.strategyData.loc[previousDate,"SMALong"]):
            #check if we have on the rsi filter, if not the MA condition was met, so we return True
            if not self.rsiFilter:
                return True
                
            elif(self.strategyData.loc[date, 'RSI'] < self.rsiBuy and self.rsiFilter):
                return True
                
        return False
        
    #check for sell signal
    def sellSignal(self,date,previousDate):

        
        #perform trading strategy, check for moving average crossover
        if(self.strategyData.loc[date,"SMAShort"] < self.strategyData.loc[date,"SMALong"] and self.strategyData.loc[previousDate,"SMAShort"] > self.strategyData.loc[previousDate,"SMALong"]):
            #check if we have on the rsi filter, if not the MA condition was met, so we return True
            if not self.rsiFilter:
                return True
                
            elif(self.strategyData.loc[date, 'RSI'] > self.rsiSell and self.rsiFilter):
                return True
                
        return False

    def calculatePositionSize(self,balance):
        if(self.riskType == "Adjusted to % risk" and self.sl != 0):
            risk = self.riskPercent/100
            pnl = self.sl/100
            return (risk*balance)/pnl
        
        if(self.riskType == "Fixed capital usage in %"):
            return balance*(self.capitalUsage/100)
        
        if(self.riskType == "Fixed position size"):
            return self.fixedPosSize
        
        return -1

    #return tuple of indexes open position trades
    def getOpenPositions(self):
        openTrades = self.account.tradeHistory[self.account.tradeHistory['open']]
        return tuple(openTrades.index)
    
    #return tuple of indexes open position trades which are buy type
    def getOpenBuyPositions(self):
        openTrades = self.account.tradeHistory[(self.account.tradeHistory['open']) & (self.account.tradeHistory['type'] == "buy")]
        return tuple(openTrades.index)
    
    #return tuple of indexes open position trades which are sell type
    def getOpenSellPositions(self):
        openTrades = self.account.tradeHistory[(self.account.tradeHistory['open']) & (self.account.tradeHistory['type'] == "sell")]
        return tuple(openTrades.index)
    
    def importNewAccount(self,account):
        self.account = account

    def openPosition(self,date,posType):
        #get current account balance
        balance = self.account.accountData.loc[date,"Balance"]
        #calculate position size
        tradePosSize = self.calculatePositionSize(balance)
        slPrice = 0
        tpPrice = 0
        #check if we have enough money
        if(tradePosSize > 0 and balance - tradePosSize > 0):
            #calculate capital used
            capitalUsed = round((tradePosSize/balance)*100,2)
            #set entry price
            entryPrice = self.marketData.loc[date,"Close"]
            #check positionType
            if(posType == "buy"):        
                #check for stoploss
                if(self.slChecked):
                    #calculate stoploss price
                    slPrice = entryPrice*((100-self.sl)/100)
                if(self.tpChecked):
                    #calculate takeprofit price
                    tpPrice = entryPrice*((100+self.tp)/100)

                #add the trade in the account's trade history
                self.account.tradeHistory.loc[len(self.account.tradeHistory.index)] = ["buy",True,entryPrice,slPrice,tpPrice,0,0,0,tradePosSize,entryPrice,capitalUsed,balance,balance]
            #we are opening sell
            else:
                #check for stoploss
                if(self.slChecked):
                    #calculate stoploss price
                    slPrice = entryPrice*((100+self.sl)/100)
                if(self.tpChecked):
                    #calculate takeprofit price
                    tpPrice = entryPrice*((100-self.tp)/100)
                #add the trade in the account's trade history
                self.account.tradeHistory.loc[len(self.account.tradeHistory.index)] = ["sell",True,entryPrice,slPrice,tpPrice,0,0,0,tradePosSize,entryPrice,capitalUsed,balance,balance]
            #deduct the position size from balance
            self.account.accountData.loc[date,"Balance"] = balance - tradePosSize
            return True
        else:
            print("not enough balance to enter a position")
            return False
        
    #calculate price change in percentage and update the trade
    def updateTrade(self,index,closePrice,slHit):
        with warnings.catch_warnings():
            warnings.simplefilter(action='ignore', category=FutureWarning)
                 
            #get trade's position size
            tradePosSize = self.account.tradeHistory.loc[index,'position size']
            #get trade's entry price
            entryPrice = self.account.tradeHistory.loc[index,'entry price']
            #get trade's type
            posType = self.account.tradeHistory.loc[index,'type']
            #get the trade's entry balance
            balance = self.account.tradeHistory.loc[index,'balance entry']
        
            if (posType == "buy"):
                #calculate float pnl
                floatPnL =  (((closePrice/entryPrice) -1)*100)
                #calculate position value
                positionValue =  (round((closePrice/entryPrice)*tradePosSize,2))
                #calculate profit
                positionPnL = positionValue - tradePosSize
                #check if we are in a loss
                if(positionPnL < 0):
                    #calculate position drawdown in percentage
                    positionDD = (round((positionPnL/balance)*100,2))
                    #get position max drawdown so far
                    maxDD = self.account.tradeHistory.loc[index,'max drawdown %']
                    #if current drawdown is higher than trade's max dd so far
                    if(positionDD > maxDD and not slHit):
                        #update max drawdown
                        self.account.tradeHistory.loc[index,'max drawdown %'] = positionDD
                    #if we are calling this function when stoploss was hit, we adjust the max drawdown so it corresponds with the sl
                    #we have only close price available, so we will assume that the position will be closed at the sl price
                    elif(slHit):
                        self.account.tradeHistory.loc[index,'max drawdown %'] = positionDD

            #its a sell adjust calculation
            else:
                #calculate float pnl
                floatPnL = ((entryPrice/closePrice) -1)*100
                #calculate position value
                positionValue =  round((entryPrice/closePrice)*tradePosSize,2)
                #calculate profit
                positionPnL = positionValue - tradePosSize
                #check if we are in a loss
                if(positionPnL < 0):
                    #calculate position drawdown in percentage
                    positionDD = round((positionPnL/balance)*100,2)
                    #get position max drawdown so far
                    maxDD = self.account.tradeHistory.loc[index,'max drawdown %']
                    #if current drawdown is higher than trade's max dd so far
                    if(positionDD > maxDD):
                        #update max drawdown
                        self.account.tradeHistory.loc[index,'max drawdown %'] = positionDD
                    #if we are calling this function when stoploss was hit, we adjust the max drawdown so it corresponds with the sl
                    #we have only close price available, so we will assume that the position will be closed at the sl price
                    elif(slHit):
                        self.account.tradeHistory.loc[index,'max drawdown %'] = positionDD

            #update the values
            self.account.tradeHistory.loc[index,'float pnl %'] = round(floatPnL,2)
            self.account.tradeHistory.loc[index,'position value'] = round(positionValue,2)
            self.account.tradeHistory.loc[index,'pnl'] = round(positionPnL,2)

    def updateAccount(self,date,previousDate):
        #get account's balance
        balance = self.account.accountData.loc[date,'Balance']
        startingBalance = self.account.accountData.loc[self.account.accountData.index[0],'Balance']
        #get tuple of indexes of open positions
        totalPositionValue = 0
        totalFloatPnL = 0
        totalPnL = 0
        #loop through open positions and sum up pnl
        for index in self.getOpenPositions():
            totalPositionValue += self.account.tradeHistory.loc[index,'position value']
            totalFloatPnL += self.account.tradeHistory.loc[index,'float pnl %']
            totalPnL += self.account.tradeHistory.loc[index,'pnl']
        #update values
        self.account.accountData.loc[date,'Profit'] = totalPnL
        self.account.accountData.loc[date,'Float PnL %'] = totalFloatPnL
        self.account.accountData.loc[date,'Balance'] = self.account.accountData.loc[previousDate,'Balance']
        self.account.accountData.loc[date,'Equity'] = self.account.accountData.loc[date,'Balance'] + totalPositionValue

            
    def closePosition(self,date,index):
        #get trade's pnl
        pnl = self.account.tradeHistory.loc[index,'pnl']
        #update balance
        self.account.accountData.loc[date,'Balance'] = self.account.tradeHistory.loc[index,"balance entry"] + pnl
        #change trade's status to closed
        self.account.tradeHistory.loc[index,'open'] = False
        #update the position exit balance
        self.account.tradeHistory.loc[index,'balance exit'] = self.account.accountData.loc[date,"Balance"] 
        #print(f"Closing long position:\nBuying price: {entryPrice}\nSelling price: {closePrice}\nProfit: {positionPnL}")


    def monitorSL(self,price,date):
        #loop through open positions
        for index in self.getOpenPositions():
            #print("date",date)
            #get position sl
            sl = self.account.tradeHistory.loc[index,'sl']
            #check position type
            posType = self.account.tradeHistory.loc[index,'type']
            if(posType == "buy" and price <= sl):
                #since we have only close, low and high price in our dataframe (not curren bid or ask) we will assume that we will close the position at sl price
                self.updateTrade(index,sl,True)
                #close position
                self.closePosition(date,index)

            elif(posType == "sell" and price >= sl):
                #since we have only close, low and high price in our dataframe (not curren bid or ask) we will assume that we will close the position at sl price
                self.updateTrade(index,sl,True)
                #close position
                self.closePosition(date,index)

                

    def monitorTP(self,price,date):
        #loop through open positions
        for index in self.getOpenPositions():
            #get position sl
            tp = self.account.tradeHistory.loc[index,'tp']
            #check position type
            posType = self.account.tradeHistory.loc[index,'type']
            #check if tp hit price
            if(posType == "buy" and price >= tp):
                
                #since we have only close, low and high price in our dataframe (not curren bid or ask) we will assume that we will close the position at sl price
                self.updateTrade(index,tp,True)
                #close position
                self.closePosition(date,index)

            elif(posType == "sell" and price <= tp):
                
                #since we have only close, low and high price in our dataframe (not curren bid or ask) we will assume that we will close the position at sl price
                self.updateTrade(index,tp,True)
                #close position
                self.closePosition(date,index)
    
    
    def runSimulation(self):
    
        #get number of rows in the market dataframe
        datalen = len(self.marketData.index)
        
    
        self.account.accountData = self.account.accountData.loc[self.strategyData.index[0]:self.strategyData.index[-1]]

        
        #loop through each closing price in the dataframe
        for i in range(5,datalen):
            #set the index 
            date = self.marketData.index[i]
            #print(f"{i}/{datalen}")
            previousDate = self.marketData.index[i - 1]
            #get candle close price
            closePrice = self.marketData.loc[date,'Close']
            #print(closePrice)
            #update account
            self.updateAccount(date,previousDate)
            #check for trading signals

            if(self.buySignal(date,previousDate)):
                #close all sell positions
                for index in self.getOpenSellPositions():
                    self.closePosition(date,index)
                
                #open a buy position
                self.openPosition(date,"buy")
                

            if(self.sellSignal(date,previousDate)):
                #close all buy positions
                for index in self.getOpenBuyPositions():
                    self.closePosition(date,index)
                    
                #open a sell position
                self.openPosition(date,"sell")
    

            #check for stoploss
            if(self.slChecked):
                self.monitorSL(closePrice,date)
                

            #check for takeprofit
            if(self.tpChecked):
                self.monitorTP(closePrice,date)
                

            #update trades
            for index in self.getOpenPositions():
                self.updateTrade(index,closePrice,False)

            self.finishedPercent = round((i/datalen),1)
            #print(self.finishedPercent)

             
        #loop has finished,close open positions
        for index in self.getOpenPositions():
            self.closePosition(date,index)
        
        #calculate profit factor for strategy, if there are not enough trades, we set it to 0
        if(len(self.account.tradeHistory) > 0.01*datalen):
            totalProfit = self.account.tradeHistory.loc[self.account.tradeHistory['pnl'] > 0, 'pnl'].sum()
            totalLoss = self.account.tradeHistory.loc[self.account.tradeHistory['pnl'] < 0, 'pnl'].sum()
            profitFactor = round(totalProfit / -totalLoss,2) if totalLoss != 0 else float(0)
        else:
            profitFactor = 0

        #get final profit
        profit = self.account.accountData.loc[self.marketData.index[datalen-1],'Balance']- self.account.accountData.loc[self.marketData.index[0],'Balance'] 
        
        #calculate sharpe ratio
        sharpeRatio = self.calculate_sharpe_ratio()

        sharpeAdjusted = round(sharpeRatio*profit,2)
        
        #return a tuple of strategy results and inputs
        self.done = True
        return [profitFactor,profit,sharpeRatio,sharpeAdjusted,self.shortMA,self.longMA,self.riskType,self.riskPercent,self.slChecked,self.sl,self.tpChecked,self.tp]


    def plotResults(self):
        fig, axs = plt.subplots(3, 1, figsize=(16, 24))

        # plot equity
        self.account.accountData[['Equity','Balance']].plot(ax=axs[0], label="Equity and Balance")
        axs[0].set_title('Equity over time', pad=20)
        axs[0].legend()
        axs[0].set_xlabel('')  # remove x-axis label

        # plot Float PnL 
        self.account.accountData[['Profit']].plot(ax=axs[1], label="Float PnL")
        axs[1].fill_between(self.account.accountData.index, self.account.accountData['Profit'], where=(self.account.accountData['Profit'] < 0), color='red', alpha=0.5) 
        axs[1].fill_between(self.account.accountData.index, self.account.accountData['Profit'], where=(self.account.accountData['Profit'] > 0), color='green', alpha=0.5) 
        axs[1].set_title('Floating profit over time', pad=20)
        axs[1].legend()
        axs[1].set_xlabel('')  # remove x-axis label

        # plot capital used %
        self.account.tradeHistory[['capital used %']].plot(ax=axs[2], label="Capital Used %")
        axs[2].set_title('Capital used percentage per trade', pad=20)
        axs[2].legend()
        axs[2].set_xlabel('')  # remove x-axis label

        # adjust layout to prevent overlap
        plt.subplots_adjust(hspace=1.3)
        plt.show()

class GeneticOptimizer:
    def __init__(self, startingBalance,riskType, riskPercent,capitalUsage,fixedPosSize,populationSize, mutationRate,mixingRate, generations, data,
                 shortMALowerBound,shortMAUpperBound,longMALowerBound,longMAUpperBound,
                 slLowerBound,slUpperBound,tpLowerBound,tpUpperBound,fitnessType):
        
        #info about simulation and the capital
        self.capitalUsage = capitalUsage
        self.fixedPosSize = fixedPosSize
        self.riskType = riskType
        self.riskPercent = riskPercent
        self.data = data
        self.startingBalance = startingBalance
        #info about the optimalization parameters
        self.populationSize = populationSize
        self.mutationRate = mutationRate
        self.mixingRate = mixingRate
        self.generations = generations
        self.lastFitnessValues = []
        #
        self.shortMALowerBound = shortMALowerBound
        self.shortMAUpperBound = shortMAUpperBound
        self.longMALowerBound = longMALowerBound
        self.longMAUpperBound = longMAUpperBound
        self.slLowerBound = slLowerBound
        self.slUpperBound = slUpperBound
        self.tpLowerBound = tpLowerBound
        self.tpUpperBound = tpUpperBound
        self.fitnessType = fitnessType
        self.genCompleted = 0
        self.averageGen = []
        self.topFitness = []
        self.resultsdataframe = None
        

    def initializePopulation(self):
        population = []
        #initialize population
        for _ in range(self.populationSize):
            #
            shortMA = random.randint(self.shortMALowerBound, self.shortMAUpperBound - 1)
            #the long MA has to be always at least 3 higher than the short MA
            longMA = random.randint(shortMA + 3, self.longMAUpperBound)
            #
            slChecked = random.choice([True, False])
            #generate value to sl only if sl is checked, otherwise set to 0
            if(slChecked):
                sl = random.randint(self.slLowerBound,self.slUpperBound)
            else:
                sl = 0
            tpChecked = random.choice([True, False])
            #same for tp, generate random value if tp is checked
            if(tpChecked):
                tp = random.randint(self.tpLowerBound, self.tpUpperBound)
            else:
                tp = 0
            
           # rsiFilter = random.choice([True, False])
            #if(rsiFilter):
             #   rsiBuy = random.randint(0,49)
              #  rsiSell = random.randint(51,100)
               # rsiPeriod = random.randint(6,25)
           # else:
            #    rsiBuy = 0
             #   rsiSell = 0
              #  rsiPeriod = 0
    
            #one individual has genetics:
            individual = {
                'shortMA': shortMA,
                'longMA': longMA,
                'slChecked': slChecked,
                'sl': sl,
                'tpChecked': tpChecked,
                'tp': tp
            }
            #add the population to the population tuple
            population.append(individual)
        return population

    def fitness(self, individual):
        demoAccount = Account(self.data, self.startingBalance)
        #create a simulation object with the input
        simulation = Simulation(demoAccount, 
                                individual['shortMA'],individual['longMA'],
                                False,0,0,1,
                                self.riskType,self.riskPercent,individual['slChecked'],individual['sl'],
                                individual['tpChecked'],individual['tp'],self.capitalUsage,self.fixedPosSize)
        #lets run the simulation with the individual
        result = simulation.runSimulation()
        #return the fitness result
        if(self.fitnessType == "Profit factor"):
            print(f"{individual} is profit factor: {result[0]}")
            return result[0]
        if(self.fitnessType == "Net profit"):
            #print(f"{individual} is profit: {result[1]}")
            return result[1]
        if(self.fitnessType == "Sharpe ratio"):
            return result[2]
        if(self.fitnessType == "Adjusted sharpe ratio"):
            return result[3]
        return -1

    def selectParents(self, population, fitnessValues):
       
        #if the fitness parameter is profit, we have to normalize the number so it is between 0 and 1, 0 meaning the worst profit in the generation and 1 the best in the generation
        min_fitness = np.min(fitnessValues)
        max_fitness = np.max(fitnessValues)
        #if the min_fitness is negative, we shift the value so the worst profit is still positive
        if(min_fitness < 0):
            min_fitness = abs(min_fitness)
            max_fitness = abs(min_fitness) + max_fitness
        
        
        # if all fitness values are equal, assign equal weights
        if max_fitness == min_fitness:
            normalized_fitness = np.ones_like(fitnessValues)

        else:
            # normalize to range [0, 1]
            if max_fitness != 0:
                normalized_fitness = (fitnessValues + min_fitness) / (max_fitness)
            else:
                #if maximum fitness is 0, the parents will be random 
                return random.choices(population,k=2)
                
        # aelect two parents based on their fitness values
        #print(normalized_fitness)

        
        parents = random.choices(population, weights=normalized_fitness, k=2)
        return parents


    # random crossover
    def arithmetic_crossover(self, parent1, parent2):
        child = {}
        for key in parent1:
            if isinstance(parent1[key], (int, float)):
                # random crossover
                if(parent1[key]> parent2[key]):
                    child[key] = int(random.uniform(parent2[key],parent1[key])) 
                else: 
                    child[key] = int(random.uniform(parent1[key],parent2[key]))
            if isinstance(parent1[key], bool):
                # 50/50 chance crossover for boolean values
                child[key] = random.choice([parent1[key], parent2[key]])
            
            #just to be 100% sure that new key value will stay inside bounds
            if(key == "shortMA" and child[key] < self.shortMALowerBound):
                child[key] = self.shortMALowerBound
            if(key == "shortMA" and child[key] > self.shortMAUpperBound):
                child[key] = self.shortMAUpperBound
            if(key == "sl" and child[key] > self.slUpperBound):
                child[key] = self.slUpperBound
            if(key == "sl" and child[key] < self.slLowerBound):
                child[key] = self.slLowerBound
            if(key == "tp" and child[key] > self.tpUpperBound):
                child[key] = self.tpUpperBound
            if(key == "tp" and child[key] > self.tpLowerBound):
                child[key] = self.tpLowerBound
            #print(f" {key}: {child[key]}")
        return child


        
    def mutate(self, individual):
        #we apply the mutation rate to each variable
        if (random.random() < self.mutationRate):
            individual['shortMA'] = random.randint(self.shortMALowerBound, self.shortMAUpperBound - 1)
        if (random.random() < self.mutationRate):
            individual['longMA'] = random.randint(int(individual['shortMA'] + 3), int(self.longMAUpperBound))
        if (random.random() < self.mutationRate):
            individual['slChecked'] = random.choice([True, False])
        if (random.random() < self.mutationRate and individual['slChecked']):
            individual['sl'] = random.randint(self.slLowerBound, self.slUpperBound)
        if (random.random() < self.mutationRate):
            individual['tpChecked'] = random.choice([True, False])
        if (random.random() < self.mutationRate and individual['tpChecked']):
            individual['tp'] = random.randint(self.tpLowerBound, self.tpUpperBound)
        if (random.random() < self.mutationRate and not individual['rsiFilter']):
            individual['rsiFilter'] = True
        if (random.random() < self.mutationRate and individual['rsiFilter']):
            individual['rsiBuy'] = random.randint(0, 49)
        if (random.random() < self.mutationRate and individual['rsiFilter']):
            individual['rsiSell'] = random.randint(51, 100)
        if (random.random() < self.mutationRate and individual['rsiFilter']):
            individual['rsiPeriod'] = random.randint(6, 25)
        

    def optimize(self):
        population = self.initializePopulation()
        bestIndividual = None
        bestFitness = -float('inf')
        seen_individuals = set()  
        bestFitnessList = []
      
      
        #main loop to go through generations
        for generation in range(self.generations):
            
            fitnessValues = []
            #run the simulation for each individual in population
            for individual in population:

                fitnessValues.append(self.fitness(individual))
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
                
            # get the top 10 fitness values and corresponding individuals in the current generation
            top10Indices = np.argsort(fitnessValues)[-10:]  
            for index in top10Indices:
                bestFitnessList.append((fitnessValues[index], population[index]['shortMA'],population[index]['longMA'],population[index]["slChecked"],population[index]["sl"],population[index]["tpChecked"],population[index]["tp"]))
            
        
            #create a new population
            newPopulation = []
            while len(newPopulation) < self.populationSize:
                parent1, parent2 = self.selectParents(population, fitnessValues)
                
                # create a child
                child = self.arithmetic_crossover(parent1, parent2)

                #mutate a child
                self.mutate(child)
                
                # convert child to a tuple
                child_tuple = tuple(sorted(child.items()))
                
                #check if child is unique       
                if child_tuple not in seen_individuals:
                    newPopulation.append(child)
                    seen_individuals.add(child_tuple)
                         
                    #parent1_tuple = tuple(sorted(parent1.items()))
                    #parent2_tuple = tuple(sorted(parent2.items()))

                   # print("Parents")
                   # print(parent1_tuple)
                   ## print(parent2_tuple)
                    #print("kid")             
                   # print(f"{child_tuple}\n")

                #since the crossover is designed to converge on specific values, we can force the algo to continue searching for new values by creating a new random kid, this way the algo will "reset" iself when it converges
                else:
                  
                    shortma = random.randint(self.shortMALowerBound, self.shortMAUpperBound - 1)
                    slChecked = random.choice([True, False])

                    if(slChecked):
                        sl = random.randint(self.slLowerBound,self.slUpperBound)
                    else:
                        sl = 0

                    tpChecked = slChecked = random.choice([True, False])

                    if(tpChecked):
                        tp = random.randint(self.slLowerBound,self.slUpperBound)
                    else:
                        tp = 0

                    newChild = {
                            'shortMA': shortma,
                            'longMA': random.randint(shortma + 3, self.longMAUpperBound),
                            'slChecked': slChecked,
                            'sl': sl,
                            'tpChecked': tpChecked,
                            'tp': tp }
                    
                    #print("new child",newChild)
                    newPopulation.append(newChild)

                    
            population = newPopulation
            self.averageGen.append(round(np.mean(fitnessValues),2))
            self.topFitness.append(round(currentBestFitness,2))
            self.genCompleted += 1
            print(f"Generation {generation}: best result = {round(currentBestFitness,2)} generation average:{round(np.mean(fitnessValues),2)}")
            #we wait one second for the GUI to catch up
            time.sleep(1)
           
    
        bestFitnessDF = pd.DataFrame(bestFitnessList, columns=['Result', 'ShortMA','LongMA',"SL on","SL","TP on","TP"])
        # sort the DataFrame by fitness values in descending order
        self.resultsdataframe = bestFitnessDF.sort_values(by='Result', ascending=False)
       
        return bestIndividual, bestFitness


