#!/usr/bin/python2

# Blame: Colton Riffel
# Department: S3 Operational Engineering
# Script: audi.py
# Function: Automate Command Processing and Validate Outputs.

import os
import subprocess
import json
import sys

#####
# Declare Globals
#####
order = []
data = {}
cmdFile = ''
outFile = ''

#####
# Find JSON File:
#####
if os.path.isfile(os.getcwd() + '/commands.json'):
    cmdFile = os.getcwd() + '/commands.json'
elif os.path.isfile('/root/commands.json'):
    cmdFile = '/root/commands.json'
else:
    print('JSON Command File Not Found!\nNot in "' + os.getcwd() + '/commands.json" or "/root/commands.json"\nPlease ensure the new file has been copyed to the Current Directory as commands.json')
    sys.exit(1)

#####
# Parse JSON File:
#####
try:
    contents = open(cmdFile, 'r').read()
except Exception as e:
    print('Incorrect permissions on ' + cmdFile + '. Please enable read permissions.')
    sys.exit(1)
try:
    cmdRules = json.loads(contents)
except Exception as e:
    print('File is not parsable. Please check your JSON syntax.')
    sys.exit(1)

#####
# Declare Functions
#####
def cmd(proc):
    command = subprocess.Popen(proc, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return command.communicate()

def isNumeric(output):
    try:
        int(output)
        return True
    except:
        return False

def toScreen():
    dataStr = ''
    failuresStr = ''
    hostname = cmd('host $(hostname)')[0].split(" ")[0].strip()
    if hostname == ';;':
        hostname = cmd('hostname')[0]
    keys = '"Hostname"'
    failuresStr = '"' + hostname + '"'
    for k in order:
        if data[k][0]:
                keys = keys + ',"' + k + '"'
                # if we want verbose output: failuresStr = failuresStr + ',"' + data[k][1].strip() + '"'
                failuresStr = failuresStr + ',"Pass"'
        else:
            keys = keys + ',"' + k + '"'
            if data[k][1].rstrip() == '':
                data[k][1] = 'Failure'
            failuresStr = failuresStr + ',"' + data[k][1].rstrip() + '"'
    if not os.path.isfile('audi.py'):
        print(failuresStr)
    else:
        print(keys)

def main():
    # translate dict into array so we can sort:
    seq_order = []
    std_order = []
    for key, value in cmdRules.iteritems():
        try:
            seq_order.append(cmdRules[key]['seq'])
        except:
            std_order.append(key)
    seq_order.sort()
    std_order.sort()
    for val in seq_order:
        for key,value in cmdRules.iteritems():
            try:
                if cmdRules[key]['seq'] == val:
                    order.append(key)
            except:
                waste = 0
    for val in std_order:
        order.append(val) 
    for value in order:
        data[value] = [False,'']
        failure = cmdRules[value]['failure'].lower()
        raw_command = cmd(cmdRules[value]['cmd'])
        command = raw_command[0]
        errout = raw_command[1]
        data[value][1] = command
        number = isNumeric(command)
        #set default operator
        try:
            operator = cmdRules[value]['operator']
        except:
            operator = 'EQ'
        data[value][0] = True
        if not number:
            command = command.rstrip()
            #operator validation for strings:
            if operator != 'EQ' and operator != 'NE' and operator != 'IN' and operator != 'NI':
                print 'ERROR: "' + operator + '" is not a valid operator for string value of "' + value + '". Please correct this and rerun.';
                sys.exit(1)
            #If STDERR exists set defaults for key to fail and run though checks (might still pass validation):
            if len(errout) > 0:
                data[value][0] = False
                data[value][1] = errout
            if operator == 'EQ':
                if failure == command.lower():
                    data[value][0] = False
                    data[value][1] = command
            elif operator == 'NE':
                if failure != command.lower():
                    data[value][0] = False
                    data[value][1] = command
            elif operator == 'IN':
                if failure in command.lower():
                    data[value][0] = False
                    data[value][1] = command
            else: # 'NI': last option after an exit
                if not failure in command.lower():
                    data[value][0] = False
                    data[value][1] = command
        else: # is numeric
            #operator validate for numbers:
            if operator != 'GT' and operator != 'LT' and operator != 'GE' and operator != 'LE' and operator != 'EQ' and operator != 'NE' and operator != 'IN' and operator != 'NI':
                print('ERROR: "' + operator + '" is not a valid operator for numerical value of "' + value + '". Please correct this and rerun.')
                sys.exit(1)
            #If STDERR exists set defaults for key to fail and run though checks (might still pass validation):
            if len(errout) > 0:
                data[value][0] = False
                data[value][1] = errout
            # parse numeric:
            scommand = command
            failure = int(failure)
            command = int(command)
            # start checks
            if operator == 'EQ':
                if failure == command:
                    data[value][0] = False
                    data[value][1] = scommand
            elif operator == 'NE':
                if not failure == command:
                    data[value][0] = False
                    data[value][1] = scommand
            elif operator == 'LT':
                if command < failure:
                    data[value][0] = False
                    data[value][1] = scommand
            elif operator == 'GT':
                if command > failure:
                    data[value][0] = False
                    data[value][1] = scommand
            elif operator == 'LE':
                if command <= failure:
                    data[value][0] = False
                    data[value][1] = scommand
            elif operator == 'GE':
                if command >= failure:
                    data[value][0] = False
                    data[value][1] = scommand
            elif operator == 'IN':
                if string(failure) in scommand:
                    data[value][0] = False
                    data[value][1] = scommand
            else: # must be NI
                if not string(failure) in scommand:
                    data[value][0] = False
                    data[value][1] = scommand
    toScreen()
main()

