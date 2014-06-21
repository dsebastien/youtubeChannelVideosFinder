#!/usr/bin/env python


# ------------------------------------------
# Imports
# ------------------------------------------
import urllib
import json
import time
import datetime
import sys
import argparse
import logging

from rfc3339 import rfc3339


# ------------------------------------------
# Initialization
# ------------------------------------------
	
# we first initialize our parser then we use it to parse the provided args
# 	references: 
# 		https://docs.python.org/2/library/argparse.html
#		http://pymotw.com/2/argparse/
#		https://docs.python.org/2/howto/argparse.html

parser = argparse.ArgumentParser(description='This program finds all videos in a given Youtube channel')

parser.add_argument('-k', '--api-key', dest='apiKey', action='store', required=True, help='Google Data API key to use. You can get one here: https://console.developers.google.com')
parser.add_argument('-c', '--channel', dest='channel', action='store', required=True, help='Youtube channel to get videos from')
parser.add_argument('-o', '--output-file-path', dest='outputFilePath', action='store', default='', help='File to write found video links to (content replaced each time). If this option is not specified, the links are sent to the standard output')

parser.add_argument('-x', '--date-from', dest='dateFrom', action='store', help='Videos published after this date will not be retrieved (expected format: yyyy-mm-dd). If not specified, the current date is taken')
parser.add_argument('-y', '--date-to', dest='dateTo', action='store', help='Videos published before this date will not be retrieved (expected format: yyyy-mm-dd). If not specified, we go back one month (related to -b / --date-from)')
parser.add_argument('-i', '--interval', dest='interval', action='store', help='Longest period of time (in days) to retrieve videos at a time for. Since the Youtube API only permits to retrieve 500 results, the interval cannot be too big, otherwise we might hit the limit. Default: 30 days')

outputDetailLevel = parser.add_mutually_exclusive_group()
outputDetailLevel.add_argument('-q', '--quiet', dest='quiet', action='store_true', default=False, help='Only print out results.. or fatal errors')
outputDetailLevel.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Print out detailed information during execution (e.g., invoked URLs, ...)')
outputDetailLevel.add_argument('-d', '--debug', dest='debug', action='store_true', default=False, help='Print out all the gory details')

parser.add_argument('-l', '--log-file-path', dest='logFilePath', action='store', help='File to write the logs to (content replaced each time). If this option is not specified, the logs are sent to the standard output (according to the verbosity level)')

parser.add_argument('--version', action='version', version='1.0') # aka how much time can we lose while programming :p (https://code.google.com/p/argparse/issues/detail?id=43)

args = parser.parse_args()


# logger configuration
log = logging.getLogger('_name_')

handler = None
if(args.logFilePath is not None):
	handler = logging.FileHandler(args.logFilePath, "w", encoding=None, delay="true")
else:
	handler = logging.StreamHandler()

logFormat = '[%(asctime)s] [%(levelname)s] - %(message)s'
# format ref: https://docs.python.org/2/library/logging.html#logrecord-attributes

handler.setFormatter(logging.Formatter(logFormat))

log.addHandler(handler)

if args.verbose:
	log.setLevel(level=logging.INFO)
elif args.debug:
	log.setLevel(level=logging.DEBUG)
elif args.quiet:
	log.setLevel(level=logging.ERROR)
else:
	log.setLevel(level=logging.WARN)

	
# start/end & interval
log.debug('Initializing variables')
dateToStartFrom = None
dateToGoBackTo = None
timeInterval = None

if(args.dateFrom is not None):
	dateToStartFrom = datetime.datetime.strptime(args.dateFrom,'%Y-%m-%d') # ref: https://docs.python.org/2/library/datetime.html
else:
	dateToStartFrom = datetime.datetime.now()

log.info('Date to start from: %s', dateToStartFrom)
	
if(args.dateTo is not None):
	dateToGoBackTo = datetime.datetime.strptime(args.dateTo,'%Y-%m-%d')
else:
	dateToGoBackTo = dateToStartFrom - datetime.timedelta(weeks=4)

log.info('Date to go back to: %s',dateToGoBackTo)

totalTimePeriod = dateToStartFrom - dateToGoBackTo
log.info('Total period of time to find videos for: %s',str(totalTimePeriod))

if(args.interval is not None):
	timeInterval = datetime.timedelta(days=int(args.interval))
else:
	timeInterval = datetime.timedelta(weeks=4)

log.info('Time interval: %s',timeInterval)


# Strings
youtubeApiUrl = 'https://www.googleapis.com/youtube/v3/'
youtubeChannelsApiUrl = youtubeApiUrl + 'channels?key={0}&'.format(args.apiKey)
youtubeSearchApiUrl = youtubeApiUrl + 'search?key={0}&'.format(args.apiKey)

requestParametersChannelId = youtubeChannelsApiUrl + 'forUsername={0}&part=id'
requestChannelVideosInfo = youtubeSearchApiUrl + 'channelId={0}&part=id&order=date&type=video&publishedBefore={1}&publishedAfter={2}&pageToken={3}&maxResults=50'

youtubeVideoUrl = 'https://www.youtube.com/watch?v={0}'

