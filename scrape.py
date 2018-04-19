from ebaysdk.finding import Connection
import time
import pymongo
import json
import argparse

'''
Example usage:


python3 scrape2.0.py \
	--mongodb-connection="mongodb://localhost:27017/" \
	--mongodb-database="ebay" \
	--mongodb-collection="listings" \
	--app-id="DanielZa-coinrde-PRD-secret-secret" \
	--category-id="18465" \
	--site-id="EBAY-DE"
'''

parser = argparse.ArgumentParser()

parser.add_argument("--mongodb-connection", type=str,
                    help="A mongodb connection string to which the listing would be saved. Example: mongodb://localhost:27017/")

parser.add_argument("--mongodb-database", type=str,
                    help="The database to which the listings would be save to. Example: ebay")

parser.add_argument("--mongodb-collection", type=str,
                    help="The collection to which the listings would be save to. Example: listings")

parser.add_argument("--app-id", type=str,
                    help="Registered eBay App ID. See: https://go.developer.ebay.com/")

parser.add_argument("--category-id", type=str,
                    help="The ID of the category to scrape. Example: 18465. Note that these change between different ebay sites.")

parser.add_argument("--site-id", type=str,
                    help="eBay site Global ID. Example: 'EBAY-DE'. See: https://developer.ebay.com/devzone/merchandising/docs/concepts/siteidtoglobalid.html")


parser.add_argument("--sleep-time", type=int, default=5,
                    help="Sleep time before everyr request.")

args = parser.parse_args()

client = pymongo.MongoClient(args.mongodb_connection)

db = client[args.mongodb_database]

APP_ID = args.app_id

COLLECTION = args.mongodb_collection

SLEEP_TIME = args.sleep_time

api = Connection(siteid=args.site_id, appid=args.app_id, config_file=None)

histogram_response = api.execute('getHistograms', {
	'categoryId': args.category_id,
})

aspects = histogram_response.reply.aspectHistogramContainer.aspect

queue = []

for aspect in aspects: 
	name = aspect._name
	for value in aspect.valueHistogram:
		queue.append({
			'aspectName': aspect._name,
			'aspectValueName': value._valueName
		})

#TODO: actual loging 
def log(line):
	print(line)

while True:
	aspect = queue.pop()
	log("Handling %s = %s\n" % (aspect['aspectName'], aspect['aspectValueName']))
	queue.insert(0, aspect)
	try:
		response = api.execute('findCompletedItems', {
			'categoryId': args.category_id,
			'sortOrder': 'EndTimeSoonest',
			'paginationInput': { 'pageNumber': '1' },
			'aspectFilter': aspect
		})	
		
		result = json.loads(response.json())
		
		if result['ack'] != 'Success':
			continue

		if result['paginationOutput']['totalEntries'] == '0':
			continue

		items = result['searchResult']['item']
		for normalized in items:
			item = db[COLLECTION].find_one({ 'itemId': normalized['itemId'] })
			if item is None:
				normalized['aspects'] = [aspect]
				db[COLLECTION].insert_one(normalized)
				continue
			if aspect not in item['aspects']:
				item['aspects'].append(aspect)
				db[COLLECTION].update_one({'_id': item['_id']}, {"$set": item}, upsert=False)
		time.sleep(SLEEP_TIME)
	except Exception as e:
		log("Failed for %s with %s\n" % (aspect, e))