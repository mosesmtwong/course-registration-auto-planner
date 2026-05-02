import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from modules.course import *
from helpers.base_gui_helpers import make_timetable_frame
import re

class BaseConfigurationWindow(tk.Toplevel):

    optionFrame = None

    def __init__(self, master):
        super().__init__(master=master)

    def onListUpdate(self, event):
        output = ''
        for listbox in self.optionFrame.children:
            key = listbox
            if (type(self.optionFrame.children[listbox])) == tk.Listbox:
                listbox = self.optionFrame.children[listbox]
                index = listbox.curselection()[0]
                item = listbox.get(index)
                if item == 'None': item = None
                lookupList = [i.id for i in self.cv[key].values()]
                comp = list(self.cv[key].values())[lookupList.index(item)]
                output += comp.summary() + '\n'

        self.outLabel['text'] = output

    def genString(self, componentData: CourseComponent):
        return f'{componentData.id if componentData.id != "None" else "Default"}'

    def generateFilteredCourse(self):
        t = FilteredCourse(self.course.course_name)
        components = []
        for listbox in self.optionFrame.children:
            key = listbox
            if (type(self.optionFrame.children[listbox])) == tk.Listbox:
                listbox = self.optionFrame.children[listbox]
                index = listbox.curselection()[0]
                item = listbox.get(index)
                if item == 'None': item = None
                lookupList = [i.id for i in self.cv[key].values()]
                comp = list(self.cv[key].values())[lookupList.index(item)]
                # print(comp)
                components.append(comp)
        t.components = components
        t.title = self.course.title 
        t.credit = self.course.credit
        return t

class CourseConfigurationWindow(BaseConfigurationWindow):

    '''Should be called by DefaultWindow as master. 
    So, the values of DefaultWindow shall be accessed directly.'''
    def __init__(self, master:tk.Tk=None, course:Course=None, section:str=None):
        
        super().__init__(master=master)
        self.master = master
        self.title("Configure course")
        self.grab_set()
        self.course = course
        self.section = section
        self.coursev = course.course_name
        self.optionFrame = ttk.LabelFrame(self, text="Options: ")

        # Swap to dynamic generation
        courseVariables = vars(course)
        self.cv = courseVariables
        col = 0

        components = course.getComponentsBySection(section)
        for key in courseVariables:
            if type(courseVariables[key]) == dict and courseVariables[key]:
                # Then it is a thing we'd like to insert
                comp = courseVariables[key]
                compList = list(comp.values())
                clist = [self.genString(i) for i in compList if i in components]
                bgcolors = ['red' if self.master.tt.check_component_for_conflicts(component) else ('red' if component.availability[0] == 0 else 'green') 
                            for component in components 
                            if component.type == key.upper()]
                selectcolors = ['#A00808' if self.master.tt.check_component_for_conflicts(component) 
                                else ('#A00808' if component.availability[0] == 0 else '#10A010')
                                for component in components
                                if component.type == key.upper()]
                listboxwidget = tk.Listbox(self.optionFrame, exportselection=0, name=key)
                listboxwidget.insert(tk.END, *clist)
                for c in range(len(bgcolors)):
                    listboxwidget.itemconfig(c, bg=bgcolors[c], selectbackground=selectcolors[c])
                listboxwidget.grid(row=1, column=col)
                listboxwidget.bind("<<ListboxSelect>>", self.onListUpdate)
                listboxwidget.select_set(0)

                ttk.Label(self.optionFrame, text=compList[0].map[key.upper()]).grid(row=0, column=col)
                col += 1

        self.optionFrame.grid(row=0, column=0, columnspan=3, sticky='WE')

        self.deleteButton = ttk.Button(self, text="Cancel", command=self.destroy)
        self.confirmButton = ttk.Button(self, text='Confirm', command=self.add_to_clist)

        outFrame = ttk.LabelFrame(self, text="Current Selection")
        self.outLabel = ttk.Label(outFrame)
        self.outLabel.grid(row=0, column=0)
        outFrame.grid(row=1, column=0, sticky='WE')

        self.deleteButton.grid(row=1, column=1, sticky='S')
        self.confirmButton.grid(row=1, column=2, sticky='S')

        self.onListUpdate('foo')

    def add_to_clist(self):
        t = self.generateFilteredCourse()
        for component in t.components:
            if self.master.tt.check_component_for_conflicts(component):
                print("Occupied!")
                return tk.messagebox.showerror("Oh no", "Conflicts found!")
            if component.availability[0] == 0:
                return tk.messagebox.showerror("You reg too slow", "No more slots left :(")
        self.master.selectedCourseList.append(t)
        self.master.courseListbox.insert(tk.END, f'{self.coursev}-{self.section}' if self.section else f'{self.coursev}')
        print(self.master.selectedCourseList)
        self.master.updateTimetablePreview()
        self.master.tt.load_selection(t)
        self.destroy()

