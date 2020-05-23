import re
import pandas as pd 
import numpy as np 
import os
import pickle
import time
import math

if not os.path.isdir('data'):
    os.mkdir('data')

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def is_float(s):
    try: 
        float(s)
        return True
    except ValueError:
        return False

def remove_entry(df, minute, second, ms, zone, pkl_path):
    start = '{:02d}:{:02d}:{:03d}'.format(minute,second,ms)

    ind = np.where((df['start_time']==start) & (df['zone']==zone))

    if len(ind[0]) == 0:
        print("Entry not in table. Please try again.")
        return df
    
    df = df.drop(df.index[ind])

    if not df['end_time'].isnull().all():
        df = df.replace({'end_time': {start: np.NaN}})
    df.to_pickle(pkl_path)

    return df

def input_entry(df, minute, second, ms, zone, pkl_path):    
    time_str = '{:02d}:{:02d}:{:03d}'.format(minute,second,ms)
    print("Inputting: Start time of {} in Zone {}".format(time_str, zone))
    
    if not df.empty:
        df.iloc[-1]=[df.iloc[-1].ix['start_time'], time_str ,df.iloc[-1].ix['zone']] 
    
    new_row = {'start_time': time_str, 'end_time':np.NaN, 'zone': zone}
    df = df.append(new_row, ignore_index=True)

    df.to_pickle(pkl_path)

    return df

def print_session(df):
    print(df)
    return True

def exit_session(df, pkl_path):
    print("Exiting Session...")
    time.sleep(1)
    df.to_pickle(pkl_path)
    exit(0)

def overwrite_pickle(df, pkl_path):
    df = df.from_csv(pkl_path[:-3]+"csv")
    df.to_pickle(pkl_path)

    return df

def compute_minute(x):
    if(is_float(x)):
        if(math.isnan(float(x))):
            return np.NaN
    
    [min, sec, ms] = [int(i) for i in x.split(":")]
    return min + sec / 60 + ms / 60000

def convert_str(fl):
    min = int(fl)
    sec = int((fl - min) * 60)
    ms = int((fl - (min + sec / 60)) * 60000)

    # get rid of 99's from rounding
    if (ms % 100) == 99:
        ms += 1

        if ms == 1000:
            ms = 0
            sec += 1

            if sec == 60:
                sec = 0
                min += 1

    
    return '{:02d}:{:02d}:{:03d}'.format(min, sec, ms)

def compute_time(df, rat_n, train_day):
    row_names = ['0-5m', '5-10m', '10-15m', '15-20m', '20-25m', '25-30m']
    col_names = list(np.arange(9) + 1)
    df_res = pd.DataFrame(index=row_names, columns=col_names)

    for zone_n in range(1,10):
        for i in range(6):
            lower_b = i*5
            upper_b = (i+1)*5

            df_time = df.copy()
            df_time.start_time = df_time.start_time.apply(compute_minute)
            df_time.end_time = df_time.end_time.apply(compute_minute)

            # Collect all rows with some length of time within the time bounds
            df_subset = df_time.loc[((df_time.start_time >= lower_b) & (df_time.end_time < upper_b) & (df_time.zone == zone_n))
                | ((df_time.start_time < upper_b) & (df_time.end_time >= upper_b) & (df_time.zone == zone_n))
                | ((df_time.start_time < lower_b) & (df_time.end_time >= lower_b) & (df_time.zone == zone_n))
            ]
            
            row_n = '{}-{}m'.format(lower_b,upper_b)

            # Running sum
            sum = 0
            for _, row in df_subset.iterrows():
                sum += (min(upper_b, row['end_time']) - max(lower_b, row['start_time']))

            # Update result data frame
            sum = convert_str(sum)
            df_res.at[row_n, zone_n] = sum
    
    print(df_res)
    time_path = 'data/{}_{}_times.csv'.format(rat_n, train_day)
    df_res.to_csv(time_path)
    print("Saving to {}...".format(time_path))


