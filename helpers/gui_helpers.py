# Helpers specifically for DefaultWindow.
# If you want to use these functions elsewhere please make a wrapper for them here
# and make the base function in base_gui_helpers.py

from gui import DefaultWindow
import tkinter as tk
import ttkbootstrap as ttk
from helpers.scraper_helpers import *
from modules.timetable import Timetable
import api
from helpers.additional_windows import AddPrivateTimeWindow, ProgramInfoBrowser
from helpers.config_windows import TopNSelectionWindow, PreassignedConfigWindow
from helpers.base_gui_helpers import *

def getSelectedTerm(dw: DefaultWindow):

    return dw._term_dict[dw.selectedTerm.get()]

def update_courses(faculty: str, gui_object: DefaultWindow):
    """Only courses should be updated when the faculty changes.

    Args:
        faculty (str): Faculty selection 1s/1000ms ago.
        gui_object (DefaultWindow): The main GUI window object.
    """

    if not gui_object.selectedFaculty.get() == faculty or gui_object.lock:
        return
    current_term = getSelectedTerm(gui_object)

    print(current_term, faculty)

    # empty and lock comboboxes
    gui_object.courseValBox.set("")
    gui_object.courseSectBox.set("")
    
    gui_object.lock = True
    gui_object.courseValBox["state"] = "disabled"
    gui_object.courseSectBox["state"] = "disabled"

    # get data of selected term and faculty
    try:
        course_list = cached_lookup(current_term, faculty)
    except Exception as ex:
        print(f'{ex} occured in updating cache.')
        gui_object.lock = False # unlock to prevent locking us in !!!
        return 
    gui_object.courseValBox["values"] = list(split_courses(course_list).keys())
    gui_object._course_list = course_list

    gui_object.courseValBox["state"] = "enabled"
    gui_object.courseSectBox["state"] = "enabled"

    gui_object.courseValBox.current(0)
    update_sections(None, gui_object)

    gui_object.lock = False

def update_sections(event: tk.Event, main_window: DefaultWindow = None):
    """Internal function, responds to changes in courseValBox

    Args:
        event (tk.Event): set to None when passing DefaultWindow.
        main_window (DefaultWindow): pass the DefaultWindow from gui. Remember to set event to None when using this option.
    """
    # no override (call from event)
    if event:
        assert not main_window
        gui_object = event.widget.winfo_toplevel()
        widget = event.widget

    # override (call from internal funcs)
    elif main_window:
        assert not event
        gui_object = main_window
        widget = gui_object.courseValBox

    # not supposed to happen
    else:
        raise Exception("An unexpected case has occured.")

    # overrided (call from other functions)
    courses = split_courses(gui_object._course_list)

    gui_object.courseSectBox["values"] = courses[widget.get()]
    if not gui_object.courseSectBox["values"]:
        gui_object.courseSectBox["values"] = ["None"]
    gui_object.courseSectBox.current(0)

    update_browser_label(None, gui_object)


