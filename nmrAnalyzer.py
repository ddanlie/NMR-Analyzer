import tkinter as tk 
import matplotlib as mlp
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import MouseEvent
from matplotlib.widgets import SpanSelector
from scipy.optimize import curve_fit
from scipy.optimize import minimize
from tkinter.font import Font
from tkinter import filedialog
import copy
import numpy as np


class VerticalScrolledFrame(tk.Frame):
    def __init__(self, parent, w, h, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
 
        # Create a canvas object and a vertical scrollbar for scrolling it.
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side="right", expand=False)
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0, 
                                width = w, height = h,
                                yscrollcommand=vscrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vscrollbar.config(command = self.canvas.yview)
 
 
        # Create a frame inside the canvas which will be scrolled with it.
        self.interior = tk.Frame(self.canvas)
        self.interior.bind('<Configure>', self._configure_interior)
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor=tk.NW)
        self.canvas.bind('<Configure>', self._configure_canvas)

    def _configure_interior(self, event):
        # Update the scrollbars to match the size of the inner frame.
        size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
        self.canvas.config(scrollregion=(0, 0, size[0], size[1]))
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # Update the canvas's width to fit the inner frame.
            self.canvas.config(width = self.interior.winfo_reqwidth())

    def _configure_canvas(self, event):
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # Update the inner frame's width to fill the canvas.
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())






class VerticalNavigationToolbar2Tk(NavigationToolbar2Tk):

    def __init__(self, canvas, window):
        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            # TODO Get this poor thing a nice gif
            #('Axes', 'Zoom in on region of interest (15-45)', 'subplots', 'plot_axes'),
            ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
            ('Save', 'Save the figure', 'filesave', 'save_figure'),
            ('Scale', 'Scale', 'zoom_to_rect', 'toolbar_change_scale')
            )
       # NavigationToolbar2Tk.toolitems += 
        super().__init__(canvas, window, pack_toolbar=False)
        self.scaleButtonText = tk.StringVar(None, f"Scale: {self.canvas.figure.get_axes()[0].get_yscale()}")
        self.custom_button = tk.Button(self, textvariable=self.scaleButtonText, command=self.toolbar_change_scale)
        #self.custom_button.pack(side=tk.TOP)

    

    # override _Button() to re-pack the toolbar button in vertical direction
    def _Button(self, text, image_file, toggle, command):
        b = super()._Button(text, image_file, toggle, command)
        b.pack(side=tk.TOP) # re-pack button in vertical direction
        return b

    # override _Spacer() to create vertical separator
    def _Spacer(self):
        s = tk.Frame(self, width=26, relief=tk.RIDGE, bg="DarkGray", padx=2)
        s.pack(side=tk.TOP, pady=5) # pack in vertical direction
        return s

    # disable showing mouse position in toolbar
    def set_message(self, s):
        pass

    def toolbar_change_scale(self):
        axes = self.canvas.figure.get_axes()
        scale = axes[0].get_yscale()
        #print(scale)
        if scale == 'linear':
            for ax in axes:
                ax.set_yscale('log')
        else:
            for ax in axes:
                ax.set_yscale('linear')
        self.scaleButtonText.set(f"Scale: {self.canvas.figure.get_axes()[0].get_yscale()}")
        self.canvas.draw()
   

class EntryScale(tk.Scale):


    def __init__(self, *a, **kwa):
        super().__init__(*a, **kwa)


    