# ------------------------------------------
# Functions
# ------------------------------------------
def getChannelId(channelName):
	log.info('Searching channel id for channel: %s',channelName)
	retVal = -1
	try:
		url = requestParametersChannelId.format(channelName)
		log.debug("Request: %s",url)
		
		log.debug('Sending request')
		response = urllib.urlopen(url)
		
		log.debug('Parsing the response')
		responseAsJson = json.load(response)

		response.close()
		
		log.debug('Response: %s',json.dumps(responseAsJson,indent=4))
		
		log.debug('Extracting the channel id')
		if(responseAsJson['pageInfo'].get('totalResults') > 0):
			returnedInfo = responseAsJson['items'][0]
			retVal = returnedInfo.get('id')
			log.info('Channel id found: %s',str(retVal))
		else:
			log.debug('Response received but it contains no item')
			raise Exception('The channel id could not be retrieved. Make sure that the channel name is correct')
			
		if(responseAsJson['pageInfo'].get('totalResults') > 1):
			log.debug('Multiple channels were received in the response. If this happens, something can probably be improved around here')
	except Exception, err:
		log.error('An exception occurred while trying to retrieve the channel id',exc_info=True)
	
	return retVal

def getChannelVideosPublishedInInterval(channelId,publishedBefore,publishedAfter):
	log.info('Getting videos published before %s and after %s',publishedBefore,publishedAfter)
	retVal = []
	foundAll = False
	
	nextPageToken = ''

	while not foundAll:
		try:
			url = requestChannelVideosInfo.format(channelId,publishedBefore,publishedAfter,nextPageToken)
			log.debug('Request: %s',url)
			
			log.debug('Sending request')
			response = urllib.urlopen(url)
			
			log.debug('Parsing the response')
			responseAsJson = json.load(response)
			
			response.close()
			
			returnedVideos = responseAsJson['items']
			log.debug('Response: %s',json.dumps(returnedVideos,indent=4))
			
			for video in returnedVideos:
				retVal.append(video) 
				
			try:
				nextPageToken = responseAsJson['nextPageToken']
				log.info('More videos to load, continuing')
			except Exception, err:
				log.info('No more videos to load')
				foundAll = True
		except Exception, err:
			log.error('An exception occurred while trying to retrieve a subset of the channel videos. Stopping search.',exc_info=True)
			foundAll = True		
	
	log.info('Found %d video(s) in this time interval',len(retVal))
	return retVal	
	
def getChannelVideos(channelId,dateToStartFrom,dateToGoBackTo,timeInterval):	
	log.info('Searching for videos published in channel between %s and %s',dateToStartFrom,dateToGoBackTo)
	if(dateToStartFrom < dateToGoBackTo):
		raise Exception('The date to start from cannot be before the date to go back to!')
	
	retVal = []
	
	# initialization
	startFrom = dateToStartFrom
	goBackTo = startFrom - timeInterval
	
	done = False
	
	while not done:
		if(goBackTo < dateToGoBackTo):
			log.debug('The interval is now larger than the remaining time span to retrieve videos for. Using the date to go back to as next boundary')
			goBackTo = dateToGoBackTo
		
		if(goBackTo == dateToGoBackTo):
			log.debug('Last round-trip')
			done = True
		
		log.debug('Converting timestamps to RFC3339 format')
		goBackTo_rfc3339 = rfc3339(goBackTo,utc=True)
		startFrom_rfc3339 = rfc3339(startFrom,utc=True)
		
		videosPublishedInInterval = getChannelVideosPublishedInInterval(channelId,startFrom_rfc3339,goBackTo_rfc3339)
		
		log.debug('Adding videos found in the interval to the results list')
		retVal.extend(videosPublishedInInterval)
		log.debug('Total video(s) found so far: %d',len(retVal))
		
		if(not done):
			# we simply continue from where we are
			startFrom = goBackTo
			
			# calculate the next date to go back to based on the given interval
			nextDate = goBackTo - timeInterval
			log.debug('Calculating the next date to go back to based on the interval: %s - %s => %s',goBackTo,timeInterval,nextDate)
			goBackTo = nextDate
			
	log.info('Found %d video(s) in total',len(retVal))
	return retVal	


def getVideoURL(videoId):
	retVal = youtubeVideoUrl.format(videoId)
	log.debug('Video URL: %s',retVal)
	return retVal

	
# ------------------------------------------
# Entry point
# ------------------------------------------
def main():
	try:
		channelId = getChannelId(args.channel)
		if(channelId == -1):
			raise Exception('Impossible to continue without the channel id')
		
		channelVideos = getChannelVideos(channelId,dateToStartFrom,dateToGoBackTo,timeInterval)
		
		if(not len(channelVideos) > 0):
			log.info("No video found for that channel! Either there's none or a problem occurred. Enable verbose or debug logging for more details..")
			sys.exit(0)
		
		log.info('Generating links for found videos')
		videoURLs = []
		for video in channelVideos:
			log.debug('Processing video: %s',json.dumps(video,indent=4))
			videoId = video.get('id').get('videoId')
			log.debug('Video id: %s',videoId)
			videoURL = getVideoURL(videoId)
			videoURLs.append(videoURL) 
		if(args.outputFilePath is not None and args.outputFilePath is not ''):
			log.debug('File output enabled')
			log.info('Links will be written to %s',args.outputFilePath)
		
			f = None
			try:
				f = open(args.outputFilePath,'w')
			except Exception, err:
				log.critical('Could not create/open the output file!',exc_info=True)
				raise Exception('Impossible to write the links to the output file. Verify that the path is correct and that it is accessible/can be created/can be written to')
			
			for videoURL in videoURLs:
				f.write(videoURL+"\n")
				
			f.close()
		else:
			for videoURL in videoURLs:
				print videoURL
		log.info('Done!')
	except Exception, err:
		log.critical('We tried our best but still..',exc_info=True)
		sys.exit(2)

if __name__ == '__main__':
    main()