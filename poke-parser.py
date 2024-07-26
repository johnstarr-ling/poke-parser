import os
import sys
import re
import argparse
import numpy as np 
import pandas as pd 



##### ARGUMENT PARSER #####
parser = argparse.ArgumentParser(description='Process Pokemon Showdown HTML files in batches.')

parser.add_argument('path', metavar='PATH',
                    help='Path to HTML file(s).')

parser.add_argument('-w', '--weeks', action='store_true',
                   help='Process files in weeks; assumes PATH location is a directory of directories.')

parser.add_argument('-ao', '--agg_out', action='store_true',
                    help='Generate only aggregate output.')

parser.add_argument('-wo', '--week_out', action='store_true',
                    help='Generate only weekly output.')

args = parser.parse_args()

WEEKLY = False
PATH = args.path

if args.weeks:
    WEEKLY = True 


##### GLOBAL CONTAINERS #####

# Getting name & number of players:
players = set()

if WEEKLY:
    weeks = os.listdir(PATH)
    players_raw = os.listdir(f'{PATH}/{weeks[0]}') # Assumes that there are no player changes after the first week
    
    for fn in players_raw:
        split_fn = fn.split('-')
        players.add(split_fn[4])
        players.add(split_fn[5][:-5]) # Dropping the .html off the last name

else:
    for fn in os.listdir(PATH):
        split_fn = fn.split('-')
        players.add(split_fn[4])
        players.add(split_fn[5][:-5]) # Dropping the .html off the last name


# Developing base array of shape N (num weeks) x P (num players) x C (aggregate statistics for desired categories); if WEEKLY = False, then N=1  
category_list = ['chat_num', 'chat_len', 'joined', 'gender', 'hazarder', 'statuser']
categories = {value[1]:value[0] for value in enumerate(category_list)}

num_players = len(players) 
num_weeks = 1 

if WEEKLY:
    num_weeks = len(weeks) # Re-assigning the number of weeks

base_array = np.zeros((num_weeks, num_players, len(list(categories))))

# Creating a dictionary which maps players to a unique index; can be used for base_array:
idx_2_player = {item[0]:item[1] for item in enumerate(sorted(players))}
player_2_idx = {item[1]:item[0] for item in idx_2_player.items()}







##### HTML FUNCTIONS #####

# ----- CLEANING ----- #
def get_player_names(line_player_name):
    """"
    line_player_name (str) -> String of format: '|player|p#|NAME|avatar'
    """
    
    line_split = line_player_name.split('|')
    return line_split[2], {line_split[2]:line_split[3].lower()} # Maps p# to NAME


def check_gender(string):
    """
    string (str) -> String of pokemon names
    """
    if ', F' in string:
        return 'Female'
    elif ', M' in string:
        return 'Male'
    else:
        return 'NONE'


def get_pokemon(line_pokemon):
    """"
    line_pokemon (str) -> String of format: '|poke|p#|Name(, Gender)(|item)
    """
    
    line_split = line_pokemon.split('|')
    return line_split[2], line_split[3].split(',')[0], check_gender(line_split[3]) # Return player_id, cleaned_pokemon name, gender

    

def clean_html(filename):
    """
    filename (str) -> Name of file; does not include PATH
    """

    with open(f'{PATH}/{filename}') as f:
        html_raw = f.readlines()

    # Removing html information 
    html_cleaned = html_raw[16:] 
    
    # Getting players and creating base dictionary for each player 
    player_dict = {}
    for line_player_name in html_cleaned[:2]:
        player_id, player_map_dict = get_player_names(line_player_name)
        player_dict.update(player_map_dict)
        player_dict[player_id] = {'pokemon':set(),
                                  'genders':{'Male':0, 'Female':0, 'NONE':0},
                                  'status':{},
                                  'hazards':set(),
                                  'healer':{}}
    # Removing rules:
    html_cleaned = html_cleaned[17:]

    # Adding Pokemon
    for line in html_cleaned[:12]: # Assumes that all teams have 6 pokemon
        player_id, pokemon_name, pokemon_gender = get_pokemon(line)
        player_dict[player_id]['pokemon'].add(pokemon_name)
        player_dict[player_id]['genders'][pokemon_gender] += 1 
    
    # Keeping only match output
    start_idx = html_cleaned.index('|teampreview\n')
    html_cleaned = html_cleaned[start_idx:-8]
    
    return player_dict, html_cleaned



# ----- PARSING ----- # 

def add_join(line_join, base_array=base_array, week=0):
    """
    base_array (arr) -> Statistics array
    line_join (str) -> Line indicating that someone joined of format |j| NAME
    """
    name = line_join.split('|j|').strip().lower()
    base_array[week, player_2_idx[name], categories['joined']] += 1  # Tracks who joined the most
    

def add_chat(line_chat, base_array=base_array, week=0):
    """
    base_array (arr) -> Statistics array    
    line_chat (str) -> Line indicating that someone chatted of format |c|NAME|chat
    """
    name, chat = line_chat.split('|')[2:]
    base_array[week, player_2_idx[name.lower()], categories['chat_num']] += 1  # Tracks who chatted the most (by number of chats) 
    base_array[week, player_2_idx[name.lower()], categories['chat_len']] += len(chat)  # Tracks who chatted the most (by length)


def calculate_damage(variable):
    pass


def parse_html(base_array, player_dictionary, cleaned_html, week=0):
    
    for line in cleaned_html:
        pass









test_dict, test_html = clean_html('Gen6Draft-2024-05-16-sonofringo-crystopperpkmn.html')





##### THINGS TO ADD ###### 
# Most & least damage giver (how much percent they gave out)
# Most & least damage taker (how much percent they took)
# Biggest healer (account for healing wish and wish?)
# Pokemon gender users (most feminist)
# Most popular items ?
# Most improved (aka stat buffs)
# Most toxic damage giver/damage?
