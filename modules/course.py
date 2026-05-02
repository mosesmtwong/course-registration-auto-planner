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

"""
"UGFN1000": [
  {
   "UGFN1000A": {
    "class details": {
     "status": "Open",
     "class Number": "8011",
     "units": "3 units",
     "grading": "Graded",
     "instruction mode": "In Person",
     "course components": "Lecture, Interactive Tutorial"
    },
    "meeting information": {
     "LEC": [
      "ELB_LT2",
      [
       [
        "Fr 01:30PM - 02:15PM",
        "10/1, 17/1, 24/1, 7/2, 14/2, 21/2, 28/2, 14/3, 21/3, 28/3, 11/4"
       ]
      ]
     ],
     "TUT": [
      "YIA_510",
      [
       [
        "Th 02:30PM - 04:15PM",
        "9/1, 16/1, 23/1, 6/2, 13/2, 20/2, 27/2, 13/3, 20/3, 27/3, 3/4, 10/4, 17/4"
       ]
      ]
     ]
    },
    "Enrollment information": [
     "For Year 1 and Year 2 students",
     "Not for students who have taken UGFN1001"
    ],
    "class availablity": {
     "available seats": "139",
     "class capacity": "150",
     "enrollment total": "11",
     "wait list capacity": "999",
     "wait list total": "0"
    }, 
    ...
}
"""
import re


class CourseComponent:

    map = {
        "LEC": "Lecture",
        "TUT": "Tutorial",
        "EXR": "Exercise/Experiment",
        "LAB": "Lab Session",
        "PRJ": "Project",
        "SEM": "Seminar",
        "OTH": "Other",
        "ASB": "Assembly",
        "CLW": "Classwork",
        "FLD": "Field Trip",
        "WBL": "Web Course",
    }

    langmap = {
        "A": "Arab only",
        "A&C": "Arab and Cantonese",
        "A&E": "Arab and English",
        "A&P": "Arab and Putonghua",
        "C": "Cantonese only",
        "C#E": "Cantonese, change to English if needed",
        "C&E": "Cantonese and English",
        "C&E&P": "Cantonese, English and Putonghua",
        "E": "English only",
        "F": "French only",
        "F&C": "French and Cantonese",
        "F&E": "French and English",
        "F&P": "French and Putonghua",
        "G": "German only",
        "G&C": "German and Cantonese",
        "G&E": "German and English",
        "G&P": "German and Putonghua",
        "H": "Hokkien only",
        "H&C": "Hokkien and Cantonese",
        "H&E": "Hokkien and English",
        "H&P": "Hokkien and Putonghua",
        "H&C&P": "Hokkien, Cantonese and\u00a0Putonghua",
        "I": "Italian only",
        "I&C": "Italian and Cantonese",
        "I&E": "Italian and English",
        "I&P": "Italian and Putonghua",
        "J": "Japanese only",
        "J&C": "Japanese and Cantonese",
        "J&E": "Japanese and English",
        "J&P": "Japanese and Putonghua",
        "J&C&P": "Japanese, Cantonese and Putonghua",
        "K": "Korean only",
        "K&C": "Korean and Cantonese",
        "K&E": "Korean and English",
        "K&P": "Korean and Putonghua",
        "P": "Putonghua only",
        "P#E": "Putonghua, change to English if needed",
        "P&C": "Putonghua and Cantonese",
        "P&E": "Putonghua and English",
        "R": "Russian",
        "R&C": "Russian and Cantonese",
        "R&E": "Russian and English",
        "R&P": "Russian and Putonghua",
        "S": "Spanish only",
        "S&C": "Spanish and Cantonese",
        "S&E": "Spanish and English",
        "S&P": "Spanish and Putonghua",
        "SL": "Hong Kong Sign Language",
        "T": "Thai only",
        "T&C": "Thai and Cantonese",
        "T&E": "Thai and English",
        "T&P": "Thai and Putonghua",
    }

    def __init__(self, type, id):
        self.type = type  # LEC, TUT, etc.
        self.id = id  # A, B, C...
        if self.id == "None":
            self.id = None
        self.courseNumber = None
        self.periods = []
        self.locations = []
        self.quotas = None
        self.lecturer = None
        self.availability = "0/0"
        self.language = ""

    def __str__(self):
        return f"{self.type}-{self.id}({self.courseNumber}) {self.periods} {self.locations} quota:{self.quotas} {self.lecturer}"

    def summary(self):
        """Give a short summary of the component.
        This function is intended to be used by the functions setting outputLabel etc.
        For general use, please call __str__() instead.
        """

        loc_string = ("\n").join(
            [
                f"{period} at {location}"
                for period, location in zip(self.periods, self.locations)
            ]
        )
        return f"{self.map[self.type]}{' - {0}'.format(self.id) if self.id else ''} ({self.lecturer})\n{self.availability[0]}/{self.availability[1]} slots available | Taught in {self.langmap[self.language]}\n{loc_string}"

    def to_dict(self):
        return {
            "type": self.type,
            "section": self.id,
            "periods": self.periods,
            "room": self.locations,
            "lecturer": self.lecturer,
            "availability": self.availability,
            "language": self.language,
        }


