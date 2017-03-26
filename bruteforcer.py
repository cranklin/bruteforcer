#!/usr/bin/python

import threading
import signal
import sys
import os
import getopt
import itertools
import subprocess

exitFlag = 0  # 0: running 1: keyboard interrupt 2: password found
version = "v0.03"
errorText = '%s -h or %s --help for help' % (__file__, __file__)
versionText = '''
bruteforcer (cranklin.com) %s
Copyright (C) 2017 Cranklin.com
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Written by Edward E. Kim (cranklin.com).
''' % (version)
usageText = '''
Usage: %s [OPTION]... [COMMAND]
Bruteforces the COMMAND (until an exit code of 0 by default).

Mandatory arguments to long options are mandatory for short options too.
  -n, --numthreads=NUM       fires up NUM threads to bruteforce COMMAND
                                (default is 1)
  -s, --statuscode=STATUS    continues to run COMMAND on all threads until
                                an exit code of STATUS has been returned
                                (default is 0)
  -l, --length=LEN           attempt passwords up to LEN length
                                (default is 8)
  -m, --marker=MARKER        denotes the marker in the COMMAND string which
                                will be replaced with password permutations
                                (default is {})
  -a                         attempt lowercase alphabet characters
  -A                         attempt uppercase alphabet characters
  -N                         attempt numeric characters
  -S                         attempt special characters
  -d, --dict=DICTFILE        attempt dictionary words supplied in DICTFILE
                                which should be a newline delimited list of
                                dictionary words to attempt.  Each word will
                                be attempted in three ways: lower case, upper
                                case, upper first
  -V                         verbose mode.  Displays each response to STDOUT
  -h, --help                 display this help and exit
  -v, --version              output version information and exit


{} denotes section in the COMMAND string to inject passwords

Examples:
    %s -a unzip -t -P {} file.zip (attempts all lowercase alphabet
        passwords up to LEN length)
    %s -a -N curl -f -u username:{} http://example.com (attempts
        all alphanumeric passwords up to LEN length)

Exit status:
 0  if OK,
 1  if minor problems (e.g., no command given),
 2  if less minor problems (e.g., incorrect command-line argument usage),
 3  if serious trouble.

online help: <http://www.cranklin.com>
Full documentation at: <http://www.cranklin.com>
''' % (__file__, __file__, __file__)

class BruteForceThread (threading.Thread):
    def __init__(self, threadID, name, thread_opts, it):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.it = it
        self.thread_opts = thread_opts
    def run(self):
        print "Starting " + self.name
        process_attempt(self.name, self.thread_opts, self.it)
        print "Exiting " + self.name


class Threadsafe:
    """
    Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """
    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()
        self.last = ""

    def __iter__(self):
        return self

    def next(self):
        with self.lock:
            #return self.it.next()
            self.last = self.it.next()
            return self.last

def threadsafe(f):
    """
    A decorator that takes a generator function and makes it thread-safe.
    """
    def g(*a, **kw):
        return Threadsafe(f(*a, **kw))
    return g

@threadsafe
def permutation_generator(perm_opts):
    numeric_representation = []
    character_representation = []
    charset = [];
    if perm_opts['lowerAlphabet']:
        charset.extend(['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'])
    if perm_opts['upperAlphabet']:
        charset.extend(['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'])
    if perm_opts['numbers']:
        charset.extend(['0','1','2','3','4','5','6','7','8','9'])
    if perm_opts['symbols']:
        charset.extend(['~','`','!','@','#','$','%','^','&','*','(',')','-','_','\\','/','\'','"',';',':',',','.','+','=','<','>','?'])
    if perm_opts['dictionaryFile'] is not None:
        with open (perm_opts['dictionaryFile'], "r") as dictFile:
            data=dictFile.readlines()
            words = [word.strip() for word in data]
        for word in words:
            yield word.lower()
            yield word.upper()
            yield word.title()

    for i in range(1, int(perm_opts['length'])+1):
        for char in itertools.product(charset, repeat=i):
            s = ''.join(char)
            yield s

