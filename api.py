from modules.course import *
from modules.timetable import *
from modules.SchemeProcessors import *
from helpers.scraper_helpers import *
from helpers.config_windows import PreassignedConfigWindow, ConflictResolverWindow
import tkinter as tk
import copy
import heapq
import random

def process_all(term: str, required: str, preferred: str, gui_object, private:list[FilteredCourse]) -> tuple[list[FilteredCourse], list[FilteredCourse]]:
    """
    **DEPRECATED**  
    In the first place, it doesn't make sense for the API to have something like `process_all`.  
    That is ambigious and unclear.  
    Instead I suggest that we change it to something else. Why not more levels of abstraction? 
    That is, we should split up `process_all` and cut it into multiple components for the GUI and the API to interact.

    Args:
        term (str): term
        required (str): \\n seperated
        preferred (str): \\n seperated

    Returns:
        tuple[list[FilteredCourse], list[FilteredCourse]]: (required courses, selected optional courses)
    """
    # use name to find course
    required = required.upper()
    preferred = preferred.upper()

    required_courses: list[Course] = copy.deepcopy(private)
    preferred_courses: list[Course] = []

    required_dict = {}
    preferred_dict = {}
    for faculty, course in [(course[:4], course) for course in required.split("\n") if course]:
        if faculty not in required_dict:
            required_dict[faculty] = []
        required_dict[faculty].append(course)
    for faculty, course in [(course[:4], course) for course in preferred.split("\n") if course]:
        if faculty not in preferred_dict:
            preferred_dict[faculty] = []
        preferred_dict[faculty].append(course)

    # process preassigned courses
    if required:
        for faculty in required_dict:
            crs_list = cached_lookup(term, faculty)
            for c in crs_list:
                for i, name in enumerate(required_dict[faculty]):
                    if c.course_name in name:
                        cur_course = c
                        cur_section = required_dict[faculty][i][8:] if required_dict[faculty][i][8:] else None
                        t = PreassignedConfigWindow(gui_object, cur_course, cur_section, required_courses)
                        try:
                            if not t.finish:
                                t.wait_window()
                        except tk.TclError:
                            return [], []
                        except Exception as ex:
                            print('caught', ex)
                            return [], []

                        required_courses = t.filtered_preassigned_list
                        # required_courses.append(filtered_course)
                    
    # process preferred courses (it will work...?)
    if preferred:
        for faculty in preferred_dict:
            crs_list = cached_lookup(term, faculty)
            for c in crs_list:
                for i, name in enumerate(preferred_dict[faculty]):
                    if c.course_name in name:
                        preferred_courses.append(c)
    
    # alg
    timetable = Timetable()
    timetable.load_preassigned(required_courses)
    available_courses = []
    available_courses_set = []
    selected_courses = []
    
    SEL_SECT_WINDOW_SPAWNED =0 
    
    for course in preferred_courses:
        section_list = course.getSections()
        if SEL_SECT_WINDOW_SPAWNED: # spawn at beginning of process_all, no need to care if conflict exist
            pass # override section list
        possible_choices = []
        clean_plausible_pairs = []
        all_components = []
        for i in section_list:
            components_list = course.getComponentsBySection(i)
            if not timetable.check_component_for_conflicts(components_list[0]): # check if LEC session is available
                # ok, it's available!
                all_components += components_list
                if len(components_list) == 1:
                    # only lecture exists! time to add it to our selected courses.
                    possible_choices.append(components_list)
                    clean_plausible_pairs.append(components_list)
                else:
                    c_dict = sort_components_into_dicts(components_list)
                    
                    # find component type with the MAX amount of indices
                    keys = [i for i in list(c_dict.keys())]
                    lens = [len(i) for i in list(c_dict.values())]
                    max_len_indx = lens.index(max(lens))

                    # this list has the components that we want to search. e.g. TUT has most components with 
                    # T01, T02, ..., T06. Using getCompsBySectCode, we can obtain pairs of components: [LEC, TUT01], [LEC, TUT02], ...
                    for i in c_dict[keys[max_len_indx]]:
                        temp_comp_list = course.getComponentsBySectionCode(i.id)
                        # since this returns LEC first, we can just skip it
                        # if any is true then the sum will be larger than zero
                        if check_components_for_conflicts(timetable, temp_comp_list):
                            continue # do not proceed to scoring if it doesn't work
                        possible_choices.append(temp_comp_list)
                        clean_plausible_pairs.append([cmp for cmp in temp_comp_list if cmp not in flatten_2d(clean_plausible_pairs)])
                    
                    # print("looped")
                    # plausible_pairs is a list of pairs of course components
                    # [print(f"{i}, {j}") for (i,j) in plausible_pairs]

        available_courses.append(possible_choices)
        available_courses_set.append(clean_plausible_pairs)

    # if len(available_courses) >= 2:
    #     # print(available_courses)
    #     scored_courses = [[] for i in range(len(available_courses))]
    #     # course list is a list of components, e.g. (UGFH1000:) [[A, AT01], [A, AT02], [B, BT01], ...]
    #     for index, course_list in enumerate(available_courses[:-1]):
    #         for particular_choice in course_list:
    #             conflicts = generate_conflicting_courses(particular_choice, flatten_list(available_courses_set[index+1:]))
    #             scored_courses[index].append(particular_choice+[conflicts])
    #     # print(scored_courses)
    ''' 
    Confused?
    available_courses: [
        (0: UGFH1000) [
            [A, AT01], [A, AT02], [B, BT01]
        ],
        (1: ENGG1120) [
            [A, AT01], [B, BT01], [C, CT01]
        ]    
    ]
    
    iterate available_courses -> give list of plausible pairs
    iterate list of plausible pairs -> get each list of components (for a specific section)
    '''

    scored_courses = [[] for i in range(len(available_courses))]
    if len(available_courses) >= 2:
        # print(available_courses)
        # course list is a list of components, e.g. (UGFH1000:) [[A, AT01], [A, AT02], [B, BT01], ...]
        for index, possible_choices in enumerate(available_courses[:-1]):
            # Case 1: No choices
            if not possible_choices:
                tk.messagebox.showwarning(message=f'WARNING: {preferred_courses[index].course_name} has been skipped due to no available timeslot.')
                continue
            # Case 2: Have choices -> need to check if any remain that have no conflict
            for particular_choice in possible_choices:
                conflicts = 0
                    # print(available_courses[index+1:])
                if check_components_for_conflicts(timetable, particular_choice):
                    continue
                conflicts = generate_conflicting_courses(particular_choice, flatten_list(available_courses_set[index+1:]))
                scored_courses[index].append(particular_choice+[conflicts])
        
            # each entry in plausible_pairs is appeneded with a list of all conflicts now
            # now we need to select one pair of components. after getting this component, we need to update available_courses such that
            # all unavailable courses are dropped from the list.
            if not scored_courses[index]:
                tk.messagebox.showwarning(message=f'WARNING: {preferred_courses[index].course_name} has been skipped due to no available timeslot.')
                continue
            c_win = ConflictResolverWindow(gui_object, scored_courses[index])
            try:
                if not c_win.finish:
                    c_win.wait_window()
                selected_pair = c_win.getSelectedPair()
            except tk.TclError:
                return [], []
            except Exception as ex:
                print('caught', ex)
                return [], []

            # do something with selected_pair
            print(f'loading {selected_pair}')
            _temp_filtered_course = FilteredCourse(selected_pair[0].courseNumber)
            _temp_filtered_course.components = selected_pair[:-1]
            _temp_filtered_course.credit = preferred_courses[index].credit
            timetable.load_selection(_temp_filtered_course)
            selected_courses.append(_temp_filtered_course)
    
    # if 1 course only / 1 course left
    if available_courses:
        if not available_courses[-1]:
            tk.messagebox.showwarning(message=f'WARNING: {preferred_courses[-1].course_name} has been skipped due to no available timeslot.')
            return required_courses, selected_courses
        
        for particular_choice in available_courses[-1]:
            # print(available_courses[-1], particular_choice)
                # print(available_courses[index+1:])
            if not check_components_for_conflicts(timetable, particular_choice):

                v = particular_choice
                v.append([])
                scored_courses[-1].append(v)
        

        c_win = ConflictResolverWindow(gui_object, scored_courses[-1])
        try:
            if not c_win.finish:
                c_win.wait_window()
            selected_pair = c_win.getSelectedPair()
        except tk.TclError:
            return [], []
        except Exception as ex:
            print('caught', ex)
            return [], []

        # do something with selected_pair
        print(f'loading {selected_pair[0].courseNumber}')
        _temp_filtered_course = FilteredCourse(selected_pair[0].courseNumber)
        # print(selected_pair[:-1][0])
        _temp_filtered_course.components = selected_pair[:-1]
        try:
            _temp_filtered_course.credit = preferred_courses[index].credit
        except Exception as ex:
            print(f'caught {ex}')
            try: 
                _temp_filtered_course.credit = preferred_courses[0].credit
            except Exception as ex2:
                raise ex2
        # timetable.load_selection(_temp_filtered_course)
        selected_courses.append(_temp_filtered_course)
    
    
    # print(scored_courses)
                    

    return required_courses, selected_courses

