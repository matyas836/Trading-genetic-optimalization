import tkinter
import tkinter.messagebox
import customtkinter
import threading
import time
import yfinance as yf

from tkcalendar import DateEntry
from simulation import GeneticOptimizer
from datetime import datetime, timedelta
from tkinter import filedialog

class optimizeWindow:
    def __init__(self):
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")
        
        # create a new top-level window 
        self.window = customtkinter.CTkToplevel()
        self.window.title("Strategy Optimizer")
        self.window.geometry("1460x650")
        self.window.attributes('-topmost', True)
        self.window.resizable(False,False)

        #
        self.data = None
        self.genCompleted = 0
    
        
        # define variables
        tickerVar = tkinter.StringVar(value="BTC-USD")
        shortMALowerVar = tkinter.IntVar(value=9)
        shortMAUpperVar = tkinter.IntVar(value=80)
        longMALowerVar = tkinter.IntVar(value=12)
        longMAUpperVar = tkinter.IntVar(value=250)
        startBalanceVar = tkinter.IntVar(value=10000)
        fixedSizeVar = tkinter.IntVar(value=1000)
        fixedCapitalUseVar = tkinter.IntVar(value=70)
        fixedPercentRiskVar = tkinter.IntVar(value=2)
        slCheckedVar = tkinter.StringVar()
        slLowerVar = tkinter.IntVar(value=5)
        slUpperVar = tkinter.IntVar(value=10)
        tpCheckedVar = tkinter.StringVar()
        tpLowerVar = tkinter.IntVar(value=5)
        tpUpperVar = tkinter.IntVar(value=10)
        timeframe_var = tkinter.StringVar(value="1d")
        pos_var = tkinter.StringVar(value="Fixed capital usage in %")
        populationSizeVar = tkinter.IntVar(value = 20)
        mutationRateVar = tkinter.IntVar(value = 10)
        mixingRateVar = tkinter.IntVar(value= 50)
        generationVar = tkinter.IntVar(value= 5)
        fitnessTypeVar = tkinter.StringVar(value="Adjusted sharpe ratio")


        def convert_date(date_entry):
            date_format = "%Y-%m-%d"
            date_obj = datetime.strptime(date_entry, date_format).date()
            return date_obj

        def download_data(ticker, start_date, end_date, interval):
            self.data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
            if self.data.empty:
                self.window.destroy()
                tkinter.messagebox.showerror(title="Error downloading data", message="Error downloading data, check ticker or try different time range of data")
                

        def exportExcel(optimizer):
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                                             title="Save Excel File")

           # print(f"Selected file path: {file_path}")  

            if file_path:
                # export the sorted DataFrame to the selected Excel file
                optimizer.resultsdataframe.to_excel(file_path, index=False)
                print(f"File saved successfully at: {file_path}")  
            else:
                print("Save operation cancelled.")  
                
        #start button callback
        def button_callback():
            #get the values
            inputValid = True
            ticker = tickerVar.get()
            shortMALower = int(shortMALowerVar.get())
            shortMAUpper = int(shortMAUpperVar.get())
            longMALower = int(longMALowerVar.get())
            longMAUpper = int(longMAUpperVar.get())
            startBalance = int(startBalanceVar.get())
            fixedPosSize = int(fixedSizeVar.get())
            fixedCapitalUsage = int(fixedCapitalUseVar.get())
            fixedPercentRisk = int(fixedPercentRiskVar.get())
            slChecked = slCheckedVar.get()
            slLower = int(slLowerVar.get())
            slUpper = int(slUpperVar.get())
            tpChecked = tpCheckedVar.get()
            tpLower = int(tpLowerVar.get())
            tpUpper = int(tpUpperVar.get())
            from_date_value = from_date.get()
            to_date_value = to_date.get()
            posSizeType = pos_var.get()
            timeframe_value = timeframe_var.get()
            populationSize = int(populationSizeVar.get())
            mutationRate = int(mutationRateVar.get())
            mixingRate = int(mixingRateVar.get())
            generations = int(generationVar.get())
            fitnessType = fitnessTypeVar.get()

            slChecked = True if slCheckedVar.get() == "1" else False
            tpChecked = True if tpCheckedVar.get() == "1" else False

            #input check
            if shortMALower < 3:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong period", message="Period of short moving average lower bound must be higher than 3")

            if shortMAUpper < 6:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong period", message="Period of short moving average upper bound must be higher than 6")


            if longMALower < 6:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong period", message="Period of long moving average lower bound must be higher than 6")

            if longMAUpper < 9:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong period", message="Period of long moving average upper bound must be higher than 9")
            
 
            if shortMALower >= longMALower or shortMAUpper >= longMAUpper:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong period", message="Period of long moving average must be greater than period of short moving average")

            if startBalance < 100:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong starting balance", message="Starting balance must be at least 100")

            if fixedPosSize > startBalance and posSizeType == "Fixed position size":
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed position size must be less than starting balance")

            if fixedPosSize <= 0 and posSizeType == "Fixed position size":
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed position size must be greater than zero")

            if fixedCapitalUsage <= 0 and posSizeType == "Fixed capital usage in %":
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed capital usage must be greater than zero")
            
            if fixedCapitalUsage > 95 and posSizeType == "Fixed capital usage in %":
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed capital usage must be at maximum 95 %")

            if posSizeType == "Adjusted to % risk" and not slChecked:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Turn on stoploss in order to use adjusted to % risk position sizing")

            if fixedPercentRisk <= 0 and posSizeType == "Adjusted to % risk":
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Risk % per trade must be greater than 0")

            if fixedPercentRisk > 100 and posSizeType == "Adjusted to % risk":
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Risk % per trade must be at maximum 100 %")

            if tpChecked and (tpLower <= 0 or tpUpper <= 0):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong takeprofit value", message="Take profit must be greater than 0%")
            
            if tpLower > tpUpper and tpChecked:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong takeprofit value", message="Upper bound for takeprofit must be higher than lower bound")


            if slChecked and (slLower <= 0 or slUpper <= 0):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong stoploss value", message="Stoploss must be greater than 0%")

            if slLower > slUpper:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong stoploss value", message="Upper bound for stoploss must be higher than lower bound")

            #convert dates so we can compare them
            from_dateConverted = convert_date(from_date_value)
            to_dateConverted = convert_date(to_date_value)
            current_date = datetime.now().date() - timedelta(days=1)

            if from_dateConverted >= to_dateConverted:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong date", message="From date must be before the to date")

            if to_dateConverted > current_date:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong date", message="The date must be at least one day before the current day")

            difference = abs((to_dateConverted - from_dateConverted).days)

            if difference > 729:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong date", message="The difference between two dates must be less than 730 days")
            
            if populationSize < 10:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong population size", message="Population size must be at least 10")
            
            if mutationRate < 0:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong mutation rate", message="Mutation rate can't be negative")
            
            if mutationRate > 100:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong mutation rate", message="Mutation rate can be at maximum 100 %")
            
            if mixingRate < 10:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong mixing rate", message="Mixing rate must be at least 10 %")
            
            if mixingRate > 100:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong mixing rate", message="Mixing rate can't be more than 100 %")
            
            if generations < 3:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong generations number", message="The least possible number of generations is 3")

           
            if inputValid:
                #if we passed the input we create progress bars
                self.progress_bar = customtkinter.CTkProgressBar(self.window, mode='indeterminate', height=30, width=250)
                self.progress_bar.grid(row=3, column=0,columnspan=3, padx=20, pady=10, sticky="sew")
                self.progress_bar.configure(progress_color="cyan")
                self.progress_bar.set(0)
                self.progress_bar.start()
                
                self.progress_bar_download = customtkinter.CTkProgressBar(self.window, mode='determinate', height=20, width=250)
                self.progress_bar_download.grid(row=2,column = 1,columnspan=2, padx=20, pady=120, sticky="new")
                self.progress_bar_download.configure(progress_color="lawngreen")
                self.progress_bar_download.set(0)
                self.progress_bar_download.start()

                download_data(ticker,from_date_value,to_date_value,timeframe_value)

                self.progress_bar_download.stop()
                self.progress_bar_download.set(1)

                if(not self.data.empty):
                    #if succesful download of data
                    progressLabel =  customtkinter.CTkLabel(self.window,text=f"Number of simulations the optimizer is going to perform: {generations*populationSize}",font=("Helvetica", 14, "normal"))
                    progressLabel.grid(row=2, column=1,columnspan=2, padx=150, pady=20, sticky="nw")

                    label2 = customtkinter.CTkLabel(self.window,text=f"Number of trading candles that are going to be analyzed: {generations*populationSize*len(self.data)}",font=("Helvetica", 14, "normal"))
                    label2.grid(row=2,column =1,columnspan=2,padx= 150,pady= 60,sticky="nw")

                    mutationRate = int(mutationRate/100)
                    mixingRate = int(mixingRate/100)
                    #create the optimalization object
                    optimizer = GeneticOptimizer(startBalance,posSizeType,fixedPercentRisk,fixedCapitalUsage,fixedPosSize,populationSize, mutationRate,mixingRate, generations,
                                                  self.data,shortMALower,shortMAUpper,longMALower,longMAUpper,slLower,slUpper,tpLower,tpLower,fitnessType)
                    #create a thread for the optimalization
                    optimizeThread = threading.Thread(target=optimizer.optimize)
                    #progress bar
                    self.progress_bar = customtkinter.CTkProgressBar(self.window, mode='determinate', height=30, width=250)
                    self.progress_bar.grid(row=3, column=0,columnspan=3, padx=20, pady=10, sticky="sew")
                    self.progress_bar.configure(progress_color="cyan")
                    self.progress_bar.set(0)
                    #label that it's running
                    labelgen = customtkinter.CTkLabel(self.window,text=f"Generations completed: {self.genCompleted}/{generations}",font=("Helvetica", 14, "normal"))
                    labelgen.grid(row=2,column =3,columnspan=2,padx= 30,pady= 60,sticky="nw")

                    labelgen2 = customtkinter.CTkLabel(self.window,text=f"Maximum {fitnessType}: 0",font=("Helvetica", 14, "normal"))
                    labelgen2.grid(row=2,column =3,columnspan=2,padx= 30,pady= 80,sticky="nw")

                    labelgen3 = customtkinter.CTkLabel(self.window,text=f"Generation: 0 {fitnessType} average: 0",font=("Helvetica", 14, "normal"))
                    labelgen3.grid(row=2,column =3,columnspan=2,padx= 30,pady= 100,sticky="nw")

                    labelgen4 = customtkinter.CTkLabel(self.window,text=f"Optimalization running",font=("Helvetica", 18, "normal"))
                    labelgen4.grid(row=2,column =1,columnspan=2,padx= 160,pady= 30,sticky="sw")

                    #start the optimalization
                    optimizeThread.start()
                    while(optimizeThread.is_alive()):
                        #check each half a second if we have finished a generation
                        time.sleep(0.5)
                        if(len(optimizer.averageGen) > self.genCompleted):
                            #update labels
                            self.genCompleted = len(optimizer.averageGen)
                            labelgen.configure(text=f"Generations completed: {self.genCompleted}/{generations}")
                            labelgen2.configure(text=f"Maximum {fitnessType}: {optimizer.topFitness[len(optimizer.topFitness)-1]}")
                            labelgen3.configure(text=f"Generation: {self.genCompleted} -> {fitnessType} average: {optimizer.averageGen[len(optimizer.averageGen)-1]}")
                            progressPercent = round(self.genCompleted/generations,2)
                            #print(f"{progressPercent*100}%\n")
                            self.progress_bar.set(progressPercent)
                            
                    self.window.withdraw()
                    exportExcel(optimizer)
                self.window.destroy()

        # configure rows and columns
        self.window.grid_rowconfigure(6, weight=1)
        self.window.grid_columnconfigure(6, weight=1)
        
        # create frames
        frame1 = customtkinter.CTkFrame(self.window)
        frame1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", rowspan=2)

        frame2 = customtkinter.CTkFrame(self.window)
        frame2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew", rowspan=2)

        frame3 = customtkinter.CTkFrame(self.window)
        frame3.grid(row=0, column=2, padx=10, pady=10, sticky="nsew", rowspan=2)

        frame4 = customtkinter.CTkFrame(self.window)
        frame4.grid(row=0, column=3, padx=10, pady=10, sticky="new", rowspan=2)

        # create frame5
        frame5 = customtkinter.CTkFrame(self.window)
        frame5.grid(row=2, column=0, padx=10, pady=10, sticky="w", columnspan=4)


        # add headings to frames
        heading1 = customtkinter.CTkLabel(frame1, text="Strategy parameters", font=("Helvetica", 16, "bold"))
        heading1.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")

        heading2 = customtkinter.CTkLabel(frame2, text="Account's capital", font=("Helvetica", 16, "bold"))
        heading2.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")

        heading3 = customtkinter.CTkLabel(frame3, text="Risk management", font=("Helvetica", 16, "bold"))
        heading3.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")

        heading4 = customtkinter.CTkLabel(frame4, text="Trading range", font=("Helvetica", 16, "bold"))
        heading4.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")\
        
        heading5 = customtkinter.CTkLabel(frame5,text="Optimalization parameters", font=("Helvetica", 16, "bold"))
        heading5.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")\
        
        # add widgets to frame1 (Trading Range)
        
        label_shortMALower = customtkinter.CTkLabel(frame1, text="Short MA Lower Bound:")
        label_shortMALower.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_shortMALower = customtkinter.CTkEntry(frame1, textvariable=shortMALowerVar)
        entry_shortMALower.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        label_shortMAUpper = customtkinter.CTkLabel(frame1, text="Short MA Upper Bound:")
        label_shortMAUpper.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_shortMAUpper = customtkinter.CTkEntry(frame1, textvariable=shortMAUpperVar)
        entry_shortMAUpper.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        label_longMALower = customtkinter.CTkLabel(frame1, text="Long MA Lower Bound:")
        label_longMALower.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entry_longMALower = customtkinter.CTkEntry(frame1, textvariable=longMALowerVar)
        entry_longMALower.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        label_longMAUpper = customtkinter.CTkLabel(frame1, text="Long MA Upper Bound:")
        label_longMAUpper.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        entry_longMAUpper = customtkinter.CTkEntry(frame1, textvariable=longMAUpperVar)
        entry_longMAUpper.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        # add widgets to frame2 (Risk Management)
        label_timeframe = customtkinter.CTkLabel(frame2, text="Position sizing type:")
        label_timeframe.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        posType_options = ["Fixed position size","Fixed capital usage in %","Adjusted to % risk"]
        timeframe_dropdown = customtkinter.CTkOptionMenu(frame2, values=posType_options, variable=pos_var)
        timeframe_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        label_startBalance = customtkinter.CTkLabel(frame2, text="Starting Balance:")
        label_startBalance.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_startBalance = customtkinter.CTkEntry(frame2, textvariable=startBalanceVar)
        entry_startBalance.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        label_fixedSize = customtkinter.CTkLabel(frame2, text="Fixed Position Size:")
        label_fixedSize.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_fixedSize = customtkinter.CTkEntry(frame2, textvariable=fixedSizeVar)
        entry_fixedSize.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        label_fixedCapitalUse = customtkinter.CTkLabel(frame2, text="Fixed Capital Usage (%):")
        label_fixedCapitalUse.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entry_fixedCapitalUse = customtkinter.CTkEntry(frame2, textvariable=fixedCapitalUseVar)
        entry_fixedCapitalUse.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        label_fixedPercentRisk = customtkinter.CTkLabel(frame2, text="Risk % Per Trade:")
        label_fixedPercentRisk.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        entry_fixedPercentRisk = customtkinter.CTkEntry(frame2, textvariable=fixedPercentRiskVar)
        entry_fixedPercentRisk.grid(row=5, column=1, padx=10, pady=5, sticky="ew")


        # add widgets to frame3 (Stoploss and Takeprofit)
        label_slChecked = customtkinter.CTkCheckBox(frame3, text="Enable Stoploss", variable=slCheckedVar, onvalue="1", offvalue="0")
        label_slChecked.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        label_slLower = customtkinter.CTkLabel(frame3, text="Stoploss Lower Bound (%):")
        label_slLower.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entry_slLower = customtkinter.CTkEntry(frame3, textvariable=slLowerVar)
        entry_slLower.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        label_slUpper = customtkinter.CTkLabel(frame3, text="Stoploss Upper Bound (%):")
        label_slUpper.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_slUpper = customtkinter.CTkEntry(frame3, textvariable=slUpperVar)
        entry_slUpper.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        label_tpChecked = customtkinter.CTkCheckBox(frame3, text="Enable Takeprofit", variable=tpCheckedVar, onvalue="1", offvalue="0")
        label_tpChecked.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        label_tpLower = customtkinter.CTkLabel(frame3, text="Takeprofit Lower Bound (%):")
        label_tpLower.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        entry_tpLower = customtkinter.CTkEntry(frame3, textvariable=tpLowerVar)
        entry_tpLower.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        label_tpUpper = customtkinter.CTkLabel(frame3, text="Takeprofit Upper Bound (%):")
        label_tpUpper.grid(row=6, column=0, padx=10, pady=5, sticky="w")
        entry_tpUpper = customtkinter.CTkEntry(frame3, textvariable=tpUpperVar)
        entry_tpUpper.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

        # add widgets to frame4 (Dates and Timeframe)
        label_ticker = customtkinter.CTkLabel(frame4, text="Ticker:")
        label_ticker.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        entry_ticker = customtkinter.CTkEntry(frame4, textvariable=tickerVar)
        entry_ticker.grid(row=1, column=1, padx=10, pady=5, sticky="ew")


        label_from_date = customtkinter.CTkLabel(frame4, text="From Date:")
        label_from_date.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        from_date = DateEntry(frame4, date_pattern='y-mm-dd')
        from_date.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        from_date.set_date(datetime.now().date() - timedelta(days=364))

        label_to_date = customtkinter.CTkLabel(frame4, text="To Date:")
        label_to_date.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        to_date = DateEntry(frame4, date_pattern='y-mm-dd', maxdate=datetime.now().date() - timedelta(days=1))
        to_date.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        label_timeframe = customtkinter.CTkLabel(frame4, text="Timeframe:")
        label_timeframe.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        timeframe_options = ["5m", "1h", "1d"]
        timeframe_dropdown = customtkinter.CTkOptionMenu(frame4, values=timeframe_options, variable=timeframe_var)
        timeframe_dropdown.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # add widgets to frame5 
        labelPopulation = customtkinter.CTkLabel(frame5, text="Population size:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        entryPopulation = customtkinter.CTkEntry(frame5, textvariable=populationSizeVar).grid(row=1, column=1, padx=10, pady=5)

        labelMutationRate = customtkinter.CTkLabel(frame5, text="Mutation rate:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        entryMutationRate = customtkinter.CTkEntry(frame5, textvariable=mutationRateVar).grid(row=2, column=1, padx=10, pady=5)

        labelGenerations = customtkinter.CTkLabel(frame5, text="Generations:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entryGenerations = customtkinter.CTkEntry(frame5, textvariable=generationVar).grid(row=4, column=1, padx=10, pady=5)

        labelFitness = customtkinter.CTkLabel(frame5, text="Optimize criteria: ").grid(row=5, column=0, padx=10, pady=5, sticky="w")

        fitness_options = ["Sharpe ratio","Adjusted sharpe ratio","Profit factor", "Net profit"]
        fitness_dropdown = customtkinter.CTkOptionMenu(frame5, values=fitness_options, variable=fitnessTypeVar)
        fitness_dropdown.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        # button to start optimization
        button_start = customtkinter.CTkButton(self.window, text="Start Optimization", command=threading.Thread(target=button_callback).start)
        button_start.grid(row=4, column=3,  padx=10, pady=10, sticky="se")

