import tkinter
import tkinter.messagebox
import customtkinter
import threading
import time
import yfinance as yf
from tkcalendar import DateEntry
from simulation import Account
from simulation import Simulation
from datetime import datetime,timedelta


class backTestWindow:
    def __init__(self):
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")
        
        # Create a new top-level window 
        self.window = customtkinter.CTkToplevel()
        self.window.title("Strategy backtester")
        self.window.geometry("1000x500")
        self.window.attributes('-topmost', True)
        self.window.resizable(0, 0)
        self.data = None
        
        # define variables
        tickerVar = tkinter.StringVar(value="BTC-USD")
        shortMAVar = tkinter.IntVar(value = 9)
        longMAVar = tkinter.IntVar(value = 18)
        startBalanceVar = tkinter.IntVar(value = 10000)
        fixedSizeVar = tkinter.IntVar(value = 1000)
        fixedCapitalUseVar = tkinter.IntVar(value = 70)
        fixedPercentRiskVar = tkinter.IntVar(value = 2)
        slCheckedVar = tkinter.StringVar()
        slVar = tkinter.IntVar(value = 5)
        tpCheckedVar = tkinter.StringVar()
        tpVar = tkinter.IntVar(value = 5)
        timeframe_var = tkinter.StringVar(value="1d")
        pos_var = tkinter.StringVar(value="Fixed capital usage in %")

        def convert_date(date_entry):
         
         # Define the format of the date string
           date_format = "%Y-%m-%d"  # Adjust this format based on how the date is formatted in your DateEntry
        
         # Convert to datetime object
           date_obj = datetime.strptime(date_entry, date_format).date()
        
           return date_obj
        
        def download_data(ticker, start_date, end_date, interval):
            #yfinance.download has handling of errors implemented, the program wont crash if this function fails, if it does, it return empty data
            self.data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
            if(self.data.empty):
                self.window.destroy()
                tkinter.messagebox.showerror(title="Error downloading data",message="Error downloading data, check ticker or try different timeframe")
               
           
            
        #callback for thes start button
        def button_callback():
            
            inputValid = True
            #get variables values
            ticker = tickerVar.get()
            shortMA = int(shortMAVar.get())
            longMA = int(longMAVar.get())
            startBalance = int(startBalanceVar.get())
            fixedPosSize = int(fixedSizeVar.get())
            fixedCapitalUsage = int(fixedCapitalUseVar.get())
            fixedPercentRisk = int(fixedPercentRiskVar.get())
            slChecked = slCheckedVar.get()
            sl = int(slVar.get())
            tpChecked = tpCheckedVar.get()
            tp = int(tpVar.get())

            # calendar
            from_date_value = from_date.get()
            to_date_value = to_date.get()

             
            posSizeType = pos_var.get()
            timeframe_value = timeframe_var.get()

            slChecked = True if slCheckedVar.get() == "1" else False
            tpChecked = True if tpCheckedVar.get() == "1" else False

            #check for input
            if(shortMA < 3):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong period", message="Period of short moving average must be higher than 3",)
            if(longMA < 9):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong period", message="Period of long moving average must be higher than 9",)
            if(shortMA >= longMA):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong period", message="Period of long moving average must be greater than period of short moving average",)
            
            if(startBalance < 100):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong starting balance", message="Starting balance must be at least 100",)
            
            if(fixedPosSize > startBalance and posSizeType == "Fixed position size"):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed position size must be less than starting balance",)
            
            if(fixedPosSize <= 0 and posSizeType == "Fixed position size"):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed position size must be greater than zero",)
            
            if(fixedCapitalUsage <= 0 and posSizeType == "Fixed capital usage in %"):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed capital usage must be greater than zero",)
            
            if(posSizeType == "Adjusted to % risk" and not slChecked):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Turn on stoploss in order to use adjusted to % risk position sizing",)

            
            if(fixedCapitalUsage > 95 and posSizeType == "Fixed capital usage in %"):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Fixed capital usage must be at maximum 95 %",)
            
            if(fixedPercentRisk <= 0 and posSizeType == "Adjusted to % risk"):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Risk % per trade must be greater than 0",)
            
            if(fixedPercentRisk > 100 and posSizeType == "Adjusted to % risk"):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong position size", message="Risk % per trade must be at maximum 100 %",)
            
            if(tpChecked and tp <= 0):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong takeprofit value", message="Take profit must be greater than 0%",)
                #tp can be in theory higner than 100%, so no need to check for this condition
            
            if(slChecked and sl <= 0):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong stoploss value", message="Stoploss must be greater than 0%",)
                #also, sl can be higher than 100%, simulation class has real time monitoring, if equity drops to zero, all positions are closed
            
            #to compare dates, we have to convert them
            from_dateConverted = convert_date(from_date_value)
            to_dateConverted = convert_date(to_date_value)
         

            if(from_dateConverted > to_dateConverted):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong date", message="From date must be at least one day before the to date",)
            
            if(from_dateConverted == to_dateConverted):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong date", message="From date must be at least one day before the to date",)
            
            if(to_dateConverted > current_date):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong date", message="The date must be at least one day before the current day",)
            
            #free version of yahoo finance library lets us only download 730 days of trading data
            difference = abs((to_dateConverted - from_dateConverted).days)
            #print(difference)
            if(difference > 729):
                self.window.destroy()
                tkinter.messagebox.showwarning(title="Wrong date", message="The difference between two dates must be less than 730 days",)


            #we passed the input check
            if(inputValid):
            
                # Add the progress bar
                self.progress_bar = customtkinter.CTkProgressBar(self.window, mode='determinate',height=40,width=130)
                self.progress_bar.grid(row=6, column=0, columnspan=4, padx=20, pady=40, sticky="ew")
                self.progress_bar.configure(progress_color="cyan")
                self.progress_bar.set(0)
                
                # Add the progress bar
                self.progress_bar_download = customtkinter.CTkProgressBar(self.window, mode='determinate',height=20,width=130)
                self.progress_bar_download.grid(row=7, column=0, columnspan=4, padx=20, pady=15, sticky="ew")
                self.progress_bar_download.configure(progress_color="lawngreen")
                self.progress_bar_download.set(0)
                self.progress_bar_download.start()

                #try to download market data
                download_data(ticker,from_date_value,to_date_value,timeframe_value)
                #once again check if we correctly downloaded the data
                if(not self.data.empty):
                    #create a simulation object
                    simulation = Simulation(Account(self.data,startBalance),shortMA,longMA,False,0,0,0,posSizeType,fixedPercentRisk,slChecked,sl,tpChecked,tp,fixedCapitalUsage,fixedPosSize)
                    self.progress_bar_download.stop()
                    self.progress_bar_download.set(1)
                    #the downloading data has finished so we adjusted the progress bar

                    self.progress_bar.set(0.15)
                    #create a separate thread to run the simulation
                    thread = threading.Thread(target=simulation.runSimulation)
                    thread.start()
                    
                    while thread.is_alive():
                        time.sleep(0.5)  # Wait for a short time to avoid busy-waiting
                        #get finished status
                        print(f"{simulation.finishedPercent*100}%")
                        #update the progress bar, in my case it is very laggy, maybe optimize the simulation itself so it runs on multiple threads?
                        if(simulation.finishedPercent > 0.15):
                            self.progress_bar.set(simulation.finishedPercent)
                        
                    self.window.destroy()
                    simulation.plotResults()
                
                
        # configure rows and columns
        self.window.grid_rowconfigure(6, weight=1)
        self.window.grid_columnconfigure(6, weight=1)
        
        # Frame for Ticker and Timeframe
        frame1 = customtkinter.CTkFrame(self.window)
        frame1.grid(row=2, column=0, padx=10, pady=10, sticky="sw", columnspan=2,rowspan=2)

        # Frame for Trading range
        frame2 = customtkinter.CTkFrame(self.window)
        frame2.grid(row=2, column=4, padx=10, pady=10, sticky="ne", rowspan=2)

        # Frame for MA periods
        frame3 = customtkinter.CTkFrame(self.window)
        frame3.grid(row=4, column=0, padx=10, pady=10, sticky="nw", columnspan=2,rowspan=4)

        # Frame for position sizing
        frame4 = customtkinter.CTkFrame(self.window)
        frame4.grid(row=2, column=2, padx=10, pady=10, sticky="sw", rowspan=4)

        # Frame for Long MA limits
        frame5 = customtkinter.CTkFrame(self.window)
        frame5.grid(row=3, column=4, padx=10, pady=10, sticky="se", rowspan=3)
 
        # text ticker
        label = customtkinter.CTkLabel(frame1, text="Ticker:", font=('Arial', 18, 'bold'))
        label.grid(row=0, column=0, padx=20, pady=25, sticky="nw")

        # text box ticker
        entry = customtkinter.CTkEntry(frame1, textvariable=tickerVar, width=100, height=40)
        entry.grid(row=0, column=1, padx=0, pady=20, sticky="nw")

        # text Timeframe
        label = customtkinter.CTkLabel(frame1, text="Timeframe", font=('Arial', 18, 'bold'))
        label.grid(row=1, column=0, padx=20, pady=0, sticky="w")

        # OptionMenu for Timeframe
        timeframe_menu = customtkinter.CTkOptionMenu(frame1, variable=timeframe_var, values=["5m","1h", "1d"])
        timeframe_menu.grid(row=1, column=1, padx=0, pady=20, sticky="w")

        #OptionMenu for position sizing
        positionSizing = customtkinter.CTkOptionMenu(frame4,variable=pos_var,values = ["Fixed position size","Fixed capital usage in %","Adjusted to % risk"])
        positionSizing.grid(row=1,column=1,padx=10,pady=10,sticky= "w")

      
        # texts for averages
        label = customtkinter.CTkLabel(frame3, text="Moving averages", font=('Arial', 18, 'bold'))
        label.grid(row=0, column=0,columnspan =2, padx=0, pady=0, sticky="ew")

        label = customtkinter.CTkLabel(frame3, text="Short moving average period")
        label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        label = customtkinter.CTkLabel(frame3, text="Long moving average period")
        label.grid(row=2, column=0, padx=20, pady=10, sticky="w")


        # entries for variables
        entry = customtkinter.CTkEntry(frame3, textvariable=shortMAVar, width=35, height=35)
        entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        entry = customtkinter.CTkEntry(frame3, textvariable=longMAVar, width=35, height=35)
        entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # texts for account's capital
        label = customtkinter.CTkLabel(frame4, text="Account's capital", font=('Arial', 18, 'bold'))
        label.grid(row=0, column=0,columnspan =2, padx=10, pady=10, sticky="ew")

        label = customtkinter.CTkLabel(frame5, text="Risk management", font=('Arial', 18, 'bold'))
        label.grid(row=0, column=0,columnspan =4, padx=0, pady=0, sticky="ew")

        label = customtkinter.CTkLabel(frame4,text="Position sizing type:")
        label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        label = customtkinter.CTkLabel(frame4, text="Starting balance:")
        label.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        label = customtkinter.CTkLabel(frame4, text="Fixed position size:")
        label.grid(row=3, column=0, padx=20, pady=10, sticky="w")

        label = customtkinter.CTkLabel(frame4, text="Fixed capital usage %:")
        label.grid(row=4, column=0, padx=20,pady=10,sticky="w")

        label = customtkinter.CTkLabel(frame4, text="Risk % per trade:")
        label.grid(row=5, column=0, padx=20, pady=10, sticky="w")

        # entreries for accounts capital
        entry = customtkinter.CTkEntry(frame4, textvariable=startBalanceVar, width=80, height=35)
        entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        entry = customtkinter.CTkEntry(frame4, textvariable=fixedSizeVar, width=80, height=35)
        entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        entry = customtkinter.CTkEntry(frame4, textvariable=fixedCapitalUseVar, width=35, height=35)
        entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        entry = customtkinter.CTkEntry(frame4, textvariable=fixedPercentRiskVar, width=35, height=35)
        entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")

     
        # checkbox 
        checkbox_1 = customtkinter.CTkCheckBox(frame5, text="Take profit", variable=tpCheckedVar, onvalue="1", offvalue="0")
        checkbox_1.grid(row=1, column=0, padx=20, pady=20, sticky="w")  

        # checkbox 
        checkbox_2 = customtkinter.CTkCheckBox(frame5, text="Stoploss", variable=slCheckedVar, onvalue="1", offvalue="0")
        checkbox_2.grid(row=2, column=0, padx=20, pady=20, sticky="w")

        # texts tp sl
        label = customtkinter.CTkLabel(frame5, text="Take profit %")
        label.grid(row=1, column=1, padx=10, pady=10, sticky="e")

        label = customtkinter.CTkLabel(frame5, text="Stoploss %")
        label.grid(row=2, column=1, padx=10, pady=10, sticky="e")

        # entries tp sl
        entry = customtkinter.CTkEntry(frame5, textvariable=tpVar, width=35, height=35)
        entry.grid(row=1, column=2, padx=10, pady=10, sticky="e")

        entry = customtkinter.CTkEntry(frame5, textvariable=slVar, width=35, height=35)
        entry.grid(row=2, column=2, padx=10, pady=10, sticky="e")

        # trading range + from, to text + calendar
        label = customtkinter.CTkLabel(frame2, text="Trading range", font=('Arial', 18, 'bold'))
        label.grid(row=0, column=0, columnspan=2, padx=0, pady=10, sticky="ew")

        label = customtkinter.CTkLabel(frame2, text="From:")
        label.grid(row=1, column=0, padx=68, pady=10, sticky="w")

        from_date = DateEntry(frame2, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-d')
        from_date.grid(row=1, column=1, padx=(5, 20), pady=10, sticky="w")
        
        #get current day
        current_date = datetime.now().date() - timedelta(days=1)
        year_ago = current_date - timedelta(days = 365)
        from_date.set_date(year_ago)

        label = customtkinter.CTkLabel(frame2, text="To:")
        label.grid(row=2, column=0, padx=68, pady=10, sticky="w")

        to_date = DateEntry(frame2, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='y-mm-d')
        to_date.grid(row=2, column=1, padx=(5, 20), pady=10, sticky="w")
        to_date.set_date(current_date)

        # START button
        button = customtkinter.CTkButton(self.window, text="START", command=threading.Thread(target=button_callback).start)
        button.grid(row=6, column=4, columnspan=2, sticky="ew", padx=10, pady=10)


        # Start the window's main loop
        self.window.mainloop()