def makeFilteredCourse(course: Course, components: list[CourseComponent]) -> FilteredCourse:
    '''make a filtered course with components'''
    t = FilteredCourse(course.course_name)
    t.components = components
    t.title = course.title 
    t.credit = course.credit
    return t

def process_preassigned(term: str, required: str) -> tuple[list[FilteredCourse], list[FilteredCourse]]:
    '''Process preassigned courses.  

    <h2>Arguments</h2>
        **term** (str): current term id
        **required** (str): string of required courses, separated by `\\n`

    <h2>Return Variables</h2>
        **config_needed_list** (list[FilteredCourse]): Preassigned courses with conflict.  
        **preassigned_list** (list[FilteredCourse]): Preassigned courses without conflict.

    Ideally, further down the pipeline the courses should be configuratedm and put into a single list of preassigned courses.  
    After that, private time can be added.
    '''
    # use name to find course
    required = required.upper()

    required_dict = {}
    for faculty, course in [(course[:4], course) for course in required.split("\n") if course]:
        if faculty not in required_dict:
            # init the list
            required_dict[faculty] = [] 
        required_dict[faculty].append(course)

    config_needed_list = []
    preassigned_list = []
    # process preassigned courses
    if required:
        for faculty in required_dict:
            crs_list = cached_lookup(term, faculty)
            for c in crs_list:
                for i, name in enumerate(required_dict[faculty]):
                    if c.course_name in name:
                        cur_course = c
                        cur_section = required_dict[faculty][i][8:] if required_dict[faculty][i][8:] else None
                        if c.checkConfigurationNeeded(cur_section):
                            config_needed_list.append((c, cur_section))
                        else:
                            c_filtered = FilteredCourse.filterCourseBySectionCode(c, cur_section)
                            preassigned_list.append(c_filtered)
                        # required_courses.append(filtered_course)

    return config_needed_list, preassigned_list

