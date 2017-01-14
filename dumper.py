import datetime
import gzip
import io
import json
import sys
import os
import urllib
import urllib.parse
import urllib.request
import time

# Constants
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OFFSET = 0
CONFIG_FILE = "config.json"
MESSAGES_FILE = "messages.json"

REQ_URL = "https://www.facebook.com/ajax/mercury/thread_info.php"

HEADERS = { "origin": "https://www.facebook.com", 
			"accept-encoding": "gzip,deflate", 
			"accept-language": "en-US,en;q=0.8",
			"pragma": "no-cache", 
			"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.122 Safari/537.36", 
			"content-type": "application/x-www-form-urlencoded", 
			"accept": "*/*", 
			"cache-control": "no-cache", 
			"referer": "https://www.facebook.com/messages/zuck"}



# Settings supplied by command-line args
if len(sys.argv) >= 3:
	conversation = sys.argv[2]
	is_group_conv = ("y" == sys.argv[3])
	if len(sys.argv) >= 4:
		conversation_name = sys.argv[4]

	chunk_size = DEFAULT_CHUNK_SIZE
	offset = DEFAULT_OFFSET
else:
	# Conversation ID
	conversation = input("Conversation ID: ")

	# Group chat or not
	is_group_conv = input("Is this a group conversation? [y/n] ")
	while is_group_conv != "y" and is_group_conv != "n":
		is_group_conv = input("Wrong answer. Is this a group conversation? [y/n] ")
	is_group_conv = (is_group_conv == "y")

	# Conversation name
	conversation_name = input("Conversation name [optional]: ")

	# Chunk size and offset
	chunk_size = int(input("Chunk size [default: " + str(DEFAULT_CHUNK_SIZE) + "]: ") or DEFAULT_CHUNK_SIZE)
	offset = int(input("Offset location [default: " + str(DEFAULT_OFFSET) + "]: ") or DEFAULT_OFFSET)
	print()


# Supplying config file via command-line arguments
if len(sys.argv) >= 2:
	CONFIG_FILE = sys.argv[1]

with open(CONFIG_FILE) as configFile:
	config = json.load(configFile)

if conversation_name != "":
	dir = "messages/" + conversation_name + "/"
else:
	dir = "messages/" + conversation + "/"
raw_dir = dir + "raw/"
img_dir = dir + "img/"

try:
	os.makedirs(dir)
	os.makedirs(raw_dir)
except OSError:
	pass # already exists

# When extracting a [newer .. older] portion of one's message history, facebook requires:
# -numeric id newer, -timestamp newer, -numeric id older, where numeric id newer is 0 for the
# the newest message, 1 for the one before that, etc.
timestamp = 0 

headers = HEADERS
headers["cookie"] = config["cookie"]
raw_messages = []
messages_data = '{ "payload" : "empty" }'


data_text = { "client": "web_messenger",
			  "__user": config["user"],
			  "__a": config["a"],
			  "__dyn": config["dyn"],
			  "__req": config["req"],
			  "__rev": config["rev"],
			  "fb_dtsg": config["fb_dtsg"],
			  "ttstamp": config["ttstamp"] }

# Goes on while FB doesn't inform of conversation end
while "end_of_history" not in json.loads(messages_data)["payload"]: 

	if not is_group_conv:
		data_text["messages[user_ids][" + conversation + "][offset]"] = offset
		data_text["messages[user_ids][" + conversation + "][timestamp]"] = timestamp
		data_text["messages[user_ids][" + conversation + "][limit]"] = chunk_size
	else:
		data_text["messages[thread_fbids][" + conversation + "][offset]"] = offset
		data_text["messages[thread_fbids][" + conversation + "][timestamp]"] = timestamp
		data_text["messages[thread_fbids][" + conversation + "][limit]"] = chunk_size

	data = urllib.parse.urlencode(data_text)
	req = urllib.request.Request(REQ_URL, data.encode("ascii"), headers)

	print("Retrieving messages " + str(offset) + "-" + str(chunk_size + offset) + "...")
	
	response = urllib.request.urlopen(req)
	compressed = io.BytesIO(response.read())
	decompressedFile = gzip.open(compressed)

	messages_data = decompressedFile.read()
	messages_data = messages_data[9:]
	json_data = json.loads(messages_data)
	
	# Writes raw file
	with open(raw_dir + str(offset) + "-" + str(chunk_size + offset) + ".json", 'w') as outfile:
		json.dump(json_data, outfile, indent = "\t")

	if json_data is not None and json_data['payload'] is not None:
		# Bad config data
		if "__dialog" in json_data["payload"]:
			print("Bad config data.")
			sys.exit()
		try:
			if not raw_messages: # if this is the first batch, insert the whole thing
				raw_messages = json_data['payload']['actions']
			else:
				raw_messages = json_data['payload']['actions'][:-1] + raw_messages # if this isn't the first batch, the final
																	# message was already there in the previous batch
			timestamp = json_data['payload']['actions'][0]['timestamp']
		except KeyError:
			pass # no more messages
	else:
		print("Error retrieving. Retrying after " + str(config["error_timeout"]) + "s")
		print("Data Dump:")
		print(json_data)
		time.sleep(config["error_timeout"])
		continue

	offset += chunk_size
	time.sleep(config["general_timeout"])



print("Message count: " + str(len(raw_messages)) + ". Writing to file...");


# As not all fields are useful, filters only the interesting ones into a complete file
messages = []
for raw_msg in raw_messages:
	msg = {}

	try:
		# Writes name of participants if this is a not group chat
		if not is_group_conv:
			if raw_msg["author"] == "fbid:" + conversation:
				msg["author_name"] = conversation_name
			else:
				msg["author_name"] = "You"

		msg["author_id"] = raw_msg["author"]
		msg["time"] = datetime.datetime.utcfromtimestamp(raw_msg["timestamp"] / 1000).strftime('%Y-%m-%d %H:%M:%S')

		# Check if it is not a log message
		if "body" in raw_msg:
			msg["msg"] = raw_msg["body"]

			msg["att"] = {}
			# Check if there's an attachement
			if bool(raw_msg["has_attachment"]) and raw_msg["attachments"][0]["attach_type"] != "error":
				msg["att"]["type"] = raw_msg["attachments"][0]["attach_type"]
				msg["att"]["name"] = raw_msg["attachments"][0]["name"]
				msg["att"]["url"] = raw_msg["attachments"][0]["url"]
				msg["att"]["preview_url"] = raw_msg["attachments"][0]["preview_url"]
				msg["att"]["large_preview_url"] = raw_msg["attachments"][0]["large_preview_url"]
				msg["att"]["thumbnail_url"] = raw_msg["attachments"][0]["thumbnail_url"]
		else:
			msg["log_msg"] = raw_msg["log_message_body"]
	except KeyError as e:
		print(str(e.args[0]))


	messages.append(msg)
	
final_dump = []
final_dump.append(conversation)
final_dump.append(messages)

with open(dir + MESSAGES_FILE, 'w') as outfile:
    json.dump(final_dump, outfile, indent = "\t", )
 
print("Messages dump completed.")