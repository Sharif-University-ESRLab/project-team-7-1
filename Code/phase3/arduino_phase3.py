import serial
from signal import signal
import numpy as np
from tkinter import *
import tkinter.font as font

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
import matplotlib.pyplot as plt
import matplotlib
import types
import time
import threading
from tkinter.filedialog import asksaveasfile, askopenfile
N = 16
L = 128
MAX_L = 1024
MIN_L = 8

signal_array = [[1] for i in range(N)]

loaded_signals = []

for j in range(N):
    for i in range(MAX_L - 2):
        signal_array[j] += [0]
    signal_array[j] += [1]

# plot function is created for
# plotting the graph in
# tkinter window

shown_signals = [1 for i in range(N)]

# the main Tkinter window
window = Tk()

# setting the title
window.title('Input Signals')

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
    zoom_in_button = Button(window, text="+", command=zoom_in,
                            bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
    zoom_in_button.place(x=50, y=height // 2 - 100, height=100, width=100)
    zoom_out_button = Button(window, text="-", command=zoom_out,
                             bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
    zoom_out_button.place(x=50, y=height // 2 + 100, height=100, width=100)


def set_checkboxes():
    global shown_signals
    tmp_shown_signals = [IntVar(value=1) for i in range(N)]

    def change_checkbox():
        for i in range(N):
            shown_signals[i] = tmp_shown_signals[i].get()
        init_plot()

    for i in range(N):
        c1 = Checkbutton(window, text='Signal{}'.format(i), font=font.Font(
            size=15), variable=tmp_shown_signals[i], onvalue=1, offvalue=0, command=change_checkbox)
        if i < N // 2:
            y = height - 200
        else:
            y = height - 100
        x = (i % (N // 2)) * (width - 400) / (N // 2 - 1) + 180
        c1.place(x=x, y=y)


def set_save_buttons():
    def save_signal(ind):
        nums = signal_array[ind][:]
        files = [('All Files', '*.*'), ('Text Document', '*.txt')]
        file = asksaveasfile(filetypes=files, defaultextension=files)
        if file:
            for num in nums:
                file.write(str(num) + '\n')
            file.close()
    for i in range(N):
        if i < N // 2:
            y = height - 200
        else:
            y = height - 100
        x = (i % (N // 2)) * (width - 400) / (N // 2 - 1) + 300
        btn = Button(window, text='💾', command=lambda: save_signal(
            i), bg='#0052cc', fg='#ffffff', font=font.Font(size=12))
        btn.place(x=x, y=y)


def set_load_button():
    def load_signal():
        global thread_lock
        thread_lock.acquire()
        file = askopenfile()
        if file:
            sig = []
            for line in file.readlines():
                num = int(line.strip())
                sig.append(num)
            if len(sig) < MAX_L:
                sig = [0] * (MAX_L - len(sig)) + sig
            loaded_signals.append(sig)
        thread_lock.release()
        init_plot()

    def unload_signal():
        global thread_lock, loaded_signals
        thread_lock.acquire()
        if len(loaded_signals):
            loaded_signals = loaded_signals[:-1]
        thread_lock.release()
        init_plot()

    load_button = Button(window, text="Load", command=load_signal,
                         bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
                         
    unload_button = Button(window, text="Unload", command=unload_signal,
                         bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
    load_button.place(x=50, y=height // 2 - 500, height=100, width=100)
    unload_button.place(x=50, y=height // 2 - 300, height=100, width=100)
    

def init_plot():
    global fig, axs, canvas, axs_step, thread_lock
    thread_lock.acquire()
    if canvas:
        for item in canvas.get_tk_widget().find_all():
            canvas.get_tk_widget().delete(item)
    M = sum(shown_signals) + len(loaded_signals)
    fig, axs = plt.subplots(M, sharex=True, figsize=(25, 13))
    # for i in range(M):
    #    axs[i].get_yaxis().set_visible(False)
    x = [i for i in range(L)]
    ind = 0
    axs_step = []
    for i in range(N):
        if not shown_signals[i]:
            continue
        axs_step += [axs[ind].step(x, signal_array[i][-L:])[0]]
        axs[ind].set_ylabel("signal{}".format(
            i), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1
    for i in range(len(loaded_signals)):
        axs_step += [axs[ind].step(x, loaded_signals[i][-L:])[0]]
        axs[ind].set_ylabel("Loaded signal{}".format(
            i), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1
    canvas = FigureCanvasTkAgg(fig,
                               master=window)

    canvas.draw()
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().place(x=200, y=100)
    thread_lock.release()


def update_signals():
    global signal_array, thread_lock
    ser = serial.Serial('COM5', 9600, timeout=1)
    while True:
        line = ser.readline()
        decoded_line = line.decode('utf-8').strip("\r\n")
        serial_signal = "{:016b}".format((int(decoded_line if decoded_line != '' else '0')))
        thread_lock.acquire()
        x = [i for i in range(L)]
        for i in range(N):
            signal_array[i] += [int(serial_signal[15 - i])]
            if len(signal_array[i]) > MAX_L:
                signal_array[i] = signal_array[i][-MAX_L:]
        # x = [i for i in range(L)]
        # for i in range(N):
        #     signal_array[i] += [int(np.random.randint(0, 2))]
        #     if len(signal_array[i]) > MAX_L:
        #         signal_array[i] = signal_array[i][-MAX_L:]
        # x = [i for i in range(L)]

        ind = 0
        for i in range(N):
            if not shown_signals[i]:
                continue
            axs_step[ind].set_xdata(x)
            axs_step[ind].set_ydata(signal_array[i][-L:])
            plt.draw()
            ind += 1
        thread_lock.release()
        time.sleep(1)


thread_lock = threading.Lock()

set_zoom_buttons()

set_checkboxes()

set_save_buttons()

set_load_button()

init_plot()


thread = threading.Thread(target=update_signals)
# thread.setDaemon(True)
thread.start()


try:
    mainloop()
except:
    print("Error!")
    exit(0)