def generate_available_courses(term: str, preassigned_list: list[FilteredCourse], preferred: str):
    '''Generate available courses for `preferred`.

    <h2>Arguments</h2>
        **term** (str): term
        **preassigned_list** (list[FilteredCourse]): list of preassigned courses. can include 
        **preferred** (str): string of preferred courses, separated by `\\n`.  
        *NOTE: priority is set here. First course should have highest priority.*
    
    <h2>Return variables</h2>
        **available_courses** (list[list[CourseComponent]]): List of list of available course components.
        **available_courses_set** (list[list[CourseComponent]]): List of available course components without any repeats.
    '''
    preferred = preferred.upper()
    preferred_courses: list[Course] = []
    preferred_dict = {}
    for faculty, course in [(course[:4], course) for course in preferred.split("\n") if course]:
        if faculty not in preferred_dict:
            preferred_dict[faculty] = []
        preferred_dict[faculty].append(course)

    # process preferred courses (it will work...?)
    if preferred:
        for faculty in preferred_dict:
            crs_list = cached_lookup(term, faculty)
            for c in crs_list:
                for i, name in enumerate(preferred_dict[faculty]):
                    if c.course_name in name:
                        preferred_courses.append(c)
    
    # alg
    timetable = Timetable()
    timetable.load_preassigned(preassigned_list)
    available_courses = []
    available_courses_set = []
    
    for course in preferred_courses:
        section_list = course.getSections()
        plausible_pairs = []
        clean_plausible_pairs = []
        all_components = []
        for i in section_list:
            components_list = course.getComponentsBySection(i)
            # check if LEC session is available
            # if not, then do not need to check because LEC must be available
            if not timetable.check_component_for_conflicts(components_list[0]):
                # ok, it's available!
                all_components += components_list
                if len(components_list) == 1:
                    # only lecture exists! time to add it to our selected courses.
                    plausible_pairs.append(makeFilteredCourse(course, components_list))
                    clean_plausible_pairs.append(components_list)
                else:
                    c_dict = sort_components_into_dicts(components_list)
                    
                    # find component type with the MAX amount of indices
                    LARGEST_KEY = MAX_LEN = -1
                    for key, items in c_dict.items():
                        # hi guys do u know that running 2 for loops is more expensive than 1 for loop? 
                        # no? well now you know!!
                        if len(items) > MAX_LEN:
                            LARGEST_KEY = key
                            MAX_LEN = len(items)

                    # this list has the components that we want to search. e.g. TUT has most components with 
                    # T01, T02, ..., T06. Using getCompsBySectCode, we can obtain pairs of components: [LEC, TUT01], [LEC, TUT02], ...
                    for i in c_dict[LARGEST_KEY]:
                        temp_comp_list = course.getComponentsBySectionCode(i.id)
                        # since this returns LEC first, we can just skip it
                        # if any is true then the sum will be larger than zero
                        if check_components_for_conflicts(timetable, temp_comp_list):
                            continue # do not proceed to scoring if it doesn't work
                        plausible_pairs.append(makeFilteredCourse(course, temp_comp_list))
                        clean_plausible_pairs.append([cmp for cmp in temp_comp_list if cmp not in flatten_2d(clean_plausible_pairs)])

        available_courses.append(plausible_pairs)
        available_courses_set.append(clean_plausible_pairs)

    return available_courses, available_courses_set

