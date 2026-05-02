import math
from modules.course import *


class Timetable:

    weekdayMap = {
        "Mo": "Monday",
        "Tu": "Tuesday",
        "We": "Wednesday",
        "Th": "Thursday",
        "Fr": "Friday",
        "Sa": "Saturday",
        "Su": "Sunday",
    }
    
    def __init__(self):
        # self.week_schedule = {}
        # self.pretty_week_schedule = {}

        # Slot 0 = 8:30, 1 = 9:30...
        self.freetime = {day: [i for i in range(11)] for day in self.weekdayMap}
        self.preassigned = []  # [ENGG1110(C)(T01), ]

    # def minutesToTimeString(self, mins):
    #     h = math.floor(mins / 60)
    #     mins = mins % 60
    #     return f"{h:02d}:{mins}"

    # # timeString format: 2:30AM
    # def minutes(self, timeString):
    #     t = timeString.split(":")
    #     h = int(t[0]) * 60
    #     if t[1][2:] == "PM":
    #         h += 12 * 60 if h < 11 * 60 else 0
    #     m = int(t[1][:2])
    #     # print( t[1][2:])
    #     return h + m
    @classmethod
    def convert_to_timeslot(self, periods: list) -> dict[str: list]:
        """Convert periods occupied by the course into timeslot format
        Args:
            periods (list): CourseComponent.periods

        Returns:
            dict[str, list]: eg. {'Tu':[2, 3, 4]}
        """
        occupied = {}
        for period in periods:
            if period == "TBA":
                continue
            # period = "Th 02:30PM - 04:15PM"
            # day = period[:2]
            # start = int(period[3:5])
            # end = int(period[14:16])

            # start_slot = (start-8)%12
            # end_slot = (end-8)%12

            # SUGGESTION
            plist = period.split()
            day = plist[0]
            start = int(plist[1][:2])
            end = int(plist[3][:2])

            start_slot = (start - 8) % 12
            end_slot = (end - 8) % 12

            if day in occupied:
                occupied[day] += [i for i in range(start_slot, end_slot)]
                occupied[day] = list(
                    dict.fromkeys(occupied[day])
                )  # Remove duplicates, if any
            else:
                occupied[day] = [i for i in range(start_slot, end_slot)]
        # return day, [i for i in range(start_slot, end_slot+1)]

        return occupied

    def check_component_for_conflicts(self, component: CourseComponent) -> bool:
        """
        Returns TRUE if there are any conflicts between this component and timetable.
        Returns FALSE otherwise.
        """
        if component.type == "WBL":
            return False
        periods = self.convert_to_timeslot(component.periods)
        checker = lambda d, p: 0 if p in self.freetime[d] else 1
        result = [checker(day, period) for day in periods for period in periods[day]]
        return sum(result) != 0

    def load_preassigned(self, courses: list[FilteredCourse]):
        """
        Assume no other options for lecture/tutorial  
        Also no conflict possible
        """
        # occupied_period = []
        # #TODO bug fix list of list
        # for course in courses:
        #     if course.lec:
        #         self.lec = course.lec.values()[0] # CourseComponent object
        #         occupied_period += self.lec.periods
        #     if course.tut:
        #         self.tut = course.tut.values()[0] # CourseComponent object
        #         occupied_period += self.tut.periods
        #     if course.lab:
        #         self.lab = course.lab.values()[0] # CourseComponent object
        #         occupied_period += self.lab.periods
        #     if course.exp:
        #         self.exp = course.exp.values()[0] # CourseComponent object
        #         occupied_period += self.exp.periods
        occupied_period = []
        for course in courses:
            occupied_period += [component.periods for component in course.components]
            self.preassigned.append(course)
        occupied_period = [period for periodlist in occupied_period for period in periodlist]  # Flatten list
        # print(occupied_period)
        occupied = self.convert_to_timeslot(occupied_period)
        for day in occupied:
            for slot in occupied[day]:
                self.freetime[day].remove(slot)

    def load_selection(self, course: FilteredCourse):
        """
        Add `course` to the timetable.  
        **Does NOT check whether there are conflicts.**
        """
        self.add_components(course.components)

    def remove_selection(self, course: FilteredCourse):
        '''Remove `course` from the timetable.'''
        self.remove_components(course.components)

    def add_components(self, components: list[CourseComponent]):
        '''Add the components to the timetable.

        Args:
            components (list[CourseComponent]): This is what you think it is.
        '''
        occupied_period = [component.periods for component in components if component.type != "WBL"]
        occupied_period = [period for periodlist in occupied_period for period in periodlist]  # Flatten list

        occupied = self.convert_to_timeslot(occupied_period)
        for day in occupied:
            for slot in occupied[day]:
                self.freetime[day].remove(slot)

    def remove_components(self, components: list[CourseComponent]):
        '''Remove components from the timetable

        Args:
            components (list[CourseComponent]): This is what you think it is.
        '''
        occupied_period = [component.periods for component in components if component.type != "WBL"]
        occupied_period = [period for periodlist in occupied_period for period in periodlist]  # Flatten list

        occupied = self.convert_to_timeslot(occupied_period)
        for day in occupied:
            for slot in occupied[day]:
                self.freetime[day].append(slot)

    # def appendDateString(self, dateString):

    #     if dateString == "TBA":
    #         return None

    #     dateString = dateString.split()
    #     date = dateString[0]
    #     start_time = self.minutes(dateString[1])
    #     end_time = self.minutes(dateString[3])

    #     duration = end_time - start_time
    #     if date not in self.week_schedule:
    #         self.week_schedule[date] = []
    #         self.pretty_week_schedule[self.weekdayMap[date]] = []
    #     self.week_schedule[date].append([start_time, duration])
    #     self.pretty_week_schedule[self.weekdayMap[date]].append(
    #         [self.minutesToTimeString(start_time), self.minutesToTimeString(end_time)]
    #     )
    #     return duration

    # def appendCourse(self, courseData):
    #     for i in courseData["components"]:
    #         [self.appendDateString(k) for k in i["periods"]]