def update_browser_label(event: tk.Event, main_window: DefaultWindow = None):
    """For updating the label to display relevant session information.

    Args:
        event (tk.Event): set to None when passing DefaultWindow.
        main_window (DefaultWindow): pass the DefaultWindow from gui. Remember to set event to None when using this option.
    """
    # no override (call from event)
    if event:
        assert not main_window
        gui_object = event.widget.winfo_toplevel()
        widget = event.widget

    # override (call from internal funcs)
    elif main_window:
        assert not event
        gui_object = main_window
        widget = gui_object.courseValBox

    # not supposed to happen
    else:
        raise Exception("An unexpected case has occured.")

    cur_faculty = gui_object.selectedFaculty.get()
    cur_course = gui_object.course_val.get()
    cur_section = gui_object.sect_val.get()

    course_index = list(split_courses(gui_object._course_list).keys()).index(cur_course)
    courseObject = gui_object._course_list[course_index]
    components = courseObject.getComponentsBySection(cur_section)

    labeltext = f"{cur_faculty}{cur_course}{cur_section if cur_section != 'None' else ''} 「{courseObject.title}」 [{courseObject.credit}c]"

    for child in gui_object.detailFrame.winfo_children():
        child.destroy()

    courseLabel = ttk.Label(gui_object.detailFrame, text=labeltext)
    courseLabel.grid(column=0, row=0, sticky="NW")

    if gui_object.toggleBrowserTimetable.get():
        draw_timetable(gui_object, gui_object._required_courses, gui_object._selected_courses)

    index = 1
    for component in components:
        component.courseNumber = courseObject.course_name
        # component = course[i]
        available = ""

        # i love SPAGHET TI !!!!!!!!!!1
        foreground = (lambda i: ("#10ee10" if i[0] > i[1] * 2 / 3 else ("#cece34" if i[0] > i[1] / 4 else "#eeba25")))(component.availability)
        if gui_object.tt.check_component_for_conflicts(component):
            available = "\nTime conflict with existing classes!"
            foreground = "#ce2727"
        if component.availability[0] == 0:
            available += "\nClass is full!"
            foreground = "#ce2727"
        
        ttk.Label(
            gui_object.detailFrame,
            text=component.summary() + available,
            foreground=foreground,
        ).grid(column=0, row=index, sticky="NW")
        index += 1

        if gui_object.toggleBrowserTimetable.get(): # implement later.
            displayComponentInTimetable(gui_object, component)

    if not components:
        ttk.Label(gui_object.detailFrame, text="NO DATA", foreground="#ce2727").grid(
            column=0, row=1, sticky="NW"
        )


def force_update_cache(gui_object: DefaultWindow):

    faculty = gui_object.selectedFaculty.get()
    term = getSelectedTerm(gui_object)

    gui_object.courseValBox.set("")
    gui_object.courseSectBox.set("")

    gui_object.courseValBox["state"] = "disabled"
    gui_object.courseSectBox["state"] = "disabled"
    course_list = lookup(faculty, term)

    # Update cache
    cache_faculty(term, faculty, course_list)

    # Let the functions process the updated data
    update_courses(faculty, gui_object)

def draw_timetable(gui_object: DefaultWindow, preassigned: list[FilteredCourse] = [], selected: list[FilteredCourse] = []):
    '''Wrapper function for main GUI.  
    Initializes the timetable GUI, given a list of preassigned courses and selected courses.  
    WARNING: THIS FUNCTION IS LAGGY! DO NOT CALL RANDOMLY!

    Args:
        gui_object (DefaultWindow): The main object
        preassigned (list[FilteredCourse], optional): If not given, assume no courses
        selected (list[FilteredCourse], optional): If not given, assume no courses
    '''

    ttFrame = make_timetable_frame(gui_object.ttFrame, preassigned, selected)
    gui_object.ttFrame = ttFrame

def displayComponentInTimetable(gui_object: DefaultWindow, component: CourseComponent):
    '''Displays the component in the GUI timetable. Note that you should call draw_timetable before using this function.

    Args:
        gui_object (DefaultWindow)
        component (CourseComponent)
    '''

    weekdayMap = gui_object.tt.weekdayMap
    convert_to_timeslot = gui_object.tt.convert_to_timeslot
    ttFrame = gui_object.ttFrame

    if component.type == 'WBL':
        return
    period_frames = convert_to_timeslot(component.periods)

    occupied = gui_object.tt.check_component_for_conflicts(component)

    for day, periods in period_frames.items():
        c = list(weekdayMap.keys()).index(day)
        for row in periods:
            e = tk.Entry(ttFrame, width=18, justify='center')
            e.grid(row=row+1, column=c+1)
            e.insert(tk.END, f"{'{0}'.format(component.id) if component.id else ''} Has conflicts!" if occupied else f"{component.courseNumber}{'-{0}'.format(component.id) if component.id else ''}")
            color = (lambda i: ("#10ee10" if i[0] > i[1] * 2 / 3 else ("#cece34" if i[0] > i[1] / 4 else "#eeba25")))(component.availability)
            if gui_object.tt.check_component_for_conflicts(component) or component.availability[0] == 0:
                color = "#ce2727"
            e.config(state='disabled', disabledbackground=color)

    gui_object.ttFrame = ttFrame

displayCompInTt = displayComponentInTimetable