class PreassignedConfigWindow(BaseConfigurationWindow): 
    finish = False 

    def __init__(self, master, course: Course, section: str, filtered_preassigned_list: list):
        '''
        ### Args:
            master (DefaultWindow)
            course (Course): Course object
            section (str): section code (str)
            filtered_preassigned_list (list): list (will be modified)
        '''
        # scode is section code. e.g. A, B, C.
        # section is the numbers behind scode
        super().__init__(master=master)

        # l = re.split(r'[A-Z]\d+', section, maxsplit=1)
        if section:
            if re.search(r'^[A-Z]\d', section): # Matching T01 etc.
                self.scode = None
                self.section = section
            elif re.search(r"[A-Z]+\d", section): # [A-Z]: Uppercase letters. +: One or more. \d: Section code. Matching AT01 etc.
                self.scode = section[0]
                self.section = section[1:]
            elif re.search(r"^[A-Z]{1,2}$", section): # ^: Any. [A-Z]: Uppercase letters, from A-Z. {1,2}: One to two matches. $: Terminator.
                self.scode = section
                self.section = None 
            else:
                self.scode = self.section = None
        else:
            self.scode = self.section = None

        self.master = master
        self.title("Configure preassigned course details")
        self.grab_set()
        self.course = course
        # self.section = section 
        self.coursev = course.course_name
        self.optionFrame = ttk.LabelFrame(self, text=f"Options for {self.coursev}: ")
        # this list needs to be kept in memory since we dont know when the user will invoke the button function
        self.filtered_preassigned_list = filtered_preassigned_list 

        # Swap to dynamic generation
        courseVariables = vars(course)
        self.cv = courseVariables
        col = 0

        components = course.getComponentsBySection(self.scode)
        MAX_SIZE = -1
        for key in courseVariables:
            if type(courseVariables[key]) == dict and courseVariables[key]:
                # Then it is a thing we'd like to insert
                comp = courseVariables[key]
                compList = list(comp.values())
                # check that this component is indeed in this section
                clist = [self.genString(i) for i in compList if (i in components and self.sessionCheck(i))]
                print(f'Clist = {clist}')
                listboxwidget = tk.Listbox(self.optionFrame, exportselection=0, name=key)
                listboxwidget.insert(tk.END, *clist)
                listboxwidget.grid(row=1, column=col)
                listboxwidget.bind("<<ListboxSelect>>", self.onListUpdate)
                listboxwidget.select_set(0)
                MAX_SIZE = max(len(clist), MAX_SIZE)
                ttk.Label(self.optionFrame, text=compList[0].map[key.upper()]).grid(row=0, column=col)
                col += 1

        self.optionFrame.grid(row=0, column=0, columnspan=3, sticky='WE')

        if MAX_SIZE == 1 and MAX_SIZE > 0:
            print(f"Fast-assigned {self.coursev}")
            self.add_to_plist()
            self.finish = True
            self.destroy()
            return
        
        self.deleteButton = ttk.Button(self, text="Cancel", command=self.destroy)
        self.confirmButton = ttk.Button(self, text='Confirm', command=self.add_to_plist)

        outFrame = ttk.LabelFrame(self, text="Current Selection")
        self.outLabel = ttk.Label(outFrame)
        self.outLabel.grid(row=0, column=0)
        outFrame.grid(row=1, column=0, sticky='WE')

        self.deleteButton.grid(row=1, column=1, sticky='S')
        self.confirmButton.grid(row=1, column=2, sticky='S')

        self.onListUpdate('foo')

    def add_to_plist(self):
        try:
            t = self.generateFilteredCourse()
        except Exception as ex:
            print(f'{ex} has occured :((')
            tk.messagebox.showerror("wtf bro","You fake me, there is no such course?!",)
            return self.destroy()
        # self.master.preAssignedListbox.insert(tk.END, f'{self.coursev}-{self.scode}' if self.scode else f'{self.coursev}')
        self.filtered_preassigned_list.append(t)
        t.finish = True
        return self.destroy()

    def sessionCheck(self, arg:CourseComponent):
        if not self.section or not arg.id:
            return True
        # print(arg.id, self.section, self.scode)
        if arg.id == self.section or arg.id == self.scode:
            return True
        # print(re.findall(r'\d+', arg.id), re.findall(r'\d+', self.section))
        # Final resort: check if the numbers of the component are equal
        return re.findall(r'\d+', arg.id) == re.findall(r'\d+', self.section)
    