def compute_entry(df, rat_n, train_day):
    df_res = pd.DataFrame()

    for zone_n in range(1,10):
        for i in range(6):
            lower_b = i*5
            upper_b = (i+1)*5

            df_time = df.copy()
            df_time.start_time = df_time.start_time.apply(compute_minute)
            df_time.end_time = df_time.end_time.apply(compute_minute)

            # Collect all rows with some length of time within the time bounds
            df_subset = df_time.loc[((df_time.start_time >= lower_b) & (df_time.end_time < upper_b) & (df_time.zone == zone_n))
                | ((df_time.start_time < upper_b) & (df_time.end_time >= upper_b) & (df_time.zone == zone_n))
            ]

            row_n = '{}-{}m'.format(lower_b,upper_b)

            # Update result data frame
            df_res.at[row_n, zone_n] = df_subset.shape[0]
    
    print(df_res)
    time_path = 'data/{}_{}_enters.csv'.format(rat_n, train_day)
    df_res.to_csv(time_path)
    print("Saving to {}...".format(time_path))

def output_csv(df, pkl_path):
    df.to_pickle(pkl_path)
    df.to_csv(pkl_path[:-3] + "csv")

def help_fn():
    print("Help Guide: neuro-zone-tracker")
    print("------------------------------\n")
    print("MM.SS[.LLL] Z     : Rat enters zone Z at time MM:SS:LLL. Milliseconds L is optional")
    print("print             : print the current state of the DataFrame")
    print("del MM.SS[.LLL] Z : Delete specified entry from DataFrame")
    print("csv               : Save DataFrame to csv")
    print("exit              : Exit neuro-zone-tracker")
    print("overwrite         : Overwrite DataFrame with CSV (for manual correction)")
    print("help              : Print this help guide")
    print("computetime       : Compute the Matrix of times in which the rat was in each zone (for each 5 minute time interval)")
    print("computeentry      : Compute the Matrix of counts for which the rat entered each zone (for each 5 minute time interval)")


def start_rat_session(rat_n, train_day):
    print("Rat {} data-entry session started for Training day {}.".format(rat_n, train_day))
    pkl_path = 'data/{}_{}.pkl'.format(rat_n, train_day)

    if os.path.exists(pkl_path):
        print('Rat session {}, Training day {} already exists. Resuming session...'.format(rat_n, train_day))
        df = pd.read_pickle(pkl_path)

    else:
        df = pd.DataFrame(columns = ['start_time', 'end_time', 'zone'])
        df.to_pickle(pkl_path)

    while True:
        user_input = input("> ")

        # test if input
        pattern = re.compile(r"^(?P<command>[a-z]+)?\s?(?P<input>(?P<min>[0-9]+)\.(?P<sec>[0-9]+)\.?(?P<ms>[0-9]*)\s(?P<zone>[1-9]))?$")
        match_obj = pattern.match(user_input)

        if(match_obj is None):
            print("Charithe, this input is not valid. Do better.")
            continue
        
        # You have given an input
        elif((match_obj.group("command") is None) and not(match_obj.group("input") is None)):
            if match_obj.group("ms"):
                ms = int(match_obj.group("ms"))
            else:
                ms = 0
            df = input_entry(df, int(match_obj.group("min")), 
                int(match_obj.group("sec")), ms, int(match_obj.group("zone")), pkl_path)

        elif(match_obj.group("command") == 'print'):
            print_session(df)

        elif(match_obj.group("command") == 'exit'):
            exit_session(df, pkl_path)

        elif(match_obj.group("command") == 'csv'):
            output_csv(df, pkl_path)

        elif(match_obj.group("command") == "overwrite"):
            df = overwrite_pickle(df, pkl_path)

        elif(match_obj.group("command") == 'computetime'):
            compute_time(df, rat_n, train_day)

        elif(match_obj.group("command") == 'computeentry'):
            compute_entry(df, rat_n, train_day)

        elif(match_obj.group("command") == 'help'):
            help_fn()

        elif(match_obj.group("command") == 'del' and not(match_obj.group("input") is None)):
            if match_obj.group("ms"):
                ms = int(match_obj.group("ms"))
            else:
                ms = 0
            df = remove_entry(df, int(match_obj.group("min")), 
                int(match_obj.group("sec")), ms, int(match_obj.group("zone")), pkl_path)
        
        else:
            print("Charithe, this input is not valid. Do better.")
    

def start_session():
    print("To start a data-entry session, please input a Rat Number followed by Training Day (space separated)...")

    while(True):
        ip = input("> ")
        ip = ip.split(" ")
        if(not len(ip) == 2):
            print("Charithe, Charithe, Charithe. This is not a valid input. Please try again.")
            continue
        if(not(is_int(ip[0]) and is_int(ip[1]))):
            print("Charithe, Charithe, Charithe. This is not a valid input. Please try again.")
            continue
        start_rat_session(int(ip[0]), int(ip[1]))

if __name__ == "__main__":
    start_session()