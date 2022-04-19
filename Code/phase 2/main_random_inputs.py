#import serial
from signal import signal
import numpy as np
from tkinter import * 
import tkinter.font as font
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)
import matplotlib.pyplot as plt
import matplotlib
import types
import time
import threading

N = 16
L = 128
MAX_L = 1024
MIN_L = 8

signal_array = [[] for i in range(N)]

for j in range(N):
    for i in range(MAX_L):
        signal_array[j] += [int(np.random.randint(0,2))]



#ser = serial.Serial('COM3', 9600, timeout=1)
#for i in range(100):
#    line = ser.readline()
#    
#    signal_array += ["{:016b}".format((int(line.decode('utf-8').strip("\r\n"))))]

#ser.close()


  
# plot function is created for 
# plotting the graph in 
# tkinter window

shown_signals = [1 for i in range(N)]

# the main Tkinter window
window = Tk()
  
# setting the title 
window.title('Plotting in Tkinter')
  
# dimensions of the main window
#width= window.winfo_screenwidth()
#height= window.winfo_screenheight()
width = 2800
height = 1800
window.geometry("%dx%d" % (width, height))

fig = None
axs = None
axs_step = None
canvas = None


def set_zoom_buttons():
    def zoom_in():
        global L
        if L >= MIN_L * 2:
            L = L // 2
            init_plot()
    def zoom_out():
        global L
        if L <= MAX_L // 2:
            L = L * 2
            init_plot()
    zoom_in_button = Button(window, text ="+", command = zoom_in, bg='#0052cc', fg='#ffffff', font=font.Font(size=30))
    zoom_in_button.place(x=50, y=height // 2 - 100, height=100, width=100)
    zoom_out_button = Button(window, text ="-", command = zoom_out, bg='#0052cc', fg='#ffffff')
    zoom_out_button.place(x=50, y=height // 2 + 100, height=100, width=100)

def set_checkboxes():
    global shown_signals
    tmp_shown_signals = [IntVar(value=1) for i in range(N)]
    def change_checkbox():
        for i in range(N):
            shown_signals[i] = tmp_shown_signals[i].get()
        init_plot()

    for i in range(N):
        c1 = Checkbutton(window, text='Signal{}'.format(i), font=font.Font(size=25), variable=tmp_shown_signals[i], onvalue=1, offvalue=0, command=change_checkbox)
        if i < N // 2:
            y = height - 200
        else :
            y = height - 100
        x = (i % (N // 2)) * (width - 400) / (N // 2 - 1) + 180
        c1.place(x=x, y=y)


def init_plot():
    global fig, axs, canvas, axs_step
    M = sum(shown_signals)
    fig, axs = plt.subplots(M, sharex=True, figsize=(25, 15))
    #for i in range(M):
    #    axs[i].get_yaxis().set_visible(False)
    x = [i for i in range(L)]
    ind = 0
    axs_step = []
    for i in range(N):
        if not shown_signals[i]:
            continue
        axs_step += [axs[ind].step(x, signal_array[i][-L:])[0]]
        axs[ind].set_ylabel("signal{}".format(i), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1

    canvas = FigureCanvasTkAgg(fig,
                        master = window)  
    

    canvas.draw()
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().place(x=200, y=100)

  
def update_signals():
    global signal_array
    while True:
        x = [i for i in range(L)]
        for i in range(N):
            signal_array[i] += [int(np.random.randint(0,2))]
            if len(signal_array[i]) > MAX_L:
                signal_array = signal_array[-MAX_L:]
        x = [i for i in range(L)]
        ind = 0
        for i in range(N):
            if not shown_signals[i]:
                continue
            axs_step[ind].set_xdata(x)
            axs_step[ind].set_ydata(signal_array[i][-L:])
            plt.draw()
            ind += 1
        time.sleep(0.1)



  

set_zoom_buttons()

set_checkboxes()

init_plot()


thread = threading.Thread(target=update_signals)
thread.setDaemon(True)
thread.start()


try:
    window.mainloop()
except:
    print("Error!")
    exit(0)
