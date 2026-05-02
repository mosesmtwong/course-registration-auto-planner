from modules.SchemeProcessors import *
# from helpers.scraper_helpers import *
import bs4
import io 

import tkinter as tk

def dummy_get_prog_info(year, prog):

    with open('./temp/P_info.htm', 'r') as f:
        src = io.StringIO(f.read())

    soup = bs4.BeautifulSoup(src, features='lxml')
    MAIN_T = soup.find("span", id="uc_scheme_lbl_study_scheme")
    major_study_schemes = []
    minor_study_schemes = []
    for tbl in MAIN_T.find_all("table"):
        tbl = str(tbl)
        data_frame = pd.read_html(io.StringIO(tbl))[0]
        # print(data_frame)
        # print(data_frame.isin(["Recommended Course Pattern"]).any())
        if "First  Year of Attendance" in data_frame.to_numpy().flatten():
            major_study_schemes.append(data_frame)
        elif "Minor  Programme Requirement" in data_frame.to_numpy().flatten():
            minor_study_schemes.append(data_frame)

    return major_study_schemes, minor_study_schemes

def process_programs(year: str, prog: str) -> tuple[list, list]:
    ma, mi = [], []
    major_study_schemes, minor_study_schemes = dummy_get_prog_info(year, prog)
    # print(minor_study_scheme)
    for a in major_study_schemes:
        a = MajorSchemeProcessor(a)
        try:
            v = a.separate_years()
        except StupidCUSISException:
            print("sorry, cusis is stupid, can't do anything")
            continue 
        except Exception as ex:
            print(f"unknown exception {ex}")
        ma.append(a.get_label_strings())
    return ma, mi

ma, mi = process_programs('2024', 'Computer Science')
for i in ma:
    for year in range(len(i)):
        print(f'Year {year+1}')
        for term in range(len(i[year])):
            print(i[year][term])
            # print(f'Term {term+1}')
            # print(('\n').join(i[year][term]))