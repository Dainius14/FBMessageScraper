import io
import json
import gzip
import os
import urllib
import urllib.parse
import urllib.request
import sys

IMG_REQ_URL = "https://www.facebook.com/webgraphql/query/?query_id="
CONFIG_FILE = "config.json"
MESSAGES_FILE = "messages.json"
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
	dir_name = sys.argv[2]
	query_id = sys.argv[3]

	while not dir_name in os.listdir("messages"):
		print("Folder does not exist!")
		dir_name = input("Folder with messages: ")
else:
	# Folder name with messages
	dir_name = input("Folder with messages: ")
	while not dir_name in os.listdir("messages"):
		print("Folder does not exist!")
		dir_name = input("Folder with messages: ")

	# Query ID
	query_id = input("Query ID: ")
	print()


dir = "messages/" + dir_name + "/"
img_dir = dir + "img/"

try:
	os.makedirs(img_dir)
except OSError:
	pass # already exists


# Supplying config file via command-line arguments
if len(sys.argv) >= 2:
	CONFIG_FILE = sys.argv[1]

with open(CONFIG_FILE) as configFile:
	config = json.load(configFile)


data_text = { "client": "web_messenger",
			  "__user": config["user"],
			  "__a": config["a"],
			  "__dyn": config["dyn"],
			  "__req": config["req"],
			  "__rev": config["rev"],
			  "fb_dtsg": config["fb_dtsg"],
			  "ttstamp": config["ttstamp"] }
img_data = urllib.parse.urlencode(data_text)

headers = HEADERS
headers["cookie"] = config["cookie"]

with open(dir + MESSAGES_FILE, "r") as infile:
	file_data = json.load(infile)
	conversation = file_data[0]
	messages = file_data[1]

# Gets message count
total_count = 0
for msg in messages:
	if "msg" in msg and len(msg["att"]) > 0 and msg["att"]["type"] == "photo":
		total_count += 1
		
print("Total image count: " + str(total_count))
print("Starting download...")

current = 0
for msg in messages:
	if "msg" in msg and len(msg["att"]) > 0 and msg["att"]["type"] == "photo":
		img_name = msg["att"]["name"][6:]
		req = IMG_REQ_URL + '{0}&variables={{"id":"{1}","photoID":"{2}"}}'.format(query_id, conversation, img_name)
		req = urllib.request.Request(req, img_data.encode("ascii"), headers)

		response = urllib.request.urlopen(req)
		compressed = io.BytesIO(response.read())
		decompressedFile = gzip.open(compressed)

		messages_data = decompressedFile.read()
		messages_data = messages_data[9:]
		json_data = json.loads(messages_data)
	
		try:
			img_url = json_data["payload"][conversation]["message_shared_media"]["edges"][0]["node"]["image2"]["uri"]
		except:
			try:
				img_url = json_data["payload"][conversation]["message_shared_media"]["edges"][0]["node"]["image1"]["uri"]
			except:
				continue

		# Image name is the date of when it was sent
		img_name = msg["time"].replace(":", ".")
		with urllib.request.urlopen(img_url) as response, open(img_dir + img_name + ".jpg", "wb") as outfile:
			img = response.read()
			outfile.write(img)

		# Reports progress
		current += 1
		if current % 10 == 0:
			print(str(round(100 * current / total_count)) + "% done. Images downloaded: " + str(current))


print("Download completed.")