"""
Format of stuff in JSON
{
    'course_code':{
        'section_code': the section code (str),
        'credits': no. of credits (int),
        'components': [
            {
                'type': type of component, e.g. LEC, TUT (str)
                'section': section code of component (str)
                'room': the location of class (str)
                'periods': time period of class (list) [e.g. Mo 2:30AM - 5:00AM]
                'dates': all dates (str)
            }
        ]
    }
}   
"""

{
    "ENGG2780": [
        {
            "components": [
                {
                    "dates": "6/1, 13/1, 20/1, 27/1, 10/2, 17/2, "
                    "24/2, 10/3, 17/3, 24/3, 31/3, 7/4, "
                    "14/4",
                    "periods": ["Mo 12:30PM - 02:15PM"],
                    "room": "MMW_LT1",
                    "section": "A",
                    "type": "LEC",
                },
                {
                    "dates": "8/1, 15/1, 22/1, 5/2, 12/2, 19/2, "
                    "26/2, 12/3, 19/3, 26/3, 2/4, 9/4, "
                    "16/4",
                    "periods": ["We 12:30PM - 02:15PM"],
                    "room": "MMW_LT1",
                    "section": "AT01",
                    "type": "TUT",
                },
            ],
            "credits": 2.0,
            "section": "A",
        },
        {
            "components": [
                {
                    "dates": "6/1, 13/1, 20/1, 27/1, 10/2, 17/2, "
                    "24/2, 10/3, 17/3, 24/3, 31/3, 7/4, "
                    "14/4",
                    "periods": ["Mo 12:30PM - 02:15PM"],
                    "room": "ERB_LT",
                    "section": "B",
                    "type": "LEC",
                },
                {
                    "dates": "8/1, 15/1, 22/1, 5/2, 12/2, 19/2, "
                    "26/2, 12/3, 19/3, 26/3, 2/4, 9/4, "
                    "16/4",
                    "periods": ["We 12:30PM - 02:15PM"],
                    "room": "SC_L1",
                    "section": "BT01",
                    "type": "TUT",
                },
            ],
            "credits": 2.0,
            "section": "B",
        },
    ]
}


if __name__ == "__main__":
    tt = Timetable()
    print(tt.freetime)
