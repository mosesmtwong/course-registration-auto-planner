import pandas as pd
import numpy as np

class StupidCUSISException(Exception):
    '''Should be raised when it's CUSIS's fault and not yours.'''
    pass

class MajorSchemeProcessor:
    # Define constants
    YEAR_MAP = {"First":1, "Second":2, "Third":3, "Fourth":4, "Fifth":5}
    year_data = None

    def __init__(self, table: pd.DataFrame):
        table = table.to_numpy()
        format_tbl = lambda s: str(s).replace('  ', ' ').replace('nan', '').replace('/ ','/')
        self.table = [[format_tbl(s) for s in row] for row in table]
        self.table = np.array(self.table)
        if len(table[0]) == 3:
            col_names = ["year", "info", "units"]
        elif len(table[0]) > 3:
            col_names = ["year", "info", "units"]
            for n in range(0, (len(table[0]) - 3 + 1) // 2):
                col_names += [f"info{n+1}", f"units{n+1}"]
        else:
            raise Exception("Weird structure? Cols should be (n-3) % 2 == 0.")
        self.frame = pd.DataFrame(self.table, 
                                  columns = col_names)

    def separate_years(self) -> list:
        '''Returns a list of the study pattern for each year. Also updates the attribute `self.year_data` with the study pattern returned.

        ```FORMAT: 

        [
            (year 1) [T1_DATA, T2_DATA],
            (year 2) [T1_DATA, T2_DATA],
            ...
        ]
        ```
        '''
        # get first year of attendance, second year of attendance, etc.
        query_words = list(set([str(s) for s in self.table[:, 0] if 'Year' in str(s)]))
        # print(query_words)
        # print(self.frame)
        
        l = ['a' for _ in range(len(query_words))]
        
        for i in range(len(query_words)):

            word = query_words[i]
            fframe = self.frame.loc[self.frame["year"] == word]
            try:
                idx_1 = int(fframe.index[fframe.isin(["1st term"]).any(axis=1)].to_list()[0]) # get (all, but guaranteed to be only 1) occurence of term 1
                idx_2 = int(fframe.index[fframe.isin(["2nd term"]).any(axis=1)].to_list()[0]) # likewise for term 2
                idx_3 = max(fframe.index) # get final pos
            except:
                raise StupidCUSISException("not my fault, it's CUSIS fault for making the thing like not work lol")
            t1_data = self.frame[idx_1+1: idx_2] # term 1 data is 1 row after t1 occurence to t2-1 (since python is not inclusive at end, we can put t2 index)
            t2_data = self.frame[idx_2+1: idx_3+1] # likewise, but idx3 is the final pos, so need to +1 for all inclusiveness.
            # print('\n\n\nT1')
            # print(t1_data)
            # print('\n\nT2')
            # print(t2_data)
            t1_data = self.process_term_data(t1_data)
            t2_data = self.process_term_data(t2_data)

            insert_index = self.YEAR_MAP[word.split(' ')[0]] - 1
            l[insert_index] = [t1_data, t2_data]

        self.year_data = l

        return l

    def get_label_strings(self) -> list:
        '''Wrapper for `year_data_to_readable`. Please call this instead of the internal function.
        
        RETURNS: list. Format below:
        ```[
        (year1): [T1_data, T2_data],
        (year2): [T1_data, T2_data],
        ...

        where T1_data and T2_data are [maj1_str, maj2_str, ...]
        ]
        ```
        '''

        return [self.year_data_to_readable(year) for year in self.year_data]

    def process_term_data(self, data: pd.DataFrame) -> tuple[dict, dict]:
        '''Internal function, processes a filtered table into two parts for use.

        Args:
            data (pd.DataFrame): filtered frame containing course data only.

        Returns:
            tuple[dict, dict]: 1st dict contains courses required. 2nd dict contains credit count. Ordering is identical in both dicts.

        Note:
            It is guaranteed that the major program for 1st degree will come first in the case of double degree option.
            To preserve ordering, repetitions may be present. **YOU SHOULD CHECK FOR REPETITIONS!!**
        '''

        out_dict = {}
        unit_dict = {}
        for idx, row_data in data.iterrows():
            # print(row_data)
            for col in range(1, len(row_data), 2):
                if f'info{col//2}' not in out_dict:
                    out_dict[f"info{col//2}"] = [row_data.to_numpy()[col]]
                else:
                    out_dict[f'info{col//2}'].append(row_data.to_numpy()[col])

                if f'info{col//2}' not in unit_dict:
                    unit_dict[f'info{col//2}'] = [row_data.to_numpy()[col+1]]
                else:
                    unit_dict[f'info{col//2}'].append(row_data.to_numpy()[col+1])

        return out_dict, unit_dict

    def year_data_to_readable(self, year_data) -> list:
        '''Internal function. Process year data into readable format.

        Args:
            year_data (list): Each element in separate_years.

            
        Returns:
            list: Format below.
            ```
            list: [T1_data, T2_data]
            where T1_data and T2_data look like: [maj1_str, maj2_str, ...]
            ```
        '''
        t = []
        for term in year_data:
            
            info_dict, unit_dict = term
            KEY_LIST = list(info_dict.keys())
            out_strs = [[] for _ in range(len(KEY_LIST))]
            for key in info_dict:
                cur_idx = KEY_LIST.index(key)
                for cur_info, cur_unit_d in zip(info_dict[key] , unit_dict[key]):
                    if (cur_info, cur_unit_d) in out_strs[cur_idx] or cur_unit_d in out_strs[cur_idx]:
                        continue 
                    else:
                        out_strs[cur_idx].append((cur_info, cur_unit_d))

                _temp_strs = [f"Major {cur_idx+1}"]
                for pair in out_strs[cur_idx]:
                    
                    if not pair[0]:
                        if len(_temp_strs) == 1: _temp_strs.append(f"NO DATA")

                    elif "Major Required" in pair[0] and "Major Elective(s)" in pair[0]:
                        # bad string

                        sp_data = pair[0].split("Major Required:")
                        fac_package = sp_data[0]
                        sp_data = sp_data[1].split("Major Elective(s):")
                        maj_required = sp_data[0].strip()
                        maj_electives = sp_data[1].strip()

                        credit_info = pair[1].split(' ')
                        req_idx = 1
                        elec_idx = 2
                        # basically, this is just shifting the credit info forward
                        if fac_package and 'Faculty Package' in fac_package:
                            _temp_strs.append(f'{fac_package.strip()} ({credit_info[0] if credit_info[0] else 0} credits)')
                        elif fac_package:
                            _temp_strs.append(fac_package.strip())
                            req_idx = 0
                            elec_idx = 1
                        else:
                            # maj_required and maj_electives only
                            # _temp_strs.append('Faculty Package: (0 credits)')
                            req_idx = 0
                            elec_idx = 1
                        if maj_required:
                            _temp_strs.append(f'Major Required: {maj_required} ({credit_info[req_idx]} credits)')
                        else:
                            _temp_strs.append("Major Required: (0 credits)")
                            elec_idx = 0
                        if maj_electives:
                            if elec_idx < len(credit_info):
                                _temp_strs.append(f'Major Elective(s): {maj_electives} ({credit_info[elec_idx]} credits)')
                        else:
                            _temp_strs.append("Major Elective(s): (0 credits)")

                    else:
                        # string is read correctly, proceed to format
                        if not pair[1].strip():
                            _temp_strs.append(f'{pair[0]} (0 credits)')
                            continue

                        _temp_strs.append(f'{pair[0]} ({pair[1]} credits)')
                    
                out_strs[cur_idx] = ('\n').join(_temp_strs)
            t.append(out_strs)

        return t