class NMR(tk.Tk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("1280x820")

        #logic
        self.current_curve_num = 1
        self.data = None
        self.figure_log = []
        self.curve_log = [] #needs to be reversed
        self.edited_curves = [] 
        self.current_curve_params = None
        self.weights_approx = True
        self.approximated_weights = [] #needs to be reversed
        self.state = "select"#or "approx"
        self.approx_figure = None
        self.current_figure = None
        #logic end

        #frames
        self.canvasPanel = None
        self.canvasToolPanel = None
        self.controlPanel = tk.Frame(self, width=100)
        self.figureSettingsPanel = tk.Frame(self, borderwidth=1)
        self.bottomPanel = tk.Frame(self)
        self.editPanel = VerticalScrolledFrame(self.bottomPanel, 200, 200)
        self.editTopPanel = tk.Frame(self.editPanel.interior)
        self.resultPanel = tk.Text(self.bottomPanel, width=23, height=10)
    

        #frame tools
        self.span_selector = None
        self.curveNumText = "Curve number\n{}"
        self.statusText = "Status\n\n<{}>"
        self.curveNumLabelVar = tk.StringVar(None, self.curveNumText.format(self.current_curve_num))
        self.statusTextMaxLen = 30
        self.statuLabelVar = tk.StringVar(None)
        self.statuLabelVar_set(" ")

        self.generalFont = ("Arial", 12)
        #control panel interface
        self.statusLabel = tk.Label(self.controlPanel, textvariable=self.statuLabelVar, font=self.generalFont)
        self.curveNumLabel = tk.Label(self.controlPanel, textvariable=self.curveNumLabelVar, font=("Arial", 20, "bold"), width=int(self.statusTextMaxLen/2))
        self.saveCurveButton = tk.Button(self.controlPanel, text="Save curve",  font=self.generalFont, command=self.saveCurveButton_pressed)
        self.previousCurveButton = tk.Button( self.controlPanel, text="Previous curve",  font=self.generalFont, command=self.previousCurveButton_pressed) 
        self.approxButton = tk.Button(self.controlPanel, text="Approximate",  font=self.generalFont, command=self.approxButton_pressed) 
        self.resetButton = tk.Button(self.controlPanel, text="Reset", font=self.generalFont, command=self.resetButton_pressed)
        self.chooseFileButton = tk.Button(self.controlPanel, text="Choose file", font=self.generalFont, command=self.chooseFileButton_pressed)

        self.controlPanel.rowconfigure((2,3,4,5), minsize=40)#space between buttons
        self.controlPanel.rowconfigure(0, minsize=200)
        self.statusLabel.grid(row=0, column=0, columnspan=4, sticky=tk.EW)
        self.curveNumLabel.grid(row=1, column=0, columnspan=4, sticky=tk.EW, pady=(0,50))
        self.saveCurveButton.grid(row=2, column=1, columnspan=2, sticky=tk.EW)
        self.previousCurveButton.grid(row=3, column=1, columnspan=2, sticky=tk.EW)
        self.approxButton.grid(row=4, column=1, columnspan=2, sticky=tk.EW)
        self.resetButton.grid(row=5, column=1, columnspan=2, sticky=tk.EW)
        self.chooseFileButton.grid(row=6, column=1, columnspan=2, sticky=tk.EW)
        #status panel

        #figure settings
        self.switchSelectedButton = tk.Button(self.figureSettingsPanel, text="Switch", font=self.generalFont, command=self.switchSelectedButton_pressed)
        self.subtractButton = tk.Button(self.figureSettingsPanel, text="Subtract", font=self.generalFont, command=self.subtractButton_pressed)
        
        self.figureSettingsPanel.columnconfigure((0,1), uniform="Settings")
        self.switchSelectedButton.grid(row=0, column=0, sticky=tk.EW)
        self.subtractButton.grid(row=0, column=1, sticky=tk.EW)
        #figure settings
        
        #edit panel
        self.defaultButton = tk.Button(self.editTopPanel, text="Default", font=self.generalFont, command=self.defaultButton_pressed)
        self.fitButton = tk.Button(self.editTopPanel, text="Fit", font=self.generalFont, command=self.fitButton_pressed)


        self.editTopPanel.columnconfigure((0,1), uniform="Settings")
        self.defaultButton.grid(row=0, column=0, sticky=tk.EW)
        self.fitButton.grid(row=0, column=1, sticky=tk.EW)

        self.editTopPanel.pack(side="top", anchor="center")
        #result panel

        #bottom panel
        self.editPanel.pack(side="left",  anchor="center", fill="both", expand=True)
        self.resultPanel.pack(side="right", padx=60)

        #main frame
        

        self.bottomPanel.pack(side="bottom", fill="both", anchor="center", pady=25)
        self.figureSettingsPanel.pack(side="bottom", anchor="center", padx=(0, 325), pady=(5,0))
        self.controlPanel.pack(side="right", anchor="center", padx=(0,25))

        #reset will pack canvas
        # self.current_figure = self.get_curve_select_figure(data)
        # self.canvasPanel_pack(self.current_figure)
        # self.span_selector_set_axis(self.current_figure.get_axes()[0])
        self.resetButton_pressed()



    def subtractButton_pressed(self):
        subtracted_x = self.current_figure.get_axes()[1].lines[0].get_xdata()
        subtracted_y = self.current_figure.get_axes()[1].lines[0].get_ydata()
        self.current_figure.clf()
        plt.close(self.current_figure)
        self.current_figure = self.get_curve_select_figure((subtracted_x, subtracted_y))
        self.canvasPanel_pack(self.current_figure)
        self.span_selector_set_axis(self.current_figure.get_axes()[0])

        self.subtractButton.config(state="disabled")

    def switchSelectedButton_pressed(self, trim=None, update=True):
        x = self.current_figure.get_axes()[0].lines[0].get_xdata()
        y = self.current_figure.get_axes()[0].lines[0].get_ydata()
        ax = self.current_figure.get_axes()[1] 
        ax.cla()
        ax.set_yscale(self.current_figure.get_axes()[0].get_yscale())
        if(not hasattr(self, "curr_switch")):
            self.curr_switch = "subtraction"
        if(update):
            if(self.curr_switch == "subtraction"):
                self.curr_switch = "curve"
            else:
                self.curr_switch = "subtraction"
        if(trim != None):
            self.curr_trim = trim
        if(self.curr_switch  == "curve"):
            if(hasattr(self, "curr_trim")):
                x = x[self.curr_trim[0]:self.curr_trim[1]]
                y = y[self.curr_trim[0]:self.curr_trim[1]]
            y_curve = self.curve_function(x, *self.current_curve_params)
            ax.plot(x, y, color='blue')
            ax.plot(x, np.exp(y_curve), color='green')
        elif(self.curr_switch  == "subtraction"):
            y_curve = np.exp(self.curve_function(x, *self.current_curve_params))    
            y_difference = y - y_curve
            print(f"diff len = {len(y_difference)}")
            ax.plot(x, y_difference, color='red')
       
        self.canvasPanel.draw()


    def get_curve_select_figure(self, xy):
        f = plt.figure()
        axis = f.subplots(nrows=2, ncols=1)
        #if(self.current_curve_num == 1):
        axis[0].set_yscale("log")
        if(xy != None):
            axis[0].plot(xy[0], xy[1])
        return f
    
    def get_approximate_figure(self, predicted_xy, original_xy, f=None):
        if(f == None):
            f = plt.figure()
        else:
            f.clf()

        axes = f.subplots(nrows=2, ncols=1)
        axes[0].set_yscale("log")
        axes[0].plot(original_xy[0], original_xy[1], "blue")
        axes[0].plot(predicted_xy[0], predicted_xy[1], "r--")
        axes[1].plot(original_xy[0], original_xy[1]-predicted_xy[1], "red")
        return f





    def canvasPanel_pack(self, f):
        if(self.canvasPanel != None):
            self.canvasPanel.get_tk_widget().destroy()
            self.toolbar.destroy()
        self.canvasPanel = FigureCanvasTkAgg(f, master=self)
        self.toolbar = VerticalNavigationToolbar2Tk(self.canvasPanel, self)
        self.toolbar.update()
        self.toolbar.pack(side="left", anchor="center", padx=(25, 0), pady=5)
        self.canvasPanel.get_tk_widget().pack(side="left", fill="both", expand=True, padx=(0, 25), pady=(25, 0))

        self.canvasPanel.draw()



    def span_selector_set_axis(self, axis):
        if(self.span_selector != None):
            self.span_selector.set_visible(False)
        self.span_selector = SpanSelector(axis, self.curve_selected, 'horizontal', useblit=True, interactive=True, drag_from_anywhere=True, props=dict(alpha=0.5, facecolor="tab:blue"))


    def curve_function(self, x, a, b):
        return a*x+b

    def curve_selected(self, xmin, xmax):
        x = self.current_figure.get_axes()[0].lines[0].get_xdata()
        y = self.current_figure.get_axes()[0].lines[0].get_ydata()
        indmin, indmax = np.searchsorted(x, (xmin, xmax))
        indmax = min(len(x) - 1, indmax)
        indmin = max(0, indmin)
        if(indmax-indmin < 2):
            self.statuLabelVar_set("Found curve is too short")
            return
        trim_x = np.array(x[indmin:indmax])
        trim_y = np.array(y[indmin:indmax])
        if(self.mode == "select"):
            #print(f"{indmin}, {indmax}")

            #we will aproximate ln(y)
            trim_ylog = np.log(trim_y)
        
            print(f"trim len = {len(trim_x)}")
            self.current_curve_params, _ = curve_fit(self.curve_function, trim_x, trim_ylog, p0=(-1/len(trim_x), 1))
            self.switchSelectedButton_pressed((indmin,indmax), False)
            
            self.saveCurveButton.config(state="normal")
            self.previousCurveButton.config(state="disabled")
            self.approxButton.config(state="disabled")
            self.subtractButton.config(state="normal")
            if(self.mode == "select"):
                self.switchSelectedButton.config(state="normal")
            self.statuLabelVar_set(f"Found curve.\nTime T{self.current_curve_num} = {int(-1/self.current_curve_params[0])}")

        if(self.mode == "approx"):
            self.trim_fit = (indmin,indmax)     
            self.fitButton.config(state="normal")
            self.statuLabelVar_set("Data for fitting are chosen")         


    def resetButton_pressed(self):
        self.span_selector = None
        self.current_curve_num = 1
        self.current_curve_params = None
        self.approximated_weights = []
        self.weights_approx = True
        self.set_results(clean=True)
        self.curve_log = []
        self.edited_curves = []
        self.mode = "select"
        self.delete_approximation_edit()
        self.curveNumLabelVar.set(self.curveNumText.format(self.current_curve_num))
        self.statuLabelVar_set("reset")
        self.defaultButton.config(state="disabled")
        self.fitButton.config(state="disabled")
        self.subtractButton.config(state="disabled")
        self.saveCurveButton.config(state="disabled")
        self.previousCurveButton.config(state="disabled")
        self.approxButton.config(state="disabled")
        self.switchSelectedButton.config(state="disabled")
        if(self.data == None):
            self.saveCurveButton.config(state="disabled")

        for f in self.figure_log:
            plt.close(f)
        self.figure_log = []

        self.approx_figure = None
        self.current_figure = self.get_curve_select_figure(self.data)

        self.canvasPanel_pack(self.current_figure)
        self.span_selector_set_axis(self.current_figure.get_axes()[0])

    def approxButton_pressed(self):

        x = np.array(self.data[0])
        y = np.array(self.data[1])
        result = np.zeros(len(x))
        if(self.weights_approx):
            self.approximated_weights = []
            sum_w = 0
            w = np.exp(self.edited_curves[0][1])
            self.approximated_weights.append(w)
            #print(f"w = {w}")
            result += w*np.exp(x*self.edited_curves[0][0])
            sum_w += w
            length = len(self.edited_curves)
            if(length > 2):
                for curve_params in self.edited_curves[1:-1]:
                    w = (1-sum_w) * np.exp(curve_params[1])
                    self.approximated_weights.append(w)
                    #print(f"w = {w}") 
                    result += w*np.exp(x*curve_params[0])
                    sum_w += w
            if(length > 1):
                w = (1-sum_w)
                self.approximated_weights.append(w)
                #print(f"w = {w}")
                result += w*np.exp(x*self.edited_curves[-1][0])
        else:
            for i in range(len(self.approximated_weights)):
                result += self.approximated_weights[i]*(np.exp(x*self.edited_curves[i][0]))

        if(self.mode == "approx"):
            self.approx_figure = self.get_approximate_figure((x, result), (x, y), self.approx_figure)
            self.canvasPanel.draw()
        else:
            self.approx_figure = self.get_approximate_figure((x, result), (x, y))
            self.canvasPanel_pack(self.approx_figure)
        
        self.span_selector_set_axis(self.approx_figure.get_axes()[0])
        

        self.saveCurveButton.config(state="disabled")
        self.approxButton.config(state="disabled")
        self.previousCurveButton.config(state="normal")
        self.statuLabelVar_set(f"Approximated with {len(self.edited_curves)} curves")

        if(self.mode != "approx"):
            self.add_approximation_edit()
        
        self.update_edit()
        self.set_results()
        self.mode = "approx"

    #delete from log this (if saved) and previous curve 
    def previousCurveButton_pressed(self):
        if(len(self.curve_log) == self.current_curve_num):#curve_log len = figure_log len
            self.curve_log.pop()
            plt.close(self.figure_log.pop())

        self.saveCurveButton.config(state="disabled")
        self.defaultButton.config(state="disabled")
        self.statuLabelVar_set("Curve(s) deleted")
        self.current_curve_params = None
        if(self.mode == "approx"):
            self.delete_approximation_edit()
            plt.close(self.approx_figure)
        else:
            self.current_curve_num -= 1
            self.curve_log.pop()
            self.current_figure = self.figure_log.pop()
            

        if(self.current_curve_num <= 1):
            self.current_curve_num = 1
            self.previousCurveButton.config(state="disabled")
            self.approxButton.config(state="disabled")

        self.canvasPanel_pack(self.current_figure)
        self.span_selector_set_axis(self.current_figure.get_axes()[0])
        self.curveNumLabelVar.set(self.curveNumText.format(self.current_curve_num))
        self.mode = "select"
        self.edited_curves = copy.deepcopy(self.curve_log)
        self.weights_approx = True
                
        # print(len(self.curve_log))
        # print(len(self.figure_log))
            

    def saveCurveButton_pressed(self):
        x = self.current_figure.get_axes()[0].lines[0].get_xdata()
        y_data = self.current_figure.get_axes()[0].lines[0].get_ydata()
        y_curve = np.exp(self.curve_function(x, *self.current_curve_params))
        #subtract
        y_difference = y_data - y_curve
        trim_index = len(y_difference)#np.where(y_difference < 1e-10)[0][0]
        #print(f"trim = {trim_index}")
        y_difference = y_difference[0:trim_index]
        x = x[0:trim_index]
        #add new data to log
        if(len(self.curve_log) == self.current_curve_num):
            self.curve_log.pop()
        self.curve_log.append(self.current_curve_params)
        if(len(self.figure_log) == self.current_curve_num):
            plt.close(self.figure_log.pop())
        self.figure_log.append(self.current_figure)
        if(len(x) > 10):
            #set figure
            self.current_curve_num += 1
            self.curveNumLabelVar.set(self.curveNumText.format(self.current_curve_num))
            self.current_figure = self.get_curve_select_figure((x,y_difference))
            self.canvasPanel_pack(self.current_figure)
            self.span_selector_set_axis(self.current_figure.get_axes()[0])
        
        self.edited_curves = copy.deepcopy(self.curve_log)

        self.saveCurveButton.config(state="disabled")
        self.previousCurveButton.config(state="normal")
        self.approxButton.config(state="normal")
        self.switchSelectedButton.config(state="disabled")
        self.statuLabelVar_set("Curve saved")

        
        # print(len(self.curve_log))
        # print(len(self.figure_log))

    def statuLabelVar_set(self, text):
        #text = text[0:self.statusTextMaxLen]
        #text = self.statusText.format(text.center(self.statusTextMaxLen))
        self.statuLabelVar.set(self.statusText.format(text))

    def set_results(self, clean=False):
        self.resultPanel.delete('1.0', tk.END)
        if(clean):
            return
        result = ""
        for i, w in enumerate(self.approximated_weights):
            result += f"W{len(self.approximated_weights)-i}: {round(w,5)}\n"
        result += "\n"
        for i, params in enumerate(self.edited_curves):
            result += f"T{len(self.edited_curves)-i}: {int((-1/params[0]))}\n"
        self.resultPanel.insert(tk.END, result)

    def defaultButton_pressed(self):
        self.weights_approx = True
        self.edited_curves = copy.deepcopy(self.curve_log)
        self.approxButton_pressed()
        for i, w in enumerate(self.w_vars):
            w.set(self.approximated_weights[i])
        for i, t in enumerate(self.t_vars):
            t.set(-1/self.edited_curves[i][0])
        self.statuLabelVar_set("returned to default curves")
        self.defaultButton.config(state="disabled")

    def fitButton_pressed(self):
        x = self.data[0]
        y = self.data[1]
        if(hasattr(self, "trim_fit")):
            if(self.trim_fit is not None):
                x = x[self.trim_fit[0]:self.trim_fit[1]]
                y = y[self.trim_fit[0]:self.trim_fit[1]]
        x = np.array(x)
        y = np.array(y)
        self.fit_goal = None
        self.fit_base = None

 
        def objective(coefs):
            result = np.zeros_like(x)
            for w,t in zip(coefs[len(self.edited_curves):], coefs[0:len(self.edited_curves)]):
                result += w*np.exp(-x/(t*maxT))
            result /= result[0]
            print(np.mean((result - y)**2))
            return np.mean((result - y)**2)

        def w_constraint(coefs):#coefs = T3,T2,T1...w3,w2,w1...
            ws = coefs[len(self.edited_curves):]
            s = sum(ws)
            res = s-1
            if(s <= 1.0001 and s > 0.999):
                res = 0
            # print(coefs)
            return res

        bnds = []
        initial_guess = []
        maxT = 0
        for t in self.t_vars:
            if(t.get() > maxT):
                maxT = t.get()
            
        for t in self.t_vars:
            initial_guess.append(np.random.random())
            bnds.append((0, 1))
        for w in self.w_vars:
            initial_guess.append(np.random.random())
            bnds.append((0, 1))

        self.statuLabelVar_set("Solving...")

        cons = ({'type': 'eq', 'fun': w_constraint})
        
        solution = minimize(objective, initial_guess, bounds=bnds, constraints=cons)
        
        self.statuLabelVar_set("Solved")
        
        
        print(solution.x)
        self.weights_approx = False
        self.approximated_weights = []
        for i, t in enumerate(solution.x[0:len(self.edited_curves)]):
            self.edited_curves[i][0] = -1/(t*maxT)
        for i, w in enumerate(solution.x[len(self.edited_curves):]):
            self.approximated_weights.append(w)

        self.defaultButton.config(state="normal")
        self.fitButton.config(state="disabled")

        self.approxButton_pressed()

 




    def approximation_update(self, _):
        self.defaultButton.config(state="normal")
        sum = 0
        for w in self.w_vars:
            sum += round(w.get(),2)
            #print(round(w.get(),2))
        if(not (sum >= 1.0-0.02 and sum <= 1.0+0.02)):
            self.statuLabelVar_set(f"weights sum is not 1 ({round(sum,2)})")
            self.approxButton.config(state="disabled")
            return
        
        self.weights_approx = False
        self.approximated_weights = []
        for w in self.w_vars:
            self.approximated_weights.append(w.get())
        for i, t in enumerate(self.t_vars):
            self.edited_curves[i][0] = -1/t.get()

        self.statuLabelVar_set("parameters changed")
        self.approxButton.config(state="normal")

        self.approxButton_pressed()


    def update_edit(self):
        if(hasattr(self, "w_vars") and hasattr(self, "t_vars")):
            for i in range(len(self.w_vars)):
                self.w_vars[i].set(self.approximated_weights[i])
                self.t_vars[i].set(max(0, int(-1/self.edited_curves[i][0])))




    def add_approximation_edit(self):
        weightEditFrame = tk.Frame(self.editPanel.interior)
        timeEditFrame = tk.Frame(self.editPanel.interior)
        #weights
        self.w_vars = []
        for i, weight in enumerate(self.approximated_weights):
            label = tk.Label(weightEditFrame, text=f"W{len(self.approximated_weights)-i}", font=self.generalFont)
            w_var = tk.DoubleVar(weightEditFrame, weight)
            self.w_vars.append(w_var)
            slider = tk.Scale(weightEditFrame, from_=0.05, to=1, resolution=0.05, orient=tk.HORIZONTAL, length=100, variable=w_var, command=self.approximation_update)
            weightEditFrame.rowconfigure(i, minsize=50)
            label.grid(row=i, column=0, sticky=tk.S)
            slider.grid(row=i, column=1, sticky=tk.S)

        #times
        self.t_vars = []
        for i, params in enumerate(self.edited_curves):
            t = max(0, round((-1/params[0]),2))
            label = tk.Label(timeEditFrame, text=f"T{len(self.edited_curves)-i}", font=self.generalFont)
            t_var = tk.IntVar(timeEditFrame, int(t))
            self.t_vars.append(t_var)
            spin = tk.Spinbox(timeEditFrame, from_=1, to=t*10, increment=1000, textvariable=t_var, width=10, font=Font(size=12), command=lambda: self.approximation_update(None))
            spin.bind("<Return>", self.approximation_update)
            timeEditFrame.rowconfigure(i, minsize=50)
            label.grid(row=i, column=0, sticky=tk.S)
            spin.grid(row=i, column=1, sticky=tk.S)

        weightEditFrame.pack(side="left", anchor="center", padx=(300, 0))
        timeEditFrame.pack(side="right", anchor="center",padx=(0, 300))
        self.update()

    def delete_approximation_edit(self):
        for c in self.editPanel.interior.winfo_children()[1:]:#1st frame is a frame with buttons
                c.destroy()
        self.w_vars = []
        self.t_vars = []
        self.update()


    def chooseFileButton_pressed(self):
        path = filedialog.askopenfilename()
        self.read_file_data(path)
        
    
    def read_file_data(self, path):
        t = []
        y = []
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                data = line.split(" ")  
                #print(data)
                t.append(float(data[0]))
                if(len(data) < 3):
                    y.append(float(data[1]))
                else:
                    y.append(float(data[2]))
        y = np.array(y)
        # n = 30
        # y = np.convolve(y, np.ones(n) / n, mode='valid')
        # t = t[0:-n+1]
        y /= y[0]

        self.data = (t,y)
        self.resetButton_pressed()

app = NMR()
app.mainloop()