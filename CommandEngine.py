#!/usr/bin/python2

# Script: audi.py
# Function: Automate Command Processing and Validate Outputs.

import os
import subprocess
import json
import argparse
import sys
import signal

#####
# Catch Dirty Exits
#####
def signal_handler(sig, frame):
        print('\n Script Aborted')
        sys.exit(2)
signal.signal(signal.SIGINT, signal_handler)

#####
# Declare Globals
#####
order = []
data = {}
cmdFile = ''
outFile = ''

#####
# Genearate Arguments
#####
parser = argparse.ArgumentParser(prog='audi.py', description='Audi Command Engine - Ansible Automation')
parser.add_argument('-t','--template', action='store_true', help='Generate a sample JSON Command File.')
parser.add_argument('-c','--cmdfile', type=str, nargs='?', action='store', default='/root/commands.json', help='Specify an alternative JSON Command File.')
parser.add_argument('-o','--output', type=str, nargs='?', action='store', default='.', help='Specify a File to Write Output.')
parser.add_argument('-a','--all', action='store_true', help='Show all tests, not just failed tests.')
parser.add_argument('-v','--verbose', action='store_true', help='Show Values instead of Success/Failure.')
parser.add_argument('-q','--quiet', action='store_true', help='Suppress Onscreen Output.')
parser.add_argument('--yes', action='store_true', help='Assume it is OK to overwrite files.')
parser.add_argument('--csv', action='store_true', help='Output in CSV Format.')
parser.add_argument('--keys', action='store_true', help='Show keys for CSV.')
parser.add_argument('--json', action='store_true', help='Output in JSON Format.')
parser.add_argument('--pjson', action='store_true', help='Output partial JSON for building a list.')
args = parser.parse_args()

#####
# Output Template if requested
#####
if args.template:
    print('{\n  "NotNovember" : {\n    "cmd" : "date",\n    "operator" : "IN",\n    "failure" : "Nov"\n  },\n  "SyslogErrors" : {\n    "cmd" : "grep -ic error /var/log/messages",\n    "operator" : "GT",\n    "failure" : "0"\n  }\n}')
    print('\nThere are two tests above:\n  - NotNovember tests the date command. Fail if "Nov" IN output.\n  - SyslogErrors tests how many times "error" is found in /var/log/messages. Fail if GT 0.\n\nNote: There is a great validator for JSON here: https://codebeautify.org/jsonvalidator')
    sys.exit(0)

#####
# Find JSON File:
#####
if os.path.isfile(os.getcwd() + '/' + args.cmdfile):
    cmdFile = os.getcwd() + '/' + args.cmdfile
elif os.path.isfile(args.cmdfile):
    cmdFile = args.cmdfile
else:
    print('JSON Command File Not Found!\nNot in "' + os.getcwd() + '/' + args.cmdfile + '" or "' + args.cmdfile + '"\nPlease create a commands.json file or specify a file using --cmdfile')
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
# Check Output File (if applicable):
#####
if not args.output == '.':
    if not args.output[0] == '/':
        outFile=os.getcwd() + '/'
    outFile=outFile + args.output
    if args.yes and os.path.isfile(outFile):
        print('Overwriting file per --yes flag')
        os.remove(outFile)
    if os.path.isfile(outFile):
        sys.stdout.write(outFile + ' exists, Overwrite? (y|N) ')
        if not raw_input().lower() in [ 'yes', 'ye', 'y' ]:
            print('\nERROR: File Exists. Please rerun with a valid --output file')
            sys.exit(1)
        else:
            os.remove(outFile)
    if not os.path.isdir(outFile[0:outFile.rfind('/')]):
        print('ERROR: Directory Does Not Exist: ' + outFile[0:outFile.rfind('/')] + '\nPlease rerun with a valid --output file')
        sys.exit(1)
else:
    outFile = ''

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
    # Output somehow:
    if args.csv or args.keys:
        keys = 'Hostname'
        failuresStr = hostname
        for k in order:
            if data[k][0]:
                if args.all:
                    keys = keys + ',' + k
                    if args.verbose:
                        failuresStr = failuresStr + ',' + data[k][1].rstrip()
                    else:
                        failuresStr = failuresStr + ',Success'
            else:
                keys = keys + ',' + k
                if args.verbose:
                    failuresStr = failuresStr + ',' + data[k][1].rstrip()
                else:
                    failuresStr = failuresStr + ',Failure'
        if not outFile == '':
            out = open(outFile, 'w')
            if args.keys:
                out.write(keys + '\n')
            if args.csv:
                out.write(failuresStr + '\n')
        if not args.quiet:
            if args.keys:
                print (keys)
            if args.csv:
                print(failuresStr)
    elif args.json or args.pjson:
        if args.pjson:
            failuresStr = '"' + hostname + '":{'
        else:
            failuresStr = '{"' + hostname + '":{'
        for k in order:
            if data[k][0]:
                if args.all:
                    if args.verbose:
                        failuresStr = failuresStr + '"' + k + '":"' + data[k][1].rstrip() + '",'
                    else:
                        failuresStr = failuresStr + '"' + k + '":"Success",'
            else:
                if args.verbose:
                    failuresStr = failuresStr + '"' + k + '":"' + data[k][1].rstrip() + '",'
                else:
                    failuresStr = failuresStr + '"' + k + '":"Failure",'
        if args.pjson:
            failuresStr = failuresStr + '"hostname":"' + hostname + '"}'
        else:
            failuresStr = failuresStr + '"hostname":"' + hostname + '"}}'
        if not outFile == '':
            out = open(outFile, 'w')
            out.write(failuresStr)
        if not args.quiet:
            print(failuresStr)
    else:
        for k in order:
            if data[k][0]:
                if args.all:
                    failuresStr = failuresStr + hostname + '\t' + k + ' = '
                    if args.verbose:
                        failuresStr = failuresStr + data[k][1].rstrip() + '\n'
                    else:
                        failuresStr = failuresStr + 'Success\n'
            else:
                failuresStr = failuresStr + hostname + '\t' + k + ' = '
                if args.verbose:
                    failuresStr = failuresStr + data[k][1].rstrip() + '\n'
                else:
                    failuresStr = failuresStr + 'Failure\n'

        if not outFile == '':
            #output to file specified...
            out = open(outFile, 'w')
            out.write(failuresStr + '--------------------------------------------\n')
        if not args.quiet:
            print(failuresStr + '--------------------------------------------')

def main():
    # translate dict into array so we can sort:
    for key, value in cmdRules.iteritems():
        order.append(key)
    order.sort()
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
            if number:
                operator = '=='
            else:
                operator = 'IN'
        data[value][0] = True
        if not number:
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
