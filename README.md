Usage: ./bruteforcer.py [OPTION]... [COMMAND]
Bruteforces the COMMAND (until an exit code of 0 by default).

Mandatory arguments to long options are mandatory for short options too.
  -n, --numthreads=NUM       fires up NUM threads to bruteforce COMMAND
                                (default is 1)
  -s, --statuscode=STATUS    continues to run COMMAND on all threads until
                                an exit code of STATUS has been returned
                                (default is 0)
  -l, --length=LEN           attempt passwords up to LEN length
                                (default is 8)
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
    ./bruteforcer.py -a unzip -t -P {} file.zip (attempts all lowercase alphabet
        passwords up to LEN length)
    ./bruteforcer.py -a -N curl -f -u username:{} http://example.com (attempts
        all alphanumeric passwords up to LEN length)

Exit status:
 0  if OK,
 1  if minor problems (e.g., no command given),
 2  if less minor problems (e.g., incorrect command-line argument usage),
 3  if serious trouble.

online help: <http://www.cranklin.com>
Full documentation at: <http://www.cranklin.com>

