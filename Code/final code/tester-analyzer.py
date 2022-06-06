# importing libraries
import serial
from signal import signal
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
# usb port for connecting to arduino
serial_port = 'COM5'

# possible colors for input signal plot lines (alternating)
colors = [['red', 'blue'], ['green', 'purple'], ['black', 'orange']]
current_color = 0

# input signals
signal_array = [[1] for i in range(N)]

# loaded signals
loaded_signals = []

# signals sent to output
output_signals = [[0], [0]]

# indices for cycling through output signals
output_inds = [0, 0]

# initialize signals with minimum length
for j in range(N):
    for i in range(MAX_L - 2):
        signal_array[j] += [0]
    signal_array[j] += [1]

# signals selected for showing
shown_signals = [1 for i in range(N)]

# setting up main GUI window
window = Tk()

window.title('Digital Tester and Analyzer')
width = 2800
height = 1800
window.geometry("%dx%d" % (width, height))

# global plot variables
fig = None
axs = None
axs_step = None
canvas = None

# sets up the buttons for zooming in and out
def set_zoom_buttons():
    # zooms in one level by halving the number of points shown
    def zoom_in():
        global L
        if L >= MIN_L * 2:
            L = L // 2
            init_plot()
    # zooms out one level by doubling the number of points shown
    def zoom_out():
        global L
        if L <= MAX_L // 2:
            L = L * 2
            init_plot()
    # zoom buttons in GUI
    zoom_in_button = Button(window, text="+", command=zoom_in,
                            bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
    zoom_in_button.place(x=50, y=height // 2 - 100, height=100, width=100)
    zoom_out_button = Button(window, text="-", command=zoom_out,
                             bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
    zoom_out_button.place(x=50, y=height // 2 + 100, height=100, width=100)

# sets up checkboxes for selecting signals to be shown
def set_checkboxes():
    global shown_signals
    tmp_shown_signals = [IntVar(value=1) for i in range(N)]
    # change shown signals
    def change_checkbox():
        for i in range(N):
            shown_signals[i] = tmp_shown_signals[i].get()
        init_plot()
    # checkboxes and labels in GUI
    for i in range(N):
        c1 = Checkbutton(window, text='Signal{}'.format(i), font=font.Font(
            size=15), variable=tmp_shown_signals[i], onvalue=1, offvalue=0, command=change_checkbox)
        if i < N // 2:
            y = height - 200
        else:
            y = height - 100
        x = (i % (N // 2)) * (width - 400) / (N // 2 - 1) + 180
        c1.place(x=x, y=y)

# set up the save buttons
def set_save_buttons():
    # show fileselect dialog and save the chosen signal in the selected file
    # saves each signal value on a seperate line
    class button_command_obj:
        def __init__(self, ind) -> None:
            self.ind = ind
        def save_signal(self):
            nums = signal_array[self.ind][:]
            print(nums)
            files = [('All Files', '*.*'), ('Text Document', '*.txt')]
            file = asksaveasfile(filetypes=files, defaultextension=files)
            if file:
                for num in nums:
                    file.write(str(num) + '\n')
                file.close()
    # set up save buttons in the GUI
    for i in range(N):
        if i < N // 2:
            y = height - 200
        else:
            y = height - 100
        x = (i % (N // 2)) * (width - 400) / (N // 2 - 1) + 300
        btn = Button(window, text='💾', command=button_command_obj(i).save_signal
        , bg='#0052cc', fg='#ffffff', font=font.Font(size=12))
        btn.place(x=x, y=y)

# set up the load button
def set_load_button():
    # show file select dialog and load a signal from the selected file
    # assumes a file with the saved file format is given, which has one number on each line 
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
    # remove the last loaded signal from loaded signals list
    def unload_signal():
        global thread_lock, loaded_signals
        thread_lock.acquire()
        if len(loaded_signals):
            loaded_signals = loaded_signals[:-1]
        thread_lock.release()
        init_plot()
    # set up the load and unload buttons in the GUI
    load_button = Button(window, text="Load", command=load_signal,
                         bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
                         
    unload_button = Button(window, text="Unload", command=unload_signal,
                         bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
    load_button.place(x=50, y=height // 2 - 500, height=100, width=100)
    unload_button.place(x=50, y=height // 2 - 300, height=100, width=100)
    

# set up color switch button
def set_color_button():
    # switches the colors used for signal plot lines
    # by cycling through the options specified before 
    def switch_color():
        global current_color, colors
        current_color = (current_color + 1) % len(colors)
        init_plot()
    # set up color button in GUI
    color_button = Button(window, text="Color", command=switch_color,
                         bg='#0052cc', fg='#ffffff', font=font.Font(size=20))
    color_button.place(x=50, y=height // 2 + 300, height=100, width=100)

# set up textboxes and buttons to input signals to be sent to arduino
def set_output_textbox():
    # set output signal based on string sequence of 0s and 1s
    def submit_output(index):
        global output_signals, output_inds
        out_text = text_var.get()
        text_var.set("")
        if not out_text or not re.match("[01]*", out_text):
            return
        output_signals[index] = [int(c) for c in out_text]
        output_inds[index] = 0
        init_plot()
    # set up the elements in the GUI
    output_label = Label(window, text="Enter Output Signal Sequence", font=font.Font(size=20))
    text_var = StringVar()
    output_textbox = Entry(window, textvariable=text_var, font=font.Font(size=20))
    sub_btn1 = Button(window, text = "Set Out1", command = lambda : submit_output(0), font=font.Font(size=20), bg='#0052cc', fg="#ffffff")
    sub_btn2 = Button(window, text = "Set Out2", command = lambda : submit_output(1), font=font.Font(size=20), bg='#0052cc', fg="#ffffff")
    output_label.place(x=180, y= height - 300, height=50, width=500)
    output_textbox.place(x=700, y= height - 300, height=50, width=1600)
    sub_btn1.place(x=2320, y=height - 300, height= 50, width=150)
    sub_btn2.place(x=2500, y=height - 300, height= 50, width=150)

# draw or redraw the entire plot, for initializing and changes other than new input entry (e.g. zoom, selection, load, etc)
def init_plot():
    global fig, axs, canvas, axs_step, thread_lock
    # avoid concurrency issues
    thread_lock.acquire()
    # delete previously drawn plot for redraw
    if canvas:
        for item in canvas.get_tk_widget().find_all():
            canvas.get_tk_widget().delete(item)
    # number of signals in plot
    M = sum(shown_signals) + len(loaded_signals) + len(output_signals)
    # make a plot with M subplots and set overall paramaters
    fig, axs = plt.subplots(M, sharex=False, figsize=(25, 13))
    plt.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.9, wspace=0.1, hspace=0.1)
    x = [i for i in range(L + 1)]
    ind = 0
    axs_step = []
    # plot input signals selected to be shown 
    for i in range(N):
        if not shown_signals[i]:
            continue
        # plot the last L elements (L is determined by zoom level)
        axs_step += [axs[ind].step(x, [signal_array[i][0]] + signal_array[i][-L:])[0]]
        axs[ind].set_yticks([0,1])
        # color the plots using alternating colors
        axs_step[ind].set_color(colors[current_color][ind % 2])
        axs[ind].set_ylabel("signal{}".format(
            i), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1
    # plot loaded signals
    for i in range(len(loaded_signals)):
        # plot the last L elements (L is determined by zoom level)
        axs_step += [axs[ind].step(x, [loaded_signals[i][0]] + loaded_signals[i][-L:])[0]]
        axs[ind].set_yticks([0,1])
        # color the plots using alternating colors
        axs_step[ind].set_color(colors[current_color][ind % 2])
        axs[ind].set_ylabel("Loaded signal{}".format(
            i), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1
    # output signal colors
    out_colors = ["fuchsia", "indigo"]
    for i in range(len(output_signals)):
        # plot all signal elements for outputs 
        x_out = [j for j in range(len(output_signals[i]) + 1)]
        ydata = output_signals[i][output_inds[i]:] + output_signals[i][:output_inds[i]]
        axs_step += [axs[ind].step(x_out, [ydata[0]] + ydata)[0]]
        axs[ind].set_yticks([0,1])
        # set plot line color
        axs_step[ind].set_color(out_colors[i % 2])
        axs[ind].set_ylabel("Output signal{}".format(
            i + 1), rotation=0, fontsize=20, labelpad=50, horizontalalignment="center")
        ind += 1

    # add plot figure to GUI
    canvas = FigureCanvasTkAgg(fig,
                               master=window)

    canvas.draw()
    canvas.get_tk_widget().place(x=200, y=100)
    thread_lock.release()


# receive signals from and send signals to arduino
# update signal plots based on data
def update_signals():
    global signal_array, thread_lock, output_inds
    # establish serial connection on usb port
    # using same baudrate as arduino code
    ser = serial.Serial(serial_port, 9600, timeout=1)
    while True:
        # receive input signals encoded as a 16 bit integer
        line = ser.readline()
        decoded_line = line.decode('utf-8').strip("\r\n")
        if not re.match("[0-9]+", decoded_line):
            continue
        print(decoded_line)
        # decode line to 16 bit binary string
        serial_signal = "{:016b}".format((int(decoded_line if decoded_line != '' else '0')))
        time.sleep(1)
        # send output signals as 2 bit integer
        num_to_write = str(sum((2**i)*output_signals[i][output_inds[i]] for i in range(len(output_signals))))
        for i in range(len(output_inds)):
            output_inds[i] = (output_inds[i] + 1) % len(output_signals[i])
        ser.write(num_to_write.encode())
        thread_lock.acquire()
        x = [i for i in range(L + 1)]
        # add new serial bits to input signals
        for i in range(N):
            signal_array[i] += [int(serial_signal[15 - i])]
            if len(signal_array[i]) > MAX_L:
                signal_array[i] = signal_array[i][-MAX_L:]
        ind = 0
        # update input plot y values
        for i in range(N):
            if not shown_signals[i]:
                continue
            axs_step[ind].set_xdata(x)
            axs_step[ind].set_ydata([signal_array[i][0]] + signal_array[i][-L:])
            plt.draw()
            ind += 1
        ind += len(loaded_signals)
        # update output signal plots
        for i in range(len(output_signals)):
            ydata = output_signals[i][output_inds[i]:] + output_signals[i][:output_inds[i]]
            axs_step[ind].set_ydata([ydata[0]] + ydata)
            ind += 1
        thread_lock.release()
        time.sleep(1)


thread_lock = threading.Lock()

# initalize GUI and plots 
set_zoom_buttons()

set_checkboxes()

set_save_buttons()

set_load_button()

set_color_button()

set_output_textbox()

init_plot()

# start receiving, sending and updating signals
thread = threading.Thread(target=update_signals)
thread.start()


try:
    # GUI main loop
    mainloop()
except:
    print("Error!")
    exit(0)