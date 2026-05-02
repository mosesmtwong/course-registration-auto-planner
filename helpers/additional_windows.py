
import tkinter as tk
from tkinter import ttk
import webbrowser, os
from modules.course import *
from api import process_programs
   
class AddPrivateTimeWindow(tk.Toplevel):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)
        self.finish = False
        self.ROWS = 10
        self.COLS = 5
        self.weekdayMap = {
            "Mo": "Monday",
            "Tu": "Tuesday",
            "We": "Wednesday",
            "Th": "Thursday",
            "Fr": "Friday", # are you really gonna study on saturday or sunday?
        }     
        self.drawUI()
        self.grab_set()
        self.title("Configure private time/unavailable timeslots")
        
    def get_coordinate(self, row, column):
        return self.checkbox_matrix[row][column].state()==('selected',)
    
    def store_periods(self):
        def check_AM(slot):
            if slot < 4:
                return "AM"
            else:
                return "PM"
        self.periods = []
        for col, day in enumerate(self.weekdayMap.keys()):
            i=0
            j=0
            while True:
                if i == self.ROWS or j == self.ROWS:
                    break
                if self.get_coordinate(i, col):
                    j=i
                    while self.get_coordinate(j, col):
                        j += 1
                        if j == self.ROWS:
                            break
                    self.periods.append(f"{day} {i+8:02}:30{check_AM(i)} - {j-1+9:02}:15{check_AM(j)}")
                    i=j
                else:
                    i += 1
        self.finish = True
        return self.destroy()
    
    def get_fake_course(self):
        """
        WHY WOULD YOU RETURN A LIST OF A FAKE COURSE????
        Returns:
            FilteredCourse: list of a fake course with unavailable timeslot
        """
        if self.periods != []:
            self.private_comp = CourseComponent("LEC", None)
            self.private_comp.periods = self.periods
            self.private_course = FilteredCourse("Private Time")
            self.private_course.components = [self.private_comp]
            return self.private_course
        else:
            return 

    def drawUI(self):      
        # header row
        e = tk.Entry(self, justify='center', width=12)
        e.insert(tk.END, 'Timeslot')
        e.config(state='disabled', disabledbackground='#141414', disabledforeground='#FFFFFF')
        e.grid(row=0, column=0)
        c=1
        for day in self.weekdayMap:
            e = tk.Entry(self, justify='center', width=5)
            e.grid(row=0, column=c)
            e.insert(tk.END, day)
            e.config(state='disabled', disabledbackground='#141414', disabledforeground='#FFFFFF')
            c+=1
        # header column
        for slot in range(self.ROWS):
            e = tk.Entry(self, justify='center', width=12)
            e.grid(row=slot+1, column=0)
            e.insert(tk.END, f'{slot+8:02}:30 - {slot+9:02}:15')
            e.config(state='disabled', disabledbackground='#141414', disabledforeground='#FFFFFF')
        
        # checkbox matrix
        self.checkbox_matrix = []
        for row in range(self.ROWS):
            checkbox_row = []
            for col in range(self.COLS):
                b = ttk.Checkbutton(self)
                b.state(["!alternate"])
                b.grid(column=col+1, row=row+1)
                checkbox_row.append(b)
            self.checkbox_matrix.append(checkbox_row)
            
        self.confirmButton = ttk.Button(
            self, text="Confirm", command=lambda: self.store_periods()
        )
        self.confirmButton.grid(column=0, row=12, sticky="W", columnspan=2)