def process_attempt(threadName, thread_opts, it):
    global exitFlag
    while not exitFlag:
        data = it.next()
        password_injected_command = [item.replace(thread_opts['marker'], data) for item in thread_opts['command']]
        if thread_opts['verbose']:
            print "%s processing %s" % (threadName, data)
            return_code = subprocess.call(password_injected_command)
        else:
            with open(os.devnull, 'w') as devnull:
                return_code = subprocess.call(password_injected_command, stdout=devnull, stderr=devnull)
        if int(return_code) == int(thread_opts['statusCode']):
            exitFlag = 2
            print "\n\n"
            print "***** PASSWORD FOUND *****"
            print "password: {}".format(data)
            print "***** PASSWORD FOUND *****"
            print "\n\n"
    if exitFlag < 2:
        print "last password attempted by {} : {}".format(threadName, data)

def start_brute_force(opts):
    global exitFlag
    print 'Lowercase alphabet: ', opts['lowerAlphabet']
    print 'Uppercase alphabet: ', opts['upperAlphabet']
    print 'Numbers: ', opts['numbers']
    print 'Symbols: ', opts['symbols']
    print 'Dictionary file: ', opts['dictionaryFile']
    print 'Number of threads: ', opts['numThreads']
    print 'Desired status code: ', opts['statusCode']
    print 'Length: ', opts['length']
    print 'Marker: ', opts['marker']
    print 'Command to brute force: ', opts['command']
    print '\n\n'
    print 'Ctrl-C to quit'
    print 'Ctrl-\\ to check status'
    print '\n\n\n\n'

    perm_opts = {k: opts[k] for k in ('lowerAlphabet', 'upperAlphabet', 'numbers', 'symbols', 'dictionaryFile', 'length')}
    thread_opts = {k: opts[k] for k in ('command', 'verbose', 'statusCode', 'marker')}
    threads = []
    threadID = 1

    permutation_iterator = permutation_generator(perm_opts);

    def signal_handler(signal, frame):
        global exitFlag
        if signal==2: # SIGINT / ctrl + c
            print('Exiting...')
            exitFlag = 1
            sys.exit(0)
        elif signal==3: # SIGQUIT / ctrl + \
            print('Last attempted password: ' + permutation_iterator.last)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)

    # Create new threads
    for i in range(0, int(opts['numThreads'])):
        thread = BruteForceThread(
                threadID,
                "thread-%s" % str(i),
                thread_opts,
                permutation_iterator,
            )
        thread.start()
        threads.append(thread)
        threadID += 1

    while not exitFlag:
        pass
    #signal.pause()

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print "Exiting Main Thread"
    return 0

def main(argv):
    numThreads = 1
    statusCode = 0
    length = 8
    marker = "{}"
    lowerAlphabet = False
    upperAlphabet = False
    numbers = False
    symbols = False
    verbose = False
    dictionaryFile = None

    try:
        opts, args = getopt.getopt(argv,"hvaANSVd:n:s:i:l:m:",["help","version","numthreads=","statuscode=","dict=","length=","marker="])
    except getopt.GetoptError:
        print errorText
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print usageText
            sys.exit()
        elif opt in ("-v", "--version"):
            print versionText
            sys.exit()
        elif opt == '-a':
            lowerAlphabet = True
        elif opt == '-A':
            upperAlphabet = True
        elif opt == '-N':
            numbers = True
        elif opt == '-S':
            symbols = True
        elif opt == '-V':
            verbose = True
        elif opt in ("-d", "--dict"):
            dictionaryFile = arg
        elif opt in ("-n", "--numthreads"):
            numThreads = arg
        elif opt in ("-s", "--statuscode"):
            statusCode = arg
        elif opt in ("-l", "--length"):
            length = arg
        elif opt in ("-m", "--marker"):
            marker = arg

    if len(args) < 1:
        print errorText
        sys.exit(1)

    return start_brute_force({
        "numThreads"        : numThreads,
        "statusCode"        : statusCode,
        "lowerAlphabet"     : lowerAlphabet,
        "upperAlphabet"     : upperAlphabet,
        "numbers"           : numbers,
        "symbols"           : symbols,
        "verbose"           : verbose,
        "dictionaryFile"    : dictionaryFile,
        "length"            : length,
        "marker"            : marker,
        "command"           : args
    })


if __name__ == "__main__":
    main(sys.argv[1:])
