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
from paternSimulation import PaternsSimulation

class paternFinder:
    def __init__(self):
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")
        
        # create a new top-level window 
        self.window = customtkinter.CTkToplevel()
        self.window.title("Paterns finder")
        self.window.geometry("950x650")
        self.window.attributes('-topmost', True)
        self.window.resizable(False,False)

        self.data = None
        self.genCompleted = 0
        
        # define variables
        tickerVar = tkinter.StringVar(value="BTC-USD")
        fixedSizeVar = tkinter.IntVar(value=1000)
        timeframe_var = tkinter.StringVar(value="1h")
        populationSizeVar = tkinter.IntVar(value = 20)
        mutationRateVar = tkinter.IntVar(value = 10)
        generationVar = tkinter.IntVar(value= 10)
        holdTimeVar = tkinter.IntVar(value=3)

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

            #print(f"Selected file path: {file_path}")  

            if file_path:
                optimizer.resultsdataframe.to_excel(file_path, index=False)
                print(f"File saved successfully at: {file_path}") 
            else:
                print("Save operation cancelled.")  

        #start button callback
        def button_callback():
            #get all the variables
            inputValid = True
            ticker = tickerVar.get()
            fixedPosSize = int(fixedSizeVar.get())
            from_date_value = from_date.get()
            to_date_value = to_date.get()
            timeframe_value = timeframe_var.get()
            populationSize = int(populationSizeVar.get())
            mutationRate = int(mutationRateVar.get())
            generations = int(generationVar.get())
            holdTime = int(holdTimeVar.get())

            #input check
            if fixedPosSize <= 0:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed position size must be greater than zero")

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
            
            if generations < 3:
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong generations number", message="The least possible number of generations is 3")

            if inputValid:
                
                self.progress_bar = customtkinter.CTkProgressBar(self.window, mode='determinate', height=30)
                self.progress_bar.grid(row=3, column=0, columnspan=3, padx=20, pady=85, sticky="sew")
                self.progress_bar.configure(progress_color="cyan")
                self.progress_bar.set(0)
     
                
                self.progress_bar_download = customtkinter.CTkProgressBar(self.window, mode='determinate', height=20)
                self.progress_bar_download.grid(row=2, column=0, columnspan=3, padx=20, pady=25, sticky="sew")
                self.progress_bar_download.configure(progress_color="lawngreen")
                self.progress_bar_download.set(0)
                self.progress_bar_download.start()

                download_data(ticker, from_date_value, to_date_value, timeframe_value)
                
                if not self.data.empty:
                    #if we downloaded data
                    progressLabel =  customtkinter.CTkLabel(self.window,text=f"Number of simulations the optimizer is going to perform: {generations*populationSize}",font=("Helvetica", 14, "normal"))
                    progressLabel.grid(row=2, column=1,columnspan=2, padx=80, pady=20, sticky="nw")

                    label2 = customtkinter.CTkLabel(self.window,text=f"Number of trading candles that are going to be analyzed: {generations*populationSize*len(self.data)}",font=("Helvetica", 14, "normal"))
                    label2.grid(row=2,column =1,columnspan=2,padx= 80,pady= 60,sticky="nw")

                    labelRunning = customtkinter.CTkLabel(self.window,text="Optimalization is running",font=("Helvetica",14,"bold"))
                    labelRunning.grid(row=2, column =1,columnspan=2,padx=140,pady=100,sticky="sew")

                    self.progress_bar_download.stop()
                    self.progress_bar_download.set(1)
                    mutationRate = int(mutationRate / 100)

                    
                    optimizer = PaternsSimulation(self.data,fixedPosSize,populationSize,generations,mutationRate,3)
                    #create a thread for the optimize function
                    optimizeThread = threading.Thread(target=optimizer.optimize)

                    labelgen = customtkinter.CTkLabel(self.window, text=f"Generations completed: {self.genCompleted}/{generations}", font=("Helvetica", 14, "normal"))
                    labelgen.grid(row=2, column=3, columnspan=3, padx=20, pady=5, sticky="nw")

                    labelgen2 = customtkinter.CTkLabel(self.window,text=f"Maximum profit: 0",font=("Helvetica", 14, "normal"))
                    labelgen2.grid(row=2,column =3,columnspan=1,padx= 20,pady= 40,sticky="nw")

                    labelgen3 = customtkinter.CTkLabel(self.window,text=f"Generation: 0 profit average: 0",font=("Helvetica", 14, "normal"))
                    labelgen3.grid(row=2,column =3,columnspan=1,padx= 20,pady= 80,sticky="nw")

                    optimizeThread.start()
              
                    while (optimizeThread.is_alive()):
                        time.sleep(0.1)
                        if len(optimizer.averageGen) > self.genCompleted:
                            self.genCompleted = len(optimizer.averageGen)
                            labelgen.configure(text=f"Generations completed: {self.genCompleted}/{generations}")
                            labelgen2.configure(text=f"Maximum profit: {optimizer.topFitness[len(optimizer.topFitness)-1]}")
                            labelgen3.configure(text=f"Generation: {self.genCompleted} profit average: {optimizer.averageGen[len(optimizer.averageGen)-1]}")
                            progressPercent = round(self.genCompleted / generations, 2)
                            self.progress_bar.set(progressPercent)
                        

                    self.window.withdraw()
                    exportExcel(optimizer)
                self.window.destroy()

        self.window.grid_rowconfigure(8, weight=1)
        self.window.grid_columnconfigure(8, weight=1)

        frame2 = customtkinter.CTkFrame(self.window)
        frame2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew", rowspan=2)

        frame4 = customtkinter.CTkFrame(self.window)
        frame4.grid(row=0, column=2, padx=10, pady=10, sticky="new", rowspan=2)

        frame5 = customtkinter.CTkFrame(self.window)
        frame5.grid(row=0, column=3, padx=10, pady=10, sticky="w", columnspan=4)

        heading2 = customtkinter.CTkLabel(frame2, text="Account's capital", font=("Helvetica", 16, "bold"))
        heading2.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")

        heading4 = customtkinter.CTkLabel(frame4, text="Trading range", font=("Helvetica", 16, "bold"))
        heading4.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")
        
        heading5 = customtkinter.CTkLabel(frame5, text="Optimalization parameters", font=("Helvetica", 16, "bold"))
        heading5.grid(row=0, column=0, columnspan=2, pady=10, sticky="n")
        
        label_fixedSize = customtkinter.CTkLabel(frame2, text="Fixed Position Size:")
        label_fixedSize.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entry_fixedSize = customtkinter.CTkEntry(frame2, textvariable=fixedSizeVar)
        entry_fixedSize.grid(row=3, column=1, padx=10, pady=5, sticky="ew")


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

        labelPopulation = customtkinter.CTkLabel(frame5, text="Population size:")
        labelPopulation.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        entryPopulation = customtkinter.CTkEntry(frame5, textvariable=populationSizeVar)
        entryPopulation.grid(row=1, column=1, padx=10, pady=5)

        labelMutationRate = customtkinter.CTkLabel(frame5, text="Mutation rate:")
        labelMutationRate.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        entryMutationRate = customtkinter.CTkEntry(frame5, textvariable=mutationRateVar)
        entryMutationRate.grid(row=3, column=1, padx=10, pady=5)

        labelGenerations = customtkinter.CTkLabel(frame5, text="Generations:")
        labelGenerations.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        entryGenerations = customtkinter.CTkEntry(frame5, textvariable=generationVar)
        entryGenerations.grid(row=4, column=1, padx=10, pady=5)

        button_start = customtkinter.CTkButton(self.window, text="Start Optimization", command= threading.Thread(target=button_callback).start)
        button_start.grid(row=3, column=3, padx=30, pady=30, sticky="ew")

