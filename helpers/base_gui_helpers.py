import tkinter as tk

from modules.timetable import Timetable
from modules.course import *


def make_timetable_frame(ttFrame: tk.Frame, preassigned: list[FilteredCourse] = [], selected: list[FilteredCourse] = []):
    '''Make a frame for the timetable.

    Args:
        ttFrame (tk.Frame): _description_
        preassigned (list[FilteredCourse], optional): If not given, assume no courses
        selected (list[FilteredCourse], optional): If not given, assume no courses
    '''
    
    weekdayMap = Timetable.weekdayMap
    convert_to_timeslot = Timetable.convert_to_timeslot

    # if don't destory widgets originally in frame, will lead to stacking and consumes a lot of memory
    for widget in ttFrame.winfo_children():
        widget.destroy()

    # The following code DIRECTLY modifies the entries inside ttFrame.
    # or should i say spawn new objects, so making too much will lag the program by a lot...
    ROWS = 10
    # Build header row
    e = tk.Entry(ttFrame, justify='center', width=13)
    e.insert(tk.END, 'Timeslot')
    e.config(state='disabled', disabledbackground='#141414', disabledforeground='#FFFFFF')
    e.grid(row=0, column=0)
    c=1
    for day in weekdayMap:
        e = tk.Entry(ttFrame, justify='center', width=18)
        e.grid(row=0, column=c)
        e.insert(tk.END, weekdayMap[day])
        e.config(state='disabled', disabledbackground='#141414', disabledforeground='#FFFFFF')
        c+=1
    
    # Build rows containing course data / free time
    for slot in range(ROWS):
        e = tk.Entry(ttFrame, justify='center', width=13)
        e.grid(row=slot+1, column=0)
        e.insert(tk.END, f'{slot+8:02}:30 - {slot+9:02}:15')
        e.config(state='disabled', disabledbackground='#141414', disabledforeground='#FFFFFF')
        c=1
        for day in weekdayMap:
            # Build timeslot entries for each day
            e = tk.Entry(ttFrame, width=18)
            e.grid(row=slot+1, column=c)
            e.insert(tk.END, '')
            color = '#00FF00'
            e.config(state='disabled', disabledbackground=color)
            c+=1
    
    # Assign labels to occupied slots
    for course in preassigned:
        for component in course.components:
            if component.type == 'WBL':
                continue
            period_frames = convert_to_timeslot(component.periods)
            for day, periods in period_frames.items():
                c = list(weekdayMap.keys()).index(day)
                for row in periods:
                    e = tk.Entry(ttFrame, width=18, justify='center')
                    e.grid(row=row+1, column=c+1)
                    e.insert(tk.END, f"{course.course_name}{'-{0}'.format(component.id) if component.id else ''}")
                    color = '#FF0000' if course.course_name != 'Private Time' else "#D400FF"
                    e.config(state='disabled', disabledbackground=color)

    for course in selected:
        for component in course.components:
            if component.type == 'WBL':
                continue
            period_frames = convert_to_timeslot(component.periods)
            for day, periods in period_frames.items():
                c = list(weekdayMap.keys()).index(day)
                for row in periods:
                    e = tk.Entry(ttFrame, width=18, justify='center')
                    e.grid(row=row+1, column=c+1)
                    e.insert(tk.END, f"{course.course_name}{'-{0}'.format(component.id) if component.id else ''}")
                    color = '#FFFF00'
                    e.config(state='disabled', disabledbackground=color)

    return ttFrame