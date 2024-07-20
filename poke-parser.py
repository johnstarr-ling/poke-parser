import os
import sys
import re

### Ensuring proper set-up
files = sys.argv

if len(files) > 2:
    raise Exception('Intended use case in command line: python poke-parser.py HTML_FILE')

### Reading in HTML
with open(sys.argv[-1]) as f:
    # Keeping only the raw log -- don't need chat, nor do we need ugly formatting text
    raw_html = f.read().split('</script>')[0].split('|gametype|singles\n')[1]

### Processing HTML

# Getting players:
player_team_dict = {}
for line in raw_html.split('\n')[:2]:
    player_team_dict[line.split('|')[3]] = {}

print(player_team_dict)