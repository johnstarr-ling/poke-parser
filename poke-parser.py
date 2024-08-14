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

HOME = os.getcwd()

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
category_list = ['chat_num', 'chat_len', 'joined', 'male_mons', 'female_mons', 'non-binary_mons']
categories = {value[1]:value[0] for value in enumerate(category_list)}

num_players = len(players) 
num_weeks = 1 

if WEEKLY:
    num_weeks = len(weeks) # Re-assigning the number of weeks

base_array = np.zeros((num_players, len(list(categories))))

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
    return line_split[2], {line_split[2]:line_split[3].lower().replace('_', '')} # Maps p# to NAME


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
    if 'Greninja' in line_pokemon:
        return line_split[2], 'Greninja', check_gender(line_split[3]) # Return player_id, cleaned_pokemon name, gender

    else:
        return line_split[2], line_split[3].split(',')[0], check_gender(line_split[3]) # Return player_id, cleaned_pokemon name, gender

def get_nickname(line_switch, name_dict):
    """
    line_switch (str) -> Line indicated that a Pokemon switched in of format |switch|p#: NICKNAME|NAME(, GENDER)|HEALTH
    """
    nickname, name = line_switch.split('|')[2:4]
    nickname = ' '.join(nickname.split()[1:]) # Keeping everything after p#:
    # Getting name without gender
    if ',' in name:
        name = name.split(',')[0]
    
    # Only targeting mons that have nicknames
    if nickname!=name and nickname not in name_dict:
        name_dict[nickname] = name 

   
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
        player_dict[player_id] = {'name':player_map_dict[player_id],
                                  'pokemon':set(),
                                  'genders':{'Male':0, 'Female':0, 'NONE':0},
                                  'status':{},
                                  'hazards':set(),
                                  'healer':{}}
    # Removing rules and stripping whitespace:
    html_cleaned = [line.strip() for line in html_cleaned[17:] if line != '|\n']
    

    # Adding Pokemon
    for line in html_cleaned[:12]: # Assumes that all teams have 6 pokemon
        player_id, pokemon_name, pokemon_gender = get_pokemon(line)
        player_dict[player_id]['pokemon'].add(pokemon_name)
        if pokemon_gender == 'Male':
            base_array[player_2_idx[player_dict[player_id]['name'].replace(' ', '')], categories['male_mons']] += 1
        elif pokemon_gender == 'Female':
            base_array[player_2_idx[player_dict[player_id]['name'].replace(' ', '')], categories['female_mons']] += 1
        else:
            base_array[player_2_idx[player_dict[player_id]['name'].replace(' ', '')], categories['non-binary_mons']] += 1 


    # Keeping only match output
    start_idx = html_cleaned.index('|teampreview')
    html_cleaned = html_cleaned[start_idx:-8]
    
    # Merging |-damage| line to the previous ones (including supereffective, crit, and move used) to ease damage calcs
    damage_line_idxs = []
    damage_markers =  {'-supereffective', '-crit', '-resisted'}
    for i in range(len(html_cleaned)):
        if any(marker in html_cleaned[i] for marker in damage_markers):
            damage_line_idxs.append(i)
        elif '|-damage|' in html_cleaned[i] and '[from]' not in html_cleaned[i]:   # Removing from marker, as we are looking at attack damage
            damage_line_idxs.append(i)   
    
    # Looping through damage and making strings easier to parse (can split on '$$$')
    for idx in reversed(damage_line_idxs):
        previous_line = html_cleaned[idx-1]
        target_line = html_cleaned[idx]
        html_cleaned[idx-1] = f'{previous_line} &&& {target_line}'
    
    # Getting nicknames:
    name_dict = {}
    switch_lines = [get_nickname(line, name_dict) for line in html_cleaned if line.startswith('|switch')]
    
    # Replacing nicknames -- this is slow theoretically but I'm too lazy to figure out a significantly faster approach
    for idx in range(len(html_cleaned)):
        for nickname, name in name_dict.items():
            html_cleaned[idx] = re.sub(nickname, name, html_cleaned[idx])
    return player_dict, html_cleaned



# test_dict, test_html = clean_html('Gen6Draft-2024-06-10-notabot1234-kaisercauto.html')




# ----- PARSING STATISTICS ----- # 

# def add_join(line_join, base_array=base_array, week=0):
  #  """
  #  base_array (arr) -> Statistics array
  #  line_join (str) -> Line indicating that someone joined of format |j| NAME
  #  """
  #  name = ''.join(line_join.split('|j| ')[1].strip().lower().split()).replace('☆', '').replace('_', '')
  #  if name in player_2_idx:
  #      base_array[player_2_idx[name], categories['joined']] += 1  # Tracks who joined the most

def add_chat(line_chat, base_array=base_array, week=0):
    """
    base_array (arr) -> Statistics array    
    line_chat (str) -> Line indicating that someone chatted of format |c|NAME|chat
    """
    name, chat = line_chat.split('|')[2:]
    name = ''.join(name).strip().lower().replace('☆', '').replace('_', '').replace(' ','')

    if name in player_2_idx:
        base_array[player_2_idx[name.lower()], categories['chat_num']] += 1  # Tracks who chatted the most (by number of chats) 
        base_array[player_2_idx[name.lower()], categories['chat_len']] += len(chat)  # Tracks who chatted the most (by length)