class ConflictResolverWindow(tk.Toplevel):

    def __init__(self, master, comp_list, *args, **kwargs):
        '''comp_list should be scored_courses processed by the api.
        '''
        super().__init__(master=master, *args, **kwargs)
        self.comp_list = comp_list
        self.finish = False 
        self.crs_idx = None

        self.drawUI()
        self.title("Finalize selection")

    def getSelectedPair(self):
        '''RETURNS: User-chosen pair.
        '''
        v = self.comp_list[self.crs_idx]
        return v


    def generateComponentString(self, comps: list[CourseComponent]) -> str:
        '''GENERATES a string that can present the conflicts of a course in human-readable format.'''
        return ('\n').join([comp.summary() for comp in comps])

    def generateConflictString(self, conflicts: list[CourseComponent]) -> str:
        '''GENERATES a string that can present the conflicts of a course in human-readable format.'''
        return (f'{len(conflicts)} conflicts found: \n' if conflicts else '') + ('\n').join([f'Conflicts with {comp.courseNumber}{comp.id}' for comp in conflicts])

    def updateLabel(self, ev: tk.Event):
        # do something...
        # box = ev.widget 
        box = self.pair_lb
        index = box.curselection()[0] # selectionmode = SINGLE

        cur_comps, conflict_info = self.comp_list[index][:-1], self.comp_list[index][-1]
        
        self.outLabel['text'] = self.generateComponentString(cur_comps) 

        self.conflictsLabel['text'] = self.generateConflictString(conflict_info)
        self.conflictsLabel['foreground'] = '#ce2727'
    
    def _finish_select(self):
        self.finish = True
        self.crs_idx = self.pair_lb.curselection()[0]
        return self.destroy()

    def _abort(self):
        self.finish = True 
        return self.destroy()

    def drawUI(self):

        selectionFrame = ttk.LabelFrame(self, text='Available choices', name = 'sframe')
        pair_listbox = tk.Listbox(selectionFrame, exportselection=0, selectmode='single', name='pair_lb')
        pair_listbox.grid(row=0, column=0)
        pair_listbox.bind("<<ListboxSelect>>", self.updateLabel)
        pair_listbox.select_set(0)
        selectionFrame.grid(row=0, column=0, sticky='NWE')

        outFrame = ttk.LabelFrame(self, text="Info for pair")
        self.outLabel = ttk.Label(outFrame)
        self.outLabel.grid(row=0, column=0,sticky='W')

        self.conflictsLabel = ttk.Label(outFrame)
        self.conflictsLabel.grid(row=1, column=0, sticky='W')
        outFrame.grid(row=0, column=1, sticky='WE')

        self.deleteButton = ttk.Button(self, text="Abort", command=self._abort)
        self.confirmButton = ttk.Button(self, text='Confirm', command=self._finish_select)
        self.deleteButton.grid(row=1, column=2, sticky='S')
        self.confirmButton.grid(row=1, column=3, sticky='S')

        MAX = 1
        confs = []
        # listbox containing all possible pair
        for l in self.comp_list:
            comps = l[:-1]
            conflicts = l[-1]
            comp_represent_string = comps[0].courseNumber + ('-').join([c.id if c.id else '' for c in comps]) + f' [{comps[0].language}]'
            pair_listbox.insert(tk.END, comp_represent_string)

            if len(conflicts) > MAX:
                MAX = len(conflicts)
            confs.append(conflicts)

        for conflict_idx in range(len(confs)):
            conflict_l = confs[conflict_idx]
            ratio = len(conflict_l) / MAX 
            R = ratio * 255
            G = (1-ratio) * 255
            B = 0
            R,G = int(R), int(G)
            SR, SG = R - 20 if R - 50 > 0 else 0, G - 20 if G - 50 > 0 else 0
            bgcolor = f'#{R:02x}{G:02x}{B:02x}'
            selectcolor = f'#{SR:02x}{SG:02x}{B:02x}'

            pair_listbox.itemconfig(conflict_idx, bg=bgcolor, selectbackground=selectcolor)

        pair_listbox.select_set(0)
        self.grab_set()
        self.pair_lb = pair_listbox
        self.updateLabel('a')