def process_needed_config(object: DefaultWindow, preassigned_list: list[FilteredCourse], config_needed_list: list[tuple[Course, str]]):
    '''Processor for config_needed_list generated by the API.

    Args:
        object (DefaultWindow): Main GUI object (for processing).
        preassigned_list (list[FilteredCourse]): output of API
        config_needed_list (list[tuple[Course, str]]): output of API

    Returns:
        list[FilteredCourse]: Actual thing idk.
    '''

    for v in config_needed_list:
        cur_course, cur_sect_code = v[0], v[1] if len(v) > 1 else 'None'
        t = PreassignedConfigWindow(object, cur_course, cur_sect_code, preassigned_list)
        try:
            if not t.finish:
                t.wait_window()
        except tk.TclError:
            return [], []
        except Exception as ex:
            print('caught', ex)
            return [], []

        preassigned_list = t.filtered_preassigned_list

    return preassigned_list
        

def update_all(object: DefaultWindow):
    '''process all:
    get preassigned & preferred course (str process)
    backend(selected course) -> timetbale
    display timetable
'''
    object.tt = Timetable()

    # required_course, selected_course = api.process_all(
    #     getSelectedTerm(object),
    #     object.preassignedTextField.get('1.0', 'end'),
    #     object.preferredTextField.get('1.0', 'end'),
    #     object,
    #     object.fake_course
    # )

    config_needed_list, preassigned_list = api.process_preassigned(getSelectedTerm(object), object.preassignedTextField.get('1.0', 'end'))
    # TODO: process config_needed_list
    # if pruivate time exists, add it
    if object.fake_course:
        preassigned_list.append(object.fake_course)
    preassigned_list = process_needed_config(object, preassigned_list, config_needed_list)
    selected_courses = []
    available_courses, available_courses_set = api.generate_available_courses(getSelectedTerm(object), preassigned_list, object.preferredTextField.get('1.0', 'end'))
    if available_courses:
        results = api.generate_top_N(preassigned_list, available_courses, 15) # 15 as default
        sel_win = TopNSelectionWindow(object, preassigned_list, results)
        try:
            if not sel_win.finish:
                sel_win.wait_window()
            # 0 is score, 1 is the actual sel_course
            selected_courses = results[sel_win.sel_idx][1]
        except tk.TclError:
            return [], []
        except Exception as ex:
            print('caught', ex)
            return [], []


    # export required_course and selected_course for fucking around with timetable
    object._required_courses = preassigned_list
    object._selected_courses = selected_courses

    if preassigned_list:
        object.tt.load_preassigned(preassigned_list)
    if selected_courses:
        [object.tt.load_selection(i) for i in selected_courses]

    # bullshit update timetable frame (only display)
    draw_timetable(object, preassigned_list, selected_courses)

    credit_sum = sum([i.credit for i in preassigned_list] + [i.credit for i in selected_courses])
    object.credit_label['text'] = f'Current credits: {credit_sum}'
    object.credit_label['foreground'] = evaluateCreditSum(credit_sum)

def add_private_time(gui_object:DefaultWindow):
    """Private time is stored in gui.fake_course as a list of a fake course

    Args:
        gui_object (DefaultWindow): 
    """
    p_time_win = AddPrivateTimeWindow(gui_object)
    if not p_time_win.finish:
        p_time_win.wait_window()
    gui_object.fake_course = p_time_win.get_fake_course()
    gui_object._required_courses = [i for i in gui_object._required_courses if i.course_name != 'Private Time']
    gui_object._required_courses.append(gui_object.fake_course)
    draw_timetable(gui_object, gui_object._required_courses, gui_object._selected_courses)
    # print(p_time_win.periods)

def spawnProgramBrowser(gui_object: DefaultWindow):
    '''Name explains everything'''
    if not gui_object._BROWSING_PROGRAM_INFO:
        w = ProgramInfoBrowser(gui_object)
        gui_object.wait_window(w)
        gui_object._BROWSING_PROGRAM_INFO = False
    else:
        tk.messagebox.showwarning(title='Bad user!', message='Close your current session first!')

def evaluateCreditSum(csum):
    if csum > 19:
        return "#A01818"
    elif csum < 9:
        return "#FF0000"
    elif csum <= 14:
        return "#CECE00"
    else:
        return "#18A018"