def get_main_damage(line_attack, health_dict):
    """
    line_attack (str) -> Line indicating attack damage of format |move|p#: ATTACKER|MOVE|TARGET |-MARKERS|...|-damage|p#: TARGET|health
    """
    
    # Finding who the attacker and targets are 
    line_attack_split = line_attack.split('|')
    
    # Skipping over substitute lines:
    if 'damage' not in line_attack:
        attack_mon = line_attack_split[2].split('a: ')[1]
        target_mon = line_attack_split[-1].split('a: ')[1]
        return ((attack_mon, 0), (target_mon, 0)) 
    
    else:
        attack_mon = line_attack_split[2].split('a: ')[1] # Saving player who attacked and Pokemon who attacked
        target_mon = line_attack_split[-2].split('a: ')[1] # Saving targeted player and target Pokemon
    
    
    # Calculating damage:
    if 'fnt' in line_attack:
        new_health = 0 
    else:
        new_health = int(line_attack_split[-1].split('/')[0][:-1])

    old_health = health_dict[target_mon]
    health_diff = old_health - new_health 
    health_dict[target_mon] = new_health
    
    return ((attack_mon, health_diff), (target_mon, -health_diff)) # Returning tuples of stats to add
    
    
def get_health_change(line_change, health_dict):
    """
    line_change (str) -> line of format |-CATEGORY|p#: MON|HP\/100 
    health_dict (dict) -> dictionary of current health of Pokemon in match 
    """
    
    # Note that this accounts for health changes of all kinds:
    # damage, healing, statuses, items, etc. 
    line_change_split = line_change.split('|')
    pokemon = line_change_split[2].split()[1]

    if 'fnt' in line_change:
        new_health = 0
    else:
        new_health = int(line_change_split[3].split('/')[0][:-1])
    
    old_health = health_dict[pokemon]
    health_diff = new_health-old_health # Getting the difference 
    health_dict[pokemon] = new_health
    return pokemon, health_diff 


def get_buff(line_buff, set_boost):
    """
    line_buff (str) -> line of format |-boost|p#: MON|stat|#boost
    """

    line_buff_split = line_buff.split('|')
    pokemon = line_buff_split[2].split()[1]

    if set_boost == 'cupcake!':
        buff = line_buff_split[4] # Accounting for things like Belly Drum
    elif '[from] item:' in line_buff:
        buff = line_buff_split[4]
    else:
        buff = line_buff_split[-1]

    return pokemon, int(buff)

def make_match_dataframe(mons2idx, stats2idx, mon_array, week,mons2player):
    df = pd.DataFrame(mon_array, 
                      index=mons2idx.keys(), 
                      columns=stats2idx.keys())
    df = df.reset_index()
    df['week'] = week
    df['trainer'] = df['index'].apply(lambda x: mons2player[x])
    return df


