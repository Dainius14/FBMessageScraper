# FBMessageScraper

A forked repo of the original FB Message Scraper. I updated it to Python 3, moved code around, edited output format and made it to work in a more user friendly (IMO) way, without the need to give everything by command-line arguments. Original code was pretty spaghetti IMO.

So this is a simple python script to download the entire conversation from Facebook, not limited like the one in the data dump provided by Facebook

Outputs the conversation in a user-friendly easy to read JSON format, as well as the raw JSON for each individual chunk.

This is  a fork of the following repository: [https://github.com/RaghavSood/FBMessageScraper](https://github.com/RaghavSood/FBMessageScraper). 

### Config setup

1. In Chrome/Firefox, open [facebook.com/messages](https://www.facebook.com/messages/) and open any conversation with a fair number of messages.
2. Open the network tab of the Developer tools.
3. Scroll up in the conversation until the page attempts to load previous messages.
4. Look for the POST request to [thread\_info.php](https://www.facebook.com/ajax/mercury/thread_info.php).
5. You need to copy certain parameters from this request into the `config.json`:
	* Set the `cookie` value to the value you see under `Request Headers`
	* Set the `__user` value to the value you see under `Form Data` 
	* Set the `__a` value to the value you see under `Form Data`
	* Set the `__dyn` value to the value you see under `Form Data`
	* Set the `__req` value to the value you see under `Form Data`
	* Set the `__rev` value to the value you see under `Form Data`
	* Set the `fb_dtsg` value to the value you see under `Form Data`
	* Set the `ttstamp` value to the value you see under `Form Data`

You're now all set to start downloading messages.


### Downloading messages

1. Get the conversation ID for those messages by opening clicking on your partner's profile picture, and checking the URL. The number sequence is their Facebook ID. If it's not a numerical ID, go to [FindMyFbID](http://findmyfbid.com). Copy it.
2. For group conversations, the ID can be retrieved from the messages tab, as part of the URL. You must use `group_dumper.py` instead.
3. Launch `dumper.py` and enter conversation ID. Additionally you can supply partner's name, chunk size and offset. Custom config file can be provided via command-line argument.
4. To use text_printer.py, do: `python text_printer.py {configuration_file}, {id}`. This will print your message on the terminal screen to redirect the output to a .txt file, do : `python text_printer.py {configuration_file}, {id} > output.txt`.

Messages are saved by default to `messages/{id or supplied_name}/`