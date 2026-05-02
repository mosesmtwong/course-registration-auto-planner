from modules.course import *
from utils.scraper import lookup, fill_webform_prog, get_webdriver_instance
import json, os, io
import requests, bs4
import pandas as pd
from selenium.webdriver import Chrome, ChromeOptions
import time 


def get_current_terms() -> dict:
    """Generates a dictionary that has the human-readable term names and term id from CUSIS.

    Returns:
        dict: {"24-25 Term 2": 2370, ...}
    """

    htmldoc = requests.get(
        "https://rgsntl.rgs.cuhk.edu.hk/rws_prd_applx2/Public/tt_dsp_timetable.aspx"
    )
    htmldoc = htmldoc.content
    soup = bs4.BeautifulSoup(htmldoc, features="lxml")

    term_dict = {
        i.text: i["value"]
        for i in soup.find("select", {"id": "ddl_acad_term"})
        if i != "\n"
    }
    return term_dict


def get_current_courses() -> list[str]:
    """Returns a list of faculties/Course offering departments. e.g. AIST, ACCT, FINA, ECON.

    Returns:
        list: ['ACCT', 'AIST', ...]
    """
    htmldoc = requests.get(
        "https://rgsntl.rgs.cuhk.edu.hk/rws_prd_applx2/Public/tt_dsp_timetable.aspx"
    )
    htmldoc = htmldoc.content
    soup = bs4.BeautifulSoup(htmldoc, features="lxml")

    fac_list = [
        i["value"] for i in soup.find("select", {"id": "ddl_subject"}) if i != "\n"
    ][1:]
    return fac_list


def split_courses(course_list: list[Course]) -> dict:
    """Spits out the course codes and sessions for each course.

    Args:
        course_list (list[Course]): A list outputted by utils.scraper.lookup.

    Returns:
        dict: The keys of this dict are the course codes, and the values of this dict are the respective sessions.
    """

    return {course.course_name[4:]: course.getSections() for course in course_list}


def create_cache_file(dir="./temp/cache.json"):
    """Do I really need to explain

    Args:
        dir (str, optional): Path of cache file. No need to fill in file extension.
        If "accidentally" filled in there is no problem as well.

        The default location of the cache file is at temp/cache.json.
    """

    # dir = dir.strip(".json")
    # with open(f"{dir}.json", "w") as f:
    # f.write("{}")  # empty file
    f = open(f"{dir}", "w")
    f.write("{}")
    f.close()


def delete_cache_file(dir="./temp/cache.json"):
    """part 2 in Do I really need to explain

    Args:
        dir (str, optional): Path of cache file. No need to fill in file extension.
        If "accidentally" filled in there is no problem as well.

        The default location of the cache file is at temp/cache.json.
    """

    dir = dir.strip(".json")
    os.remove(f"{dir}.json")


def cache_faculty(term: str, faculty: str, data: list[Course], cache_dir="./temp/cache.json") -> None:
    """Push data provided by scraper.lookup into cache.

    Args:
        term (str): term id provided to lookup
        faculty (str): faculty code provided to lookup
        data (list[Course]): data returned by lookup
        cache_dir (str, optional): FULL path of the cache file. Defaults to './temp/cache.json'.

    Cache formatting
        The cache file is a dict. First layer is term_id, second layer is faculty, and the value of 2nd layer is the
        to_dict version of the courses outputted by lookup.
    """

    # read file contents
    with open(cache_dir, "r") as f:
        cache_contents = json.load(f)

    # update with cache stuff
    if term not in cache_contents:
        cache_contents[term] = {}
    cache_contents[term][faculty] = [i.to_dict() for i in data]

    # close file
    with open(cache_dir, "w") as f:
        json.dump(cache_contents, f)


def cached_lookup(term: str, faculty: str, cache_dir="./temp/cache.json") -> list[Course]:
    """Basically the same as lookup except with cache functionality implemented
    Unless you are forcing a refetch from web you should ALWAYS call this function to get course data

    Args:
        course (str): 4-character id of course. For example: ENGG, MATH, FINA
        term (str): the term id from the CUSIS system. use webscraping to get this number. Should be 4 digits.
        cache_dir (str, optional): Unless you have updated the cache location, this should be set to the default.

    Returns:
        list[Course]: its a fucking list of course objects
    """

    if not os.path.isfile(cache_dir):
        create_cache_file()
    with open(cache_dir, "r") as f:
        cache_contents = json.load(f)

    if term in cache_contents:
        if faculty in cache_contents[term]:

            course_list_json = cache_contents[term][faculty]
            course_list = [Course.from_dict(i) for i in course_list_json]

            return course_list

    course_list = lookup(faculty, term)

    # Update cache
    cache_faculty(term, faculty, course_list, cache_dir=cache_dir)

    return course_list

def get_prog_info(year: str, program: str):
    '''Wrapper function for fill_webform_prog. Gets program information for given year and program.

    Args:
        Refer to fill_webform_prog in `scraper.py`

    Returns:
        list, list, str: 1st list is major_study_schemes, 2nd is minor_study_schemes , 3rd is page src.
        (technically, there is no study scheme for minor. it is more of a requirement list.)
    '''

    driver = get_webdriver_instance()
    PROG_INFO_URL = 'https://rgsntl.rgs.cuhk.edu.hk/aqs_prd_applx/Public/tt_dsp_acad_prog.aspx'
    driver.get(PROG_INFO_URL)
    driver.implicitly_wait(2)
    src = None
    errs = 0
    while not src:
        src = fill_webform_prog(year=year, program=program, driver=driver)
        errs += 1
        if errs > 100:
            raise Exception("WTF IS HAPPENING ?????? 100 ERRORS ???")
    
    if src == -1:
        return -1

    soup = bs4.BeautifulSoup(src, features='lxml')
    MAIN_T = soup.find("span", id="uc_scheme_lbl_study_scheme")
    major_study_schemes = []
    minor_study_schemes = []
    for tbl in MAIN_T.find_all("table"):
        tbl = str(tbl)
        data_frame = pd.read_html(io.StringIO(tbl))[0]
        # print(data_frame)
        # print(data_frame.isin(["Recommended Course Pattern"]).any())
        word_list = data_frame.to_numpy().flatten()
        word_list = [str(i).replace('  ', ' ') for i in word_list]
        # Fucking gay FAculty of ENGINEER ING !@ #)(@*#()*!(@)*!()@*( )!@)_!@@40@)_#)_!)_@)_
        if "First Year of Attendance" in word_list:
            major_study_schemes.append(data_frame)
        elif "Minor Programme Requirement" in word_list:
            minor_study_schemes.append(data_frame)

    return major_study_schemes, minor_study_schemes, src