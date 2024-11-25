### Youtube Archiving

This project is not yet finished! Do not use it in it's current state. Core functionality is still missing and a lot of bug-fixes are still to do.

## Motivation
Over the last years I have noticed more and more videos vanishing from the internet.
My liked playlist alone is missing dozens. Be it deleted channels, videos being privated
by the uploader or copyright disputes. It is just a shame to watch them disappear.

So since storage is pretty cheap, I've decided to just start archiving. A big focus of this script including good subtitles in the downloads. 

## How to Use

The script (`main.py`) is currently meant to be run from the console.
Please run it from the main directory like this:

	python src/main.py --url <your-url>

The following commandline arguments are available:

	--url <your-url>            Provide the URL of a video,
	                            playlist or channel
	--playlist                  Flag for proper handling of the URL 
	                            if it is a playlist URL
	--channel                   Flag for proper handling of the URL 
	                            if it is a channel URL

	--file <file-path>          Path to a text file containing 
	                            one video url per line
	--video-source <name>       Allows you to manually specify a video source.
	                            This is only used in the database to allow you
	                            to search for videos from a specific source. 
                                Will be autofilled if video-urls are provided
                                via a playlist or channel url

	--rate-limit <limit>        Override for the default rate limit
	                            in Megabyte per second
	--max-height <height>       Override for the default max video
                                height in Pixels

	--postpone-post-processing  Flag to skip post-processing after the download.
                                Files will instead be moved into a seperate
                                directory for later finalization

All directories, certain file names and a number of other factors can be specified/changed in `config/config.json`.

## ToDo
    [x] Organisation:
		[x] Videos stored in single directory with uniform names
		[x] Searchable by title, channel, url, upload date, download date, subtitle content, download source
	[ ] Automation:
		[ ] Access to channel to automatically download new additions to liked videos or watch-history
	[x] Video quality:
		[x] Highest quality up to a max of 1080p (currently targetting formats 299+140)
		[x] Try to use AV1 if available
	[x] Automatically add subtitles to videos:
		[x] Add Manually Created Subtitles if available (en, de)
		[x] Add Autogenerated Subtitles if available (en, de)
		[x] Generate Subtitles myself if subtitles are not available
		[x] Convert youtube-subtitles to iterative subs compatible with mpv (en, de)
		[x] Convert youtube-subtitles to iterative and non-iterative subs with improved sentence structure (en)
		[x] Additionally store subtitle files seperately for search
			[-] Need to find optimal storage method (might not be just individual files)
	[x] Add Metadata (If possibe) or store seperately:
		- Video-id
		- Upload date
		- Channel name
		- Download date
		- Thumbnail
		- Download Source (ie: Watch History, Liked Playlist)
	[ ] Make Web interface for the script