class ProgramInfoBrowser(tk.Toplevel):

    def __init__(self, master, *args, **kwargs):
        self.master = master
        super().__init__(master, *args, **kwargs)
        master._BROWSING_PROGRAM_INFO = True
        self.setup_UI()

    def setup_UI(self):

        self.title("Browse program information (abridged)")
        fr = tk.LabelFrame(self, text='Query parameters')
        # yes, hard code makes it run faster, so i'm doing this
        l = [str(i) for i in range(2010, 2026)]
        l.reverse()
        year_combobox = ttk.Combobox(fr, values=l) # TODO: Update year range automatically
        year_combobox.grid(row=0, column=0,sticky='WE')
        
        year_combobox.current(1)
        self.year_v = l[1]

        self.query_field = ttk.Entry(fr, exportselection=0)
        self.query_field.grid(row=1, column=0, columnspan=2, sticky='WE')
        
        process_button = ttk.Button(fr, text='Search', command=self._get_info)
        process_button.grid(row=0, column=1, sticky='WE')
        fr.grid(row=0, column=0, sticky='NWE')

        fr2 = tk.LabelFrame(self, text='Program info')
        self.detail_combobox = ttk.Combobox(fr2)
        self.detail_combobox.grid(row=0, column=0, sticky='NWE')
        b = ttk.Button(fr2, text='Failsafe: Open in browser', command=self._launch_browser)
        b.grid(row=0, column=1, sticky='E')
        self.programInfoView = ttk.Treeview(fr2)
        self.programInfoView.insert("", "end", "0", text='Query first!')
        self.programInfoView.grid(row=1, column=0,sticky='NWSE',columnspan=2)
        self.outputLabel = ttk.Label(fr2, text='Waiting for input...')
        self.outputLabel.grid(row=2, column=0, sticky='NWSE',columnspan=2)
        fr2.grid(row=1, column=0, sticky='SWE')

        year_combobox.bind('<<ComboboxSelected>>', self.update_year)
        self.detail_combobox.bind('<<ComboboxSelected>>', self.update_treeview)
        self.programInfoView.bind("<<TreeviewSelect>>", self.update_label)

    def _get_info(self):

        year = self.year_v
        query_input = self.query_field.get()
        major_details = process_programs(year, query_input)
        if major_details == -1:
            self.outputLabel['text'] = 'No record found!'
            return 
        major_details, minor_details, src = major_details
        self.detail_combobox['values'] = [f'Major #{i}' for i in range(len(major_details))] + [f'Minor #{i}' for i in range(len(minor_details))]
        self.major_d = major_details 
        self.minor_d = minor_details
        self.html_data = src
        try:
            self.detail_combobox.current(0)
        except Exception as ex:
            print(f'Exception {ex} has occured.')
            self.outputLabel['text'] = 'An exception has occured! Maybe retry or use the failsafe button?'
            return
        self.update_treeview(w=self.detail_combobox)

    def update_year(self, event):
        self.year_v = event.widget.get()

    def update_treeview(self, event=None, w=None):
        '''Update the treeview to reflect info.'''
        if event:
            cur_selection = event.widget.get()
        elif w:
            cur_selection = w.get()
        select = cur_selection.split()[0]
        idx = int(cur_selection.split()[1].strip('#'))
        self.selected_major = idx
        self.programInfoView.delete(*self.programInfoView.get_children())

        if select == 'Major':
            data = self.major_d[idx]
            for idx, year in enumerate(data):
                self.insert_year_data(idx+1, year)

        if select == 'Minor':
            data = self.minor_d[idx]

    def insert_year_data(self, id, year_d):
        item = self.programInfoView.insert('', 'end', f'y{id}', text=f'Year {id}') # insert at root
        for term_idx, term_data in enumerate(year_d):
            term_itm = self.programInfoView.insert(item, 'end', f'y{id}_t{term_idx}', text=f'Term {term_idx+1}')
            if len(term_data) == 1:
                txt = term_data[0].strip('Major 1\n')
                self.programInfoView.insert(term_itm, 'end', f'y{id}_t{term_idx}_m0', text='Major 1')
                continue 
            for n, major_str in enumerate(term_data):
                self.programInfoView.insert(term_itm, 'end', f'y{id}_t{term_idx}_m{n}', text=f'Major {n+1}')

    def update_label(self, event):
        id = event.widget.selection()[0]
        lookup_values = id.split('_')
        if len(lookup_values) != 3:
            # just secondary stuff, no need to care
            self.outputLabel['text'] = 'Select a term!'
            return 
        y_idx = int(lookup_values[0].strip('y')) - 1
        t_idx = int(lookup_values[1].strip('t'))
        m_idx = int(lookup_values[2].strip('m'))
        major_str = self.major_d[self.selected_major][y_idx][t_idx][m_idx]
        self.outputLabel['text'] = major_str.replace(f"Major {m_idx + 1}\n",'')

    def _launch_browser(self):

        path = os.path.abspath('temp/temp.html')
        url = 'file://' + path

        with open(path, 'w') as f:
            f.write(self.html_data)
        webbrowser.open(url)

# setup alias
ProgramInfoBrowserWindow = ProgramInfoBrowser