def generate_top_N(preassigned_list: list[FilteredCourse], available_courses: list[list[FilteredCourse]], N: int):
    '''Generate top N best course selections.  
    Criteria:  
    1) Amount of courses  
    2) Priority

    Args:
        preassigned_list (list[FilteredCourse]): _description_
        available_courses (list): _description_
        N (int): _description_
    '''
    # make preassigned tt
    preassigned_tt = Timetable()
    preassigned_tt.load_preassigned(preassigned_list)

    # results: min-heap
    results = []
    counter = 0 # to break ties

    def backtrack(course_index: int, tt: Timetable, selected_indices: list[int], selected_courses: list[list[CourseComponent]]):
        '''DFS of all selection cases.

        Args:
            course_index (int): current index
            tt (Timetable): timetable object to keep track of conflicts
            selected_indices (list[int]): list of indices of components that were selected
            selected_courses (list[list[CourseComponent]]): list of components that were selected
        '''
        nonlocal counter

        # base case: iterated through all of the courses
        if course_index == len(available_courses): 
            availability = sum([i.getAvailabilityRatio() for i in selected_courses]) / len(selected_courses) if selected_courses else 0
            score = [len(selected_indices), [-i for i in selected_indices], availability, random.random()] # sum smaller -> higher priority
            # push onto min-heap if score better than top of heap
            counter += 1
            # this rather scary looking branch:
            # 1: results is empty
            # 2: len(results) < N, and no. of courses ties with top
            # 3: just better than the top
            if not results or (len(results) < N and score[0] == results[0][0][0]) or score >= results[0][0]:
                heapq.heappush(results, [score, list(selected_courses)])
            if len(results) > N:
                # pop the worst score out of the heap
                # since this is a min-heap, the thing with the lowest score is placed on top
                heapq.heappop(results)
            return
        
        # case 1: select this course
        # go through all of the selected pairs, and then explore down the tree
        for fcourse in available_courses[course_index]:
            # check if there is no conflict between selection and this pair
            if check_components_for_conflicts(tt, fcourse.components):
                continue
            if fcourse.getAvailabilityRatio() == 0:
                continue

            # add to tt, selected_indices and selected_courses, check next course
            tt.load_selection(fcourse)
            selected_indices.append(course_index)
            selected_courses.append(fcourse)

            backtrack(course_index+1, tt, selected_indices, selected_courses)

            # return to original state for processing next pair
            tt.remove_selection(fcourse)
            selected_indices.pop()
            selected_courses.pop()

        # case 2: do not select course
        backtrack(course_index+1, tt, selected_indices, selected_courses)

    # do the dfs
    backtrack(0, preassigned_tt, [], [])
    # check the results, sort in DESC order of x[0] (score)
    for i in range(len(results)):
        results[i][0][1] = -sum(results[i][0][1])
    results.sort(key=lambda x: x[0], reverse=True)
    return results
    