def parse_html(base_array, match_dict, match_html, week):

    # Choosing the stats we want to track
    tracked_stats = ['damage_given',
                     'damage_received',
                     'damage_healed',
                     'toxic_damage_taken', 
                     'hazard_damage_taken',
                     'burn_damage_taken', 
                     'poison_damage_taken',
                     'life_orb_damage_taken', 
                     'stealth_rock_damage_taken', 
                     'spike_damage_taken',
                     'buff_received',
                     'recoil_damage_taken']
    
    stats2idx = {item[1]:item[0] for item in enumerate(tracked_stats)}
    
    # Creating arrays for each player and their team that we can update later
    # p1_mons2idx = {item[1]:item[0] for item in enumerate(match_dict['p1']['pokemon'])}
    # p2_mons2idx = {item[1]:item[0] for item in enumerate(match_dict['p2']['pokemon'])}
    # p1_match_array = np.zeros((len(p1_mons2idx), len(stats2idx)))
    # p2_match_array = np.zeros((len(p2_mons2idx), len(stats2idx)))
    
    # Making a dictionary that gives unique index to each mon in match
    p1_mons = [mon for mon in match_dict['p1']['pokemon']]
    p2_mons = [mon for mon in match_dict['p2']['pokemon']]
    total_mons = p1_mons+p2_mons
    mons2idx = {item[1]:item[0] for item in enumerate(total_mons)}
    
    # Making an array that keeps track of stat changes 
    mon_array = np.zeros((len(mons2idx), len(stats2idx)))
    
    # Making a dictionary that keeps track of current health for all mons in match
    health_dict = {name:100 for name in mons2idx.keys()}
    
    # Making a dictionary that maps Pokemon to players:
    p1_mons2player = {mon:match_dict['p1']['name'] for mon in p1_mons}
    p2_mons2player = {mon:match_dict['p2']['name'] for mon in p2_mons}
    
    mons2player = p1_mons2player | p2_mons2player

    # Going through html
    for line in match_html:
        
       

        # -- POKEMON STATISTICS -- #
        ### To avoid all the if/elif statements, it'd probably be easier to have 
        ### some kind of map or dict that maps condition. I'm lazy for now -- will update later!
        
        type_change = ''
        # Boosting
        if 'boost|' in line:
            if 'setboost' in line:
                pokemon, change = get_buff(line, set_boost='cupcake!')
                type_change = 'buff_received'
            elif 'unboost' in line:
                if '[of]' in line:
                    continue
                pokemon, change = get_buff(line, set_boost='you are alive!')
                type_change = 'buff_received'
                change = -change
            elif 'copyboost' in line:
                continue
            else:
                pokemon, change = get_buff(line, set_boost='you are alive!')
                type_change = 'buff_received'

        # Healing
        elif line.startswith('|-heal'):
            pokemon, change = get_health_change(line, health_dict)
            type_change = 'damage_healed'

        # Toxic damage taken
        elif line.startswith('|-damage|') and 'tox|[from] psn' in line:
            pokemon, change = get_health_change(line, health_dict)
            type_change = 'toxic_damage_taken'

        # Burn damage taken
        elif line.startswith('|-damage|') and '[from] brn' in line:
            pokemon, change = get_health_change(line, health_dict)
            type_change = 'burn_damage_taken' 

        # Poison damage taken
        elif line.startswith('|-damage|') and '[from] psn' in line:
            pokemon, change = get_health_change(line, health_dict)
            type_change = 'poison_damage_taken' 

        # Life Orb 
        elif line.startswith('|-damage|') and '[from] item: Life Orb' in line:
            pokemon, change = get_health_change(line, health_dict)
            type_change = 'life_orb_damage_taken' 


        # Stealth Rock  
        elif line.startswith('|-damage|') and '[from] Stealth Rock' in line:
            pokemon, change = get_health_change(line, health_dict)
            type_change = 'stealth_rock_damage_taken' 


        # Spikes
        elif line.startswith('|-damage|') and '[from] Spikes' in line:
            pokemon, change = get_health_change(line, health_dict)
            type_change = 'spike_damage_taken' 

        # Rocky Helmet (commented out because no one ran this set in our league):
        # elif line.startswith('|-damage|') and '[from] item: Rocky Helmet' in line:
        #   get_health_change(line, health_dict)
        
        # Recoil 
        elif line.startswith('|-damage|') and '[from] Recoil' in line:
            pokemon, change = get_health_change(line, health_dict)
            type_change = 'recoil_damage_taken' 
        
        # Doing main damage case after 
        if type_change:
            mon_array[mons2idx[pokemon], stats2idx[type_change]] += change 

        if '&&&' in line and '|move|' in line: 
            attacker, target = get_main_damage(line, health_dict)
            
            # Damage given (attacking)
            mon_array[mons2idx[attacker[0]], stats2idx['damage_given']] += attacker[1]

            # Damage taken (target)
            mon_array[mons2idx[target[0]], stats2idx['damage_received']] += target[1]
        
        # -- PLAYER STATISTICS -- #
        
        if line.startswith('|j|'):
            # add_join(line)
            pass    

        if line.startswith('|c|'):
            add_chat(line)
        
    return make_match_dataframe(mons2idx, stats2idx, mon_array, week, mons2player)


# print(parse_html(base_array, test_dict, test_html))


# ----- AGGREGATING POKEMON STATS ----- # 
final_df = pd.DataFrame()
if WEEKLY:
    for week in weeks:
        week_df = pd.DataFrame()
        print(f'--{week}--')
        week_num = week.split('eek')[1]
        for file in os.listdir(f'{PATH}/{week}'):
            print(f'Processing {file}')
            file_dict, file_html = clean_html(f'{week}/{file}')
            match_df = parse_html(base_array, file_dict, file_html, week_num)
            week_df = pd.concat([week_df, match_df])
        final_df = pd.concat([final_df, week_df])
        print()
    name = 'pokemon_stats_weekly.csv'
else:
    for file in os.listdir(PATH):
       file_dict, file_html = clean_html(file)
       output_df = parse_html(base_array, file_dict, file_html, 0)
       final_df = pd.concat([final_df, output_df])
    name = 'pokemon_stats.csv'
final_df.to_csv(f'{HOME}/csvs/{name}')

# -- PLAYER CSV -- #
player_df = pd.DataFrame(base_array,
                         index=player_2_idx,
                         columns=categories)
player_df['average_chat_len'] = player_df['chat_len']/player_df['chat_num']
player_df.to_csv(f'{HOME}/csvs/player_stats.csv')

##### THINGS TO ADD ###### 
# Most & least damage giver (how much percent they gave out)
# Most & least damage taker (how much percent they took)
# Biggest healer (account for healing wish and wish?)
# Pokemon gender users (most feminist)
# Most popular items ?
# Most improved (aka stat buffs)
# Most toxic damage giver/damage?
# Hurts itself the most (life orb, etc.)
# Most crits
