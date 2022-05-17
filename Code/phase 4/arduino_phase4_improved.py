import serial
from signal import signal
import numpy as np
from tkinter import *
import tkinter.font as font
import re

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
MIN_L = 1

colors = [['red', 'blue'], ['green', 'purple'], ['black', 'orange']]
current_color = 0


signal_array = [[1] for i in range(N)]

loaded_signals = []

output_signals = [[0], [0]]

output_inds = [0, 0]

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

def set_color_button():
    def switch_color():
        global current_color, colors
        current_color = (current_color + 1) % len(colors)
        init_plot()
    color_button = Button(window, text="Color", command=switch_color,
                         bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
    color_button.place(x=50, y=height // 2 + 300, height=100, width=100)

def set_output_textbox():
    def submit_output(index):
        global output_signals, output_inds
        out_text = text_var.get()
        text_var.set("")
        if not out_text or not re.match("[01]*", out_text):
            return
        output_signals[index] = [int(c) for c in out_text]
        output_inds[index] = 0
        init_plot()
    output_label = Label(window, text="Enter Output Signal Sequence", font=font.Font(size=20))
    text_var = StringVar()
    output_textbox = Entry(window, textvariable=text_var, font=font.Font(size=20))
    sub_btn1 = Button(window, text = "Set Out1", command = lambda : submit_output(0), font=font.Font(size=20), bg='#0052cc', fg="#ffffff")
    sub_btn2 = Button(window, text = "Set Out2", command = lambda : submit_output(1), font=font.Font(size=20), bg='#0052cc', fg="#ffffff")
    output_label.place(x=180, y= height - 300, height=50, width=500)
    output_textbox.place(x=700, y= height - 300, height=50, width=1600)
    sub_btn1.place(x=2320, y=height - 300, height= 50, width=150)
    sub_btn2.place(x=2500, y=height - 300, height= 50, width=150)


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
    M = sum(shown_signals) + len(loaded_signals) + len(output_signals)
    fig, axs = plt.subplots(M, sharex=False, figsize=(25, 13))
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.9, wspace=0.1, hspace=0.1)
    # for i in range(M):
    #    axs[i].get_yaxis().set_visible(False)
    x = [i for i in range(L + 1)]
    ind = 0
    axs_step = []
    for i in range(N):
        if not shown_signals[i]:
            continue
        axs_step += [axs[ind].step(x, [signal_array[i][0]] + signal_array[i][-L:])[0]]
        axs[ind].set_yticks([0,1])
        axs_step[ind].set_color(colors[current_color][ind % 2])
        axs[ind].set_ylabel("signal{}".format(
            i), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1
    for i in range(len(loaded_signals)):
        axs_step += [axs[ind].step(x, [loaded_signals[i][0]] + loaded_signals[i][-L:])[0]]
        axs[ind].set_yticks([0,1])
        axs_step[ind].set_color(colors[current_color][ind % 2])
        axs[ind].set_ylabel("Loaded signal{}".format(
            i), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1
    out_colors = ["fuchsia", "indigo"]
    for i in range(len(output_signals)):
        x_out = [j for j in range(len(output_signals[i]) + 1)]
        ydata = output_signals[i][output_inds[i]:] + output_signals[i][:output_inds[i]]
        axs_step += [axs[ind].step(x_out, [ydata[0]] + ydata)[0]]
        axs[ind].set_yticks([0,1])
        axs_step[ind].set_color(out_colors[i % 2])
        axs[ind].set_ylabel("Output signal{}".format(
            i + 1), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1

    canvas = FigureCanvasTkAgg(fig,
                               master=window)

    canvas.draw()
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().place(x=200, y=100)
    thread_lock.release()


def update_signals():
    global signal_array, thread_lock, output_inds
    ser = serial.Serial('COM5', 9600, timeout=1)
    while True:
        
        line = ser.readline()
        decoded_line = line.decode('utf-8').strip("\r\n")
        if not re.match("[0-9]+", decoded_line):
            continue
        print(decoded_line)
        serial_signal = "{:016b}".format((int(decoded_line if decoded_line != '' else '0')))
        time.sleep(1)
        num_to_write = str(sum((2**i)*output_signals[i][output_inds[i]] for i in range(len(output_signals))))
        for i in range(len(output_inds)):
            output_inds[i] = (output_inds[i] + 1) % len(output_signals[i])
        ser.write(num_to_write.encode())
        thread_lock.acquire()
        x = [i for i in range(L + 1)]
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
            axs_step[ind].set_ydata([signal_array[i][0]] + signal_array[i][-L:])
            plt.draw()
            ind += 1
        ind += len(loaded_signals)
        for i in range(len(output_signals)):
            ydata = output_signals[i][output_inds[i]:] + output_signals[i][:output_inds[i]]
            axs_step[ind].set_ydata([ydata[0]] + ydata)
            ind += 1


        
        thread_lock.release()
        time.sleep(1)


thread_lock = threading.Lock()

set_zoom_buttons()

set_checkboxes()

set_save_buttons()

set_load_button()

set_color_button()

set_output_textbox()

init_plot()


thread = threading.Thread(target=update_signals)
# thread.setDaemon(True)
thread.start()


try:
    mainloop()
except:
    print("Error!")
    exit(0)