def sort_components_into_dicts(componentList: list[CourseComponent]) -> dict:
    '''Sorts components into their categories

    Args:
        componentList (list[CourseComponent]): a list of course components (should be filtered else why are you using this function)

    Returns:
        dict: keys of this dict are the component type. values are list containing all such components
    '''
    out_dict = {} 
    for component in componentList:
        if component.type not in out_dict:
            out_dict[component.type] = [component]
        else:
            out_dict[component.type].append(component)

    return out_dict

def check_conflict_between_components(component1:CourseComponent, component2:CourseComponent)->bool:
    """
    Returns TRUE if there are any conflicts between this component and another component.
    Returns FALSE otherwise.
    """
    if component1.type == "WBL":
        return False
    tt = Timetable()
    fil_course = FilteredCourse('something')
    fil_course.components = [component1]
    tt.load_selection(fil_course)
    blocked_time = tt.convert_to_timeslot(component2.periods)
    checker = lambda d, p: 0 if p in tt.freetime[d] else 1
    result = [checker(day, period) for day in blocked_time for period in blocked_time[day]]
    return sum(result) != 0

def generate_conflicting_courses(particular_choice:list[CourseComponent], remaining_courses:list[CourseComponent]):
    """Return a list of all *component* conflicts between particular choice and remaining courses.

    Args:
        particular_choice (list): the selection in question
        remaining_courses (list): flattened list of remaining courses set

    Returns:
        conflict (list[CourseComponent]): a list of all **component conflicts**.
    """
    conflict = []
    for component1 in particular_choice:    
        for component2 in remaining_courses:
            if check_conflict_between_components(component1, component2):
                conflict.append(component2)
    return conflict

def process_programs(year: str, prog: str) -> tuple[list, list, str]:
    '''For a given year and program, return the 1st available program info.

    Args:
        year (str): Literally a year
        prog (str): Any string to be queried

    Returns:
        tuple (list, list, str): 1st is major detail, 2nd is minor detail. Can be output to label, with minor processing. 3rd is source of page.
        
        For your reference check `MajorSchemeProcessor.get_label_strings()`
    '''
    ma, mi = [], []
    
    d = get_prog_info(year, prog)
    if d == -1:
        return -1
    major_study_schemes, minor_study_schemes, src = d
    # print(minor_study_scheme)
    for a in major_study_schemes:
        try:
            m = MajorSchemeProcessor(a)
            v = m.separate_years()
            print(v)
        except StupidCUSISException:
            print("sorry, cusis is stupid, can't do anything")
            continue 
        except Exception as ex:
            print(f"unknown exception {ex}")
            continue
        ma.append(m.get_label_strings())

    return ma, mi, src

# UTIL/GENERAL FUNCS

false_true_adder = lambda i: 1 if i else 0
check_components_for_conflicts = lambda t, comps: sum([false_true_adder(t.check_component_for_conflicts(i)) for i in comps]) > 0
'''
#### ARGS: 

    t (Timetable)
    comps (list[CourseComponent])

#### RETURNS:

    TRUE if conflicts exist between this timetable and comps.
    FALSE if otherwise.
'''

def flatten_2d(l):
    return [i for j in l for i in j] # for j in l: for i in j: append i

def flatten_list(list_of_courses):
    """list_of_course: list of courses
    courses: list of pairs
    pairs: list of components
    return list of all components"""
    # this is basically a 3d flatten
    return [x_0 for x_2 in list_of_courses for x_1 in x_2 for x_0 in x_1]