class Course:
    """For raw data of course. From scraper"""

    def __init__(self, course_name):

        self.course_name = course_name  # ENGG1110, not for ENGG1100CL01 etc.
        """course_name: Course name of the course. Example: ENGG1110"""

        self.faculty = course_name[:4]  # ENGG, CSCI, ...
        """First 4 letters of the course name. """

        self.term_id = None  # 2350, 2340, ...
        self.title = None
        """The title of the course. e.g. Calculus for Engineers"""

        self.credit = 0
        self.lec = {}  # {A: CourseComponent()}
        """INTERNAL: Dict of this component type."""

        self.tut = {}  # {AT01: CourseComponent()}
        """INTERNAL: Dict of this component type."""

        self.lab = {}  # {AL01: CourseComponent()}
        """INTERNAL: Dict of this component type."""

        self.exr = {}  # {E01: CourseComponent()}
        """INTERNAL: Dict of this component type."""

        self.prj = {}  # {AJ01: CourseComponent()}
        """INTERNAL: Dict of this component type."""

        self.sem = {}  # {AS01: CourseComponent()}
        """INTERNAL: Dict of this component type."""

        self.oth = {}  # {AO01: CourseComponent()}
        """INTERNAL: Dict of this component type."""

        self.asb = {}
        """INTERNAL: Dict of this component type."""

        self.clw = {}
        """INTERNAL: Dict of this component type."""

        self.wbl = {}
        """INTERNAL: Dict of this component type."""

        self.fld = {}
        """INTERNAL: Dict of this component type."""

        self.ind = {}
        """INTERNAL: Dict of this component type."""

        self.description = None

    def printclass(self):
        """print all variable of the Course object"""
        temp = vars(self)
        for key in temp:
            if type(temp[key]) == dict:
                l = (", ").join([f"{k} {v}" for k, v in temp[key].items()])
                print(f"{key}: {l}")
            else:
                print(f"{key}: {temp[key]}")
        print("\n")

    def getSections(self):
        """Get all sections of a course

        Returns:
            list: list of all session codes (they are in string format.)
        """
        if self.lec:
            l = [id for id in list(self.lec.keys())]
            return l if l else ["None"]
        else:
            # this is FUCKING annoying

            merged_dict = {}
            temp = vars(self)
            for key in temp:
                if type(temp[key]) == dict:
                    merged_dict.update(temp[key])

            # OK, you might be a bit scared by this regex here.
            # What this does is search for a uppercase letter followed by a digit immediately (i.e. A[T0]1, A[T1])
            # Then we return all the string in front of it, which is the section code we'd like.
            all_index = [
                key[: re.search(r"[A-Z]\d", key).span()[0]]
                for key in merged_dict.keys()
            ]
            return all_index

    def getComponentsBySection(self, sectionId) -> list[CourseComponent]:
        """Get **all** components of a certain section.  
        Call `getComponentsBySectionCode` instead for a more general solution.  

        Args:
            sectionId (str): sectionId (e.g. 'A', 'B', 'None')

        Returns:
            list of CourseComponent object
        """
        merged_dict = {}
        temp = vars(self)
        for key in temp:
            if type(temp[key]) == dict:
                merged_dict.update(temp[key])
        if sectionId == "None" or sectionId == None:
            return [componentObject for id, componentObject in list(merged_dict.items())]
        else:
            # See above for what the regex does.
            # Return all components if they match the session specified.
            # N: `and` is executed left to right. so we need to check if `id` is valid first. see comment below on why.
            section_match = lambda id: (id[: re.search(r"[A-Z]\d", id).span()[0]] if id and re.search(r"[A-Z]\d", id) else id) # somehow slipped through when some STUPID people at cusis decide to add None, A, B, C as course id.
            return [componentObject for id, componentObject in list(merged_dict.items()) if section_match(id) == sectionId]

    def sessionCheck(self, arg:CourseComponent):
        if not self.section or not arg.id:
            return True
        # print(arg.id, self.section, self.scode)
        if arg.id == self.section or arg.id == self.scode:
            return True
        # print(re.findall(r'\d+', arg.id), re.findall(r'\d+', self.section))
        # Final resort: check if the numbers of the component are equal
        return re.findall(r'\d+', arg.id) == re.findall(r'\d+', self.section)

    def getComponentsBySectionCode(self, section_code: str) -> list[CourseComponent]:
        '''Returns a list of all components matching the section number specified.

        Args:
            section_code (str): EXAMPLE: GT04, T05.
            You should not call with None.
        '''

        # sanitize input 
        number = str(section_code)
        if section_code:
            if re.search(r'^[A-Z]\d', section_code):
                self.scode = None
                self.section = section_code 
            elif re.search(r"[A-Z]+\d", section_code):
                self.scode = section_code[0]
                self.section = section_code[1:]
            elif re.search(r"[A-Z]{2}\d+", section_code):
                self.scode = section_code[0]
                self.section = section_code[1:]
            elif re.search(r"^[A-Z]$", section_code):
                self.scode = section_code
                self.section = None 
            else:
                self.scode = self.section = None
        else:
            self.scode = self.section = None

        courseVariables = vars(self)

        components = self.getComponentsBySection(self.scode if self.scode else 'None')
        clist = []
        for key in courseVariables:
            if type(courseVariables[key]) == dict and courseVariables[key]:
                # Then it is a thing we'd like to insert
                comp = courseVariables[key]
                compList = list(comp.values())
                if len(compList) == 1:
                    # Then we can just add it since it must be required
                    clist += compList
                    continue
                # check that this component is indeed in this section
                clist += [i for i in compList if (i in components and self.sessionCheck(i))]
                
        return clist

    getComponentsByNumber = getComponentsBySectionCode

    def checkConfigurationNeeded(self, section_code: str) -> bool:
        '''Check if any further processing is needed for the given section code.  
        This is really just a getComponentsBySectionCode wrapper...

        Args:
            section_code (str): Section code desired.

        Returns:
            bool: True if further processing is needed.
        '''
        # magic regex matching
        if section_code:
            if re.search(r'^[A-Z]\d', section_code):
                self.scode = None
                self.section = section_code 
            elif re.search(r"[A-Z]+\d", section_code):
                self.scode = section_code[0]
                self.section = section_code[1:]
            elif re.search(r"[A-Z]{2}\d+", section_code):
                self.scode = section_code[0]
                self.section = section_code[1:]
            elif re.search(r"^[A-Z]$", section_code):
                self.scode = section_code
                self.section = None 
            else:
                self.scode = self.section = None
        else:
            self.scode = self.section = None

        courseVariables = vars(self)
        # if you know how to optimize this i'd like you to
        components = self.getComponentsBySection(self.scode if self.scode else None) # this is necessary because sessionCheck only checks the numbers (joy)
        # check for each dict containing course comps
        for key in courseVariables:
            if type(courseVariables[key]) == dict and courseVariables[key]:
                comp = courseVariables[key]
                compList = list(comp.values())
                compList = [i for i in compList if (i in components and self.sessionCheck(i))]
                # more than 1 course comp -> need further configuration
                if len(compList) > 1:
                    return True
                
        return False

    @staticmethod
    def from_dict(dict_object):
        """Static method, creates course object from dict.  

        PARAMETERS:
            `dict_object`: a dictionary containing details of a single course.

        RETURNS
            `Course`: a course object

        Dictionary format (same as that in temp/cache.json)
        {"<course code>": [
            {"section": <section code>, "credits": <credits>, "components": [
                {"type": <LEC/TUT...>, "section": <A, AT01, ...>, "periods": [<same as periods here>], "dates": <meeting dates>, "room": <location>},
                ...
            ]}, ...
        }
        """
        courseObj = Course("mikuchan")
        courseObj.course_name = list(dict_object.keys())[0]
        courseObj.faculty = courseObj.course_name[:4]
        for entry in dict_object[courseObj.course_name]:
            courseObj.title = entry["title"]
            courseObj.credit = entry["credits"]
            for component in entry["components"]:
                tempComponent = CourseComponent(component["type"], component["section"])
                tempComponent.courseNumber = courseObj.course_name# + str(component["section"] if component["section"] else '')
                tempComponent.periods = component["periods"]
                tempComponent.lecturer = component["lecturer"]
                tempComponent.locations = component["room"]
                tempComponent.availability = component["availability"]
                tempComponent.language = component["language"]
                # Append to correct component dict.
                # I hate you RES
                temp = vars(courseObj)
                for key in temp:
                    if type(temp[key]) == dict and key.upper() == component["type"]:
                        component_dict = getattr(courseObj, key)
                        component_dict[component["section"]] = tempComponent
                        setattr(courseObj, key, component_dict)
                # if component['type'] == 'LEC':
                #     courseObj.lec[component['section']] = tempComponent
                # elif component['type'] == 'TUT':
                #     courseObj.tut[component['section']] = tempComponent
                # elif component['type'] == 'LAB':
                #     courseObj.lab[component['section']] = tempComponent
                # elif component['type'] == 'EXR':
                #     courseObj.exr[component['section']] = tempComponent
                # elif component['type'] == 'PRJ':
                #     courseObj.prj[component['section']] = tempComponent
                # elif component['type'] == 'SEM':
                #     courseObj.sem[component['section']] = tempComponent
                # elif component['type'] == 'OTH':
                #     courseObj.oth[component['section']] = tempComponent
                # elif component['type'] == 'ASB':
                #     courseObj.asb[component['section']] = tempComponent

        return courseObj

    def to_dict(self):
        """
        Builds dictionary similar to temp/cache.json format.

        RETURNS: Dictionary built by the function.
        """

        component_ids = list(self.lec.keys())
        sectionList = []
        for component_id in component_ids:
            components = self.getComponentsBySection(component_id)
            components = [component.to_dict() for component in components]
            sectionList.append(
                {
                    "title": self.title,
                    "section": component_id,
                    "credits": self.credit,
                    "components": components,
                }
            )
        if not sectionList:
            components = self.getComponentsBySection("None")
            components = [component.to_dict() for component in components]
            sectionList.append(
                {
                    "title": self.title,
                    "section": None,
                    "credits": self.credit,
                    "components": components,
                }
            )
        return {self.course_name: sectionList}