class TopNSelectionWindow(tk.Toplevel):
    '''Your good friend is very lazy so this is basically just a refactoring of ConflictResolverWindow
    Except now there's a timetable preview
    '''

    def __init__(self, master, preassigned_list, results, *args, **kwargs):
        '''comp_list should be scored_courses processed by the api.
        '''
        super().__init__(master=master, *args, **kwargs)
        self.preassigned_list = preassigned_list
        self.selection_choices = results
        self.finish = False 
        self.sel_idx = None

        self.drawUI()
        self.title("Finalize selection")

    def getSelectedPair(self):
        '''RETURNS: User-chosen pair.
        '''
        v = self.comp_list[self.crs_idx]
        return v

    def generateScoreAndReprString(self, idx):
        '''
        `idx`: index of selection  
        Score is calculated by the following: `no_of_choices` + `priority_sum` + `RNG`
        '''
        score = self.selection_choices[idx][0][0] + self.selection_choices[idx][0][1] + self.selection_choices[idx][0][2]
        return round(score, 3), f'Choice {idx+1} - Score: {score}'

    def generateComponentString(self, comps: list[CourseComponent]) -> str:
        '''GENERATES a string that can present the conflicts of a course in human-readable format.'''
        return ('\n').join([comp.summary() for comp in comps])

    def generateConflictString(self, conflicts: list[CourseComponent]) -> str:
        '''GENERATES a string that can present the conflicts of a course in human-readable format.'''
        return (f'{len(conflicts)} conflicts found: \n' if conflicts else '') + ('\n').join([f'Conflicts with {comp.courseNumber}{comp.id}' for comp in conflicts])

    def updateLabel(self, ev: tk.Event):
        '''Update the window when listbox selected'''
        # do something...
        # box = ev.widget 
        box = self.pair_lb
        index = box.curselection()[0] # selectionmode = SINGLE

        _, fcourses = self.selection_choices[index]
        self.ttFrame = make_timetable_frame(self.ttFrame, self.preassigned_list, fcourses)
        self.ttFrame.grid(row=2, column=0, sticky='S', columnspan=4)
        
        # you don't need to know how i make this
        self.outLabel['text'] = ('\n\n').join([course.course_name + '\n' + ('\n').join([comp.summary() for comp in course.components]) for course in fcourses])

        self.conflictsLabel['foreground'] = '#ce2727'
    
    def _finish_select(self):
        self.finish = True
        self.sel_idx = self.pair_lb.curselection()[0]
        return self.destroy()

    def _abort(self):
        self.finish = True 
        return self.destroy()

    def drawUI(self):

        mainFrame = ttk.Frame(self)
        mainFrame.grid(row=0, column=0)

        displayFrame = ttk.Frame(mainFrame)
        selectionFrame = ttk.LabelFrame(displayFrame, text='Available choices', name = 'sframe')
        pair_listbox = tk.Listbox(selectionFrame, exportselection=0, selectmode='single', name='pair_lb')
        pair_listbox.grid(row=0, column=0)
        pair_listbox.bind("<<ListboxSelect>>", self.updateLabel)
        pair_listbox.select_set(0)
        selectionFrame.grid(row=0, column=0, sticky='NWE')
        outFrame = ttk.LabelFrame(displayFrame, text="Info for pair")
        self.outLabel = ttk.Label(outFrame)
        self.outLabel.grid(row=0, column=0,sticky='W')

        self.conflictsLabel = ttk.Label(outFrame)
        self.conflictsLabel.grid(row=1, column=0, sticky='WE')
        outFrame.grid(row=0, column=1, sticky='WE')
        displayFrame.grid(row=0, column=0, columnspan=3,sticky='NWE')
        displayFrame.columnconfigure(1, weight=1) # allocate all extra space to outFrame

        self.ttFrame = ttk.LabelFrame(mainFrame, text='Proposed timetable')
        self.ttFrame.grid(row=1, column=0, sticky='')
        self.ttFrame = make_timetable_frame(self.ttFrame)

        buttonFrame = ttk.Frame(self)
        self.deleteButton = ttk.Button(buttonFrame, text="Abort", command=self._abort)
        self.confirmButton = ttk.Button(buttonFrame, text='Confirm', command=self._finish_select)
        self.deleteButton.grid(row=0, column=0, sticky='SE')
        self.confirmButton.grid(row=0, column=1, sticky='SE', padx=5)
        buttonFrame.columnconfigure(0, weight=1)
        buttonFrame.grid(row=2, column=0, sticky='NEWS')

        MAX = 1
        scores = []
        # listbox containing all possible pair
        for i in range(len(self.selection_choices)):
            
            score, comp_represent_string = self.generateScoreAndReprString(i)
            pair_listbox.insert(tk.END, comp_represent_string)

            if score > MAX:
                MAX = score
            scores.append(score)

        for score_idx in range(len(scores)):
            ratio = scores[score_idx] / MAX 
            R = (1-ratio) * 255
            G = ratio * 255
            B = 0
            R,G = int(R), int(G)
            SR, SG = R - 20 if R - 50 > 0 else 0, G - 20 if G - 50 > 0 else 0
            bgcolor = f'#{R:02x}{G:02x}{B:02x}'
            selectcolor = f'#{SR:02x}{SG:02x}{B:02x}'

            pair_listbox.itemconfig(score_idx, bg=bgcolor, selectbackground=selectcolor)

        pair_listbox.select_set(0)
        self.pair_lb = pair_listbox


        self.grab_set()
        self.updateLabel('a')