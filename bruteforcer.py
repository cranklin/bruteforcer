#!/usr/bin/python

import threading
import signal
import sys
import os
import getopt
import itertools
import subprocess

from threadsafe import Threadsafe, threadsafe


version = "v0.04"
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


class BruteForcer:

    lowerAlphabetCharset = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    upperAlphabetCharset = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    numbersCharset = ['0','1','2','3','4','5','6','7','8','9']
    symbolsCharset = ['~','`','!','@','#','$','%','^','&','*','(',')','-','_','\\','/','\'','"',';',':',',','.','+','=','<','>','?']

    def __init__(self, opts):
        """
        0: running
        1: keyboard interrupt
        2: password found
        """
        self.exitFlag = 0
        self.lowerAlphabet = opts['lowerAlphabet']
        self.upperAlphabet = opts['upperAlphabet']
        self.numbers = opts['numbers']
        self.symbols = opts['symbols']
        self.dictionaryFile = opts['dictionaryFile']
        self.numThreads = opts['numThreads']
        self.length = opts['length']
        self.command = opts['command']
        self.verbose = opts['verbose']
        self.statusCode = opts['statusCode']
        self.marker = opts['marker']
        self.charset = self.generate_charset()
        self.permutationIterator = self.permutation_generator();
        self.threads = []

    def signal_handler(self, signal, frame):
        print 'Last attempted password: ' + self.permutationIterator.last
        print 'Attempt #: ' + str(self.get_attempt_by_password(self.permutationIterator.last))
        if signal == 2: # SIGINT / ctrl + c
            print 'Exiting...'
            self.exitFlag = 1
            sys.exit(0)

    def print_status(self):
        print 'Lowercase alphabet: ', self.lowerAlphabet
        print 'Uppercase alphabet: ', self.upperAlphabet
        print 'Numbers: ', self.numbers
        print 'Symbols: ', self.symbols
        print 'Dictionary file: ', self.dictionaryFile
        print 'Number of threads: ', self.numThreads
        print 'Desired status code: ', self.statusCode
        print 'Length: ', self.length
        print 'Marker: ', self.marker
        print 'Command to brute force: ', self.command
        print '\n\n'
        print 'Ctrl-C to quit'
        print 'Ctrl-\\ to check status'
        print '\n\n\n\n'

    def get_attempt_by_password(self, password):
        pos = len(self.charset)
        value = 0
        try:
            for i,c in enumerate(reversed(str(password))):
                value += (pos**i) * self.charset.index(c)
        except ValueError:
            return "N/A"
        return value

    def generate_charset(self):
        charset = []
        if self.lowerAlphabet:
            charset.extend(self.lowerAlphabetCharset)
        if self.upperAlphabet:
            charset.extend(self.upperAlphabetCharset)
        if self.numbers:
            charset.extend(self.numbersCharset)
        if self.symbols:
            charset.extend(self.symbolsCharset)
        return charset

    @threadsafe
    def permutation_generator(self):
        if self.dictionaryFile is not None:
            with open (self.dictionaryFile, "r") as dictFile:
                data=dictFile.readlines()
                words = [word.strip() for word in data]
            for word in words:
                yield word.lower()
                yield word.upper()
                yield word.title()

        for i in range(1, int(self.length)+1):
            for char in itertools.product(self.charset, repeat=i):
                s = ''.join(char)
                yield s

    def process_attempt(self, name):
        print "Starting " + name
        while not self.exitFlag:
            data = self.permutationIterator.next()
            password_injected_command = [item.replace(self.marker, data) for item in self.command]
            if self.verbose:
                print "%s processing %s" % (self.name, data)
                return_code = subprocess.call(password_injected_command)
            else:
                with open(os.devnull, 'w') as devnull:
                    return_code = subprocess.call(password_injected_command, stdout=devnull, stderr=devnull)
            if int(return_code) == int(self.statusCode):
                self.exitFlag = 2
                print "\n\n"
                print "***** PASSWORD FOUND *****\n"
                print "password: {}".format(data)
                print "***** PASSWORD FOUND *****\n"
                print "\n\n"
                print "attempt #: " + str(self.get_attempt_by_password(data))
        print "Exiting " + name

    def run(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGQUIT, self.signal_handler)

        # Create new threads
        for i in range(1, int(self.numThreads)+1):
            threadName = "thread-%s" % str(i)
            thread = threading.Thread(target=self.process_attempt, args=(threadName,))
            thread.start()
            self.threads.append(thread)

        while not self.exitFlag:
            pass

        # Wait for all threads to complete
        for thread in self.threads:
            thread.join()
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

    bf = BruteForcer({
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
    bf.print_status()
    return bf.run()


if __name__ == "__main__":
    main(sys.argv[1:])