class FilteredCourse(Course):

    components = []

    def __init__(self, course_name):
        super().__init__(course_name)


    def is_ambigious(self) -> bool:
        """Check if the FilteredCourse needs further filtering.

        Returns: `bool`"""
        return list(set([i.type for i in self.components])) == [i.type for i in self.components]

    def getAvailabilityRatio(self):
        '''average availability of this FilteredCourse
        Empty courses have availability 0'''
        if not self.components: return 0
        if 0 in [i.availability[0] for i in self.components]: return 0
        return sum([i.availability[0]/i.availability[1] for i in self.components]) / len(self.components)

    @staticmethod
    def filterCourseBySection(course: Course, component_id: str):
        """For a given course object, filter it such that only the components with the given component_id exists.

        `component_id` should be some alphabetical stuff or None.

        Returns a FilteredCourse object."""

        t = FilteredCourse(course.course_name)
        t.components = course.getComponentsBySection(component_id)
        t.title = course.title
        t.credit = course.credit
        t.description = course.description
        return t
    
    @staticmethod
    def filterCourseBySectionCode(course: Course, component_id: str):
        """For a given course object, filter it such that only the components with the given component_id exists.  
        `component_id` should be some alphanumeric stuff or None.  
        Returns:
            FilteredCourse: a FilteredCourse object."""

        t = FilteredCourse(course.course_name)
        t.components = course.getComponentsBySectionCode(component_id)
        t.title = course.title
        t.credit = course.credit
        t.description = course.description
        return t