import tkinter as tk
import ttkbootstrap as ttk
from modules import timetable

from helpers.scraper_helpers import *
from helpers.gui_helpers import * # this is probably not a good practice but whatever

import webbrowser



class DefaultWindow(ttk.Window):

    TT_BACKGROUND_COLOR = "#FFFFFF"
    TT_FOREGROUND_COLOR = "#141414"

    DARK_MODE = True  # Default set to true (for me :D)
    DUMB_MODE = True
    _BROWSING_PROGRAM_INFO = False
    
    lock = False
    _required_courses = _selected_courses = []

    def __init__(self, *args, **kwargs):

        if self.DARK_MODE:
            super().__init__(themename="darkly")
            t = self.TT_BACKGROUND_COLOR
            self.TT_BACKGROUND_COLOR = self.TT_FOREGROUND_COLOR
            self.TT_FOREGROUND_COLOR = t
        else:
            super().__init__

        self.title('Course Registration Utility v0.3 "making proper APIs"')
        self.geometry()

        self.tt = timetable.Timetable()
        self._term_dict = get_current_terms()

        self.mainframe = ttk.Frame()
        self.mainframe.grid(column=0, row=0, sticky="NWES")
        
        self.fake_course = None

        bframe = self.setup_browser_frame()
        bframe.grid(column=0, row=0, sticky="NWS")
        self.setup_planner_frame().grid(column=1, row=0, sticky="NES")
        self.setup_timetable_frame().grid(column=0, row=1, columnspan=2)
        self.setup_private_frame().grid(column=0, row=2, sticky="NWES", columnspan=3)

        if self.DUMB_MODE:
            self.termValBox.current(2) # set to term 2 for easy operation

    def setup_browser_frame(self):

        browserFrame = ttk.LabelFrame(self.mainframe, text="Browser")

        # ROW_0 Choose Term
        v = tk.Label(browserFrame, text="Select term")
        v.grid(column=0, row=0, sticky="WN")
        self.selectedTerm = tk.StringVar()
        self.termValBox = ttk.Combobox(
            browserFrame,
            text=self.selectedTerm,
            values=list(self._term_dict.keys()),
            exportselection=False,
            width=27,
        )
        self.termValBox.grid(column=1, row=0, sticky="WN", columnspan=2)

        ttk.Button(
            browserFrame,
            text="Refetch from web",
            command=lambda: force_update_cache(self),
        ).grid(column=2, row=0, sticky="ES", padx=5, columnspan=2)

        # ROW_1 Choose course code
        v = tk.Label(browserFrame, text="Select course")
        v.grid(column=0, row=1, sticky="WNS")

        self.selectedFaculty = tk.StringVar()
        self.facultyValBox = ttk.Combobox(
            browserFrame,
            text=self.selectedFaculty,
            values=get_current_courses(),
            exportselection=False,
        )
        self.facultyValBox.grid(column=1, row=1, sticky="WNS")

        self.course_val = tk.StringVar()
        self.courseValBox = ttk.Combobox(
            browserFrame,
            text=self.course_val,
            values=["Placeholder"],
            height=10,
            width=20,
            exportselection=False,
            state="disabled",
        )
        self.courseValBox.grid(column=2, row=1, sticky="WNS", padx=5)

        self.sect_val = tk.StringVar()
        self.courseSectBox = ttk.Combobox(
            browserFrame,
            text=self.sect_val,
            values=["Select course first!"],
            height=10,
            width=20,
            exportselection=False,
            state="disabled",
        )
        self.courseSectBox.current(0)
        self.courseSectBox.grid(column=3, row=1, sticky="WNS", padx=5)

        # ROW_2 details
        self.detailFrame = ttk.Frame(browserFrame)
        courseLabel = ttk.Label(self.detailFrame, text="Waiting for input...")
        courseLabel.grid(column=0, row=0, sticky="NW", columnspan=4)

        self.toggleBrowserTimetable = tk.BooleanVar(browserFrame)

        experimental_toggle_button = ttk.Checkbutton(
            browserFrame, text='Show in timetable', variable=self.toggleBrowserTimetable, offvalue=False, onvalue=True, 
            # do 2 things at once
            command=lambda: draw_timetable(self, self._required_courses, self._selected_courses) or update_browser_label(event=None, main_window=self)
        )
        experimental_toggle_button.state(["!alternate"])
        experimental_toggle_button.grid(column=3, row=2, sticky='EN')

        self.detailFrame.grid(column=0, row=2, columnspan=5, sticky="WES")

        # Bind events
        self.facultyValBox.bind("<<ComboboxSelected>>", self.facultyComboboxOnChange)
        self.courseValBox.bind("<<ComboboxSelected>>", update_sections)
        self.courseSectBox.bind("<<ComboboxSelected>>", update_browser_label)
        
        #Row_3 link to details
        self.outlineButton = ttk.Button(browserFrame, text="Open Outline", command=lambda:webbrowser.open(f"https://cucampus.one/courses/{self.facultyValBox.get()}{self.courseValBox.get()}"))
        self.outlineButton.grid(column=0, row=3, sticky="WN")
        
        return browserFrame

    def setup_planner_frame(self):
        plannerFrame = ttk.LabelFrame(self.mainframe, text="Planner")

        # Column 0 & 1: Course input Textbox
        v = tk.Label(plannerFrame, text="Pre-assigned")
        v.grid(column=0, row=0, sticky="N")

        self.preassignedTextField = tk.Text(plannerFrame, width=15, height=7)
        self.preassignedTextField.grid(column=0, row=1, sticky="WN", rowspan=7)

        v = tk.Label(plannerFrame, text="Preferred")
        v.grid(column=1, row=0, sticky="N")

        self.preferredTextField = tk.Text(plannerFrame, width=15, height=7)
        self.preferredTextField.grid(column=1, row=1, sticky="WN", rowspan=7)

        self.processButton = ttk.Button(
            plannerFrame, text="Process All", command=lambda: update_all(self)
        )
        self.processButton.grid(column=0, row=8, sticky="W")

        # Column 2: preferences
        # v = tk.Label(plannerFrame, text="Preferences")
        # v.grid(column=2, row=0, sticky="W")

        # self.checkbox1 = ttk.Checkbutton(plannerFrame, text="Enable Feature", state=1)
        # self.checkbox2 = ttk.Checkbutton(plannerFrame, text="Enable Feature", state=1)
        # self.checkbox3 = ttk.Checkbutton(plannerFrame, text="Enable Feature", state=1)
        # self.checkbox4 = ttk.Checkbutton(plannerFrame, text="Enable Feature", state=1)
        # self.checkbox1.state(["!alternate"])
        # self.checkbox2.state(["!alternate"])
        # self.checkbox3.state(["!alternate"])
        # self.checkbox4.state(["!alternate"])
        # self.checkbox1.grid(column=2, row=1)
        # self.checkbox2.grid(column=2, row=2)
        # self.checkbox3.grid(column=2, row=3)
        # self.checkbox4.grid(column=2, row=4)

        return plannerFrame

    def setup_timetable_frame(self):
        self.ttFrame = timetableFrame = tk.LabelFrame(self.mainframe, text="timetable")

        draw_timetable(self, [], [])

        return timetableFrame
    
    def setup_private_frame(self):
        private_frame = ttk.Frame(self.mainframe)
        self.privateTimeButton = ttk.Button(
            private_frame, text="Add Private Time", command=lambda: add_private_time(self)
        )
        self.privateTimeButton.grid(column=0, row=0, sticky="W")
        b = ttk.Button(
            private_frame, text="Browse program information", command=lambda: spawnProgramBrowser(self)
        )
        b.grid(column=1, row=0, sticky="W", padx=5)

        self.credit_label = ttk.Label(private_frame, text='Current credits: 0', font=('Segoe UI', 12), foreground=evaluateCreditSum(0))
        self.credit_label.grid(column=2, row=0, sticky='E')
        private_frame.columnconfigure(2, weight=1) # Allocate all extra space to column 2 to align credit label to E.
        return private_frame

    def facultyComboboxOnChange(self, event):
        """Delay lookup search to allow for scrolling."""
        self.after(1000, update_courses, self.selectedFaculty.get(), self)

    def temp(self):
        pass


if __name__ == "__main__":
    default = DefaultWindow()
    default.mainloop()
