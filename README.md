# Description
YoutubeChannelVideosFinder is a small utility script that goes out and find all video links of a given Youtube channel.
Youtube's data API has a limit of 500 search results. This script splits the search in multiple smaller operations, making it possible to get all video links while respecting the rules :)

# Usage
This script provides multiple arguments that can be used to customize its behavior.

Only two arguments are mandatory:
* -k or --api-key: mandatory to access Youtube's data API. You can get one from there: https://console.developers.google.com
* -c or --channel: otherwise the script cannot find many videos, can it? :)

To display the full list of supported arguments, use '-h' or '--help'.

	$ py ./youtubeChannelVideosFinder.py --help
	usage: youtubeChannelVideosFinder.py [-h] -k APIKEY -c CHANNEL
										 [-o OUTPUTFILEPATH] [-x DATEFROM]
										 [-y DATETO] [-i INTERVAL] [-q | -v | -d]
										 [-l LOGFILEPATH] [--version]

	This program finds all videos in a given Youtube channel

	optional arguments:
	  -h, --help            show this help message and exit
	  -k APIKEY, --api-key APIKEY
							Google Data API key to use. You can get one here:
							https://console.developers.google.com
	  -c CHANNEL, --channel CHANNEL
							Youtube channel to get videos from
	  -o OUTPUTFILEPATH, --output-file-path OUTPUTFILEPATH
							File to write found video links to (content replaced
							each time). If this option is not specified, the links
							are sent to the standard output
	  -x DATEFROM, --date-from DATEFROM
							Videos published after this date will not be retrieved
							(expected format: yyyy-mm-dd). If not specified, the
							current date is taken
	  -y DATETO, --date-to DATETO
							Videos published before this date will not be
							retrieved (expected format: yyyy-mm-dd). If not
							specified, we go back one month (related to -b /
							--date-from)
	  -i INTERVAL, --interval INTERVAL
							Longest period of time (in days) to retrieve videos at
							a time for. Since the Youtube API only permits to
							retrieve 500 results, the interval cannot be too big,
							otherwise we might hit the limit. Default: 30 days
	  -q, --quiet           Only print out results.. or fatal errors
	  -v, --verbose         Print out detailed information during execution (e.g.,
							invoked URLs, ...)
	  -d, --debug           Print out all the gory details
	  -l LOGFILEPATH, --log-file-path LOGFILEPATH
							File to write the logs to (content replaced each
							time). If this option is not specified, the logs are
							sent to the standard output (according to the
							verbosity level)
	  --version             show program's version number and exit

# Example
Retrieve all videos in the 'martyzsongs' Youtube channel that were published between 2014-01-01 and 2014-06-15. Once found, put the links in a file called 'result.txt'. Also, create a log file containing all the gory details of what the script has done:

	$ py ./youtubeChannelVideosFinder.py 
	-k ...  # the API key
	-c martyzsongs # the channel name 
	--date-from 2014-06-15 # last published videos we care about
	--date-to 2014-01-01 # oldest published videos we care about
	--log-file-path awesome.log # generate a log file
	--output-file-path result.txt # put generated links in that file
	-d # debug -> tell everything you're doing
