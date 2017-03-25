Cranky's Bruteforcer
====================
Usage: ./bruteforcer.py [OPTION]... [COMMAND]<br />
Bruteforces the COMMAND (until an exit code of 0 by default).<br />
<br />
Mandatory arguments to long options are mandatory for short options too.<br />
  -n, --numthreads=NUM       fires up NUM threads to bruteforce COMMAND<br />
                                (default is 1)<br />
  -s, --statuscode=STATUS    continues to run COMMAND on all threads until<br />
                                an exit code of STATUS has been returned<br />
                                (default is 0)<br />
  -l, --length=LEN           attempt passwords up to LEN length<br />
                                (default is 8)<br />
  -a                         attempt lowercase alphabet characters<br />
  -A                         attempt uppercase alphabet characters<br />
  -N                         attempt numeric characters<br />
  -S                         attempt special characters<br />
  -d, --dict=DICTFILE        attempt dictionary words supplied in DICTFILE<br />
                                which should be a newline delimited list of<br />
                                dictionary words to attempt.  Each word will<br />
                                be attempted in three ways: lower case, upper<br />
                                case, upper first<br />
  -V                         verbose mode.  Displays each response to STDOUT<br />
  -h, --help                 display this help and exit<br />
  -v, --version              output version information and exit<br />
<br />
<br />
{} denotes section in the COMMAND string to inject passwords<br />
<br />
Examples:<br />
    ./bruteforcer.py -a unzip -t -P {} file.zip (attempts all lowercase alphabet<br />
        passwords up to LEN length)<br />
    ./bruteforcer.py -a -N curl -f -u username:{} http://example.com (attempts<br />
        all alphanumeric passwords up to LEN length)<br />
<br />
Exit status:<br />
 0  if OK,<br />
 1  if minor problems (e.g., no command given),<br />
 2  if less minor problems (e.g., incorrect command-line argument usage),<br />
 3  if serious trouble.<br />
<br />
online help: <http://www.cranklin.com><br />
Full documentation at: <http://www.cranklin.com><br />

