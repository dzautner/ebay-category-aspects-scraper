# eBay ended biddings and aspects scrper

This script will listen and store every ending bidding on a given eBay category to mongodb and enrich it with every aspect in the category.
## Setup
I recommend using virtualenv to have a sanitised environment with the correct dependencies.
  
e.g:

```bash  
git clone https://github.com/dzautner/ebay-category-aspects-scraper
cd ebay-category-aspects-scraper
virtualenv .
source bin/activate
pip3 install -r requirements.txt  
```

You will also need to obtain a valid eBay App ID. 
You can get one by registering via:
https://go.developer.ebay.com/
## Usage

Simply run `scrape.py` with the required params, e.g:

```python
python3 scrape.py \
	--mongodb-connection="mongodb://localhost:27017/" \
	--mongodb-database="ebay" \
	--mongodb-collection="listings" \
	--app-id="DanielZa-coinrde-PRD-secret-secret" \
	--category-id="18465" \
	--site-id="EBAY-DE"
```


### Params:

#### mongodb-connection
A connection string for mongodb 

#### mongodb-database
The database to which the listings will be stored

#### mongodb-collection

The collection to which the listings will be stored

#### app-id

Your eBay App ID

#### category-id 

The category ID to listen and scrape from. Note that this changes from site to site, so the category ID for "shoes" for example would be different on eBay.com and eBay.co.uk
  
#### site-id

The eBay site ID to scrape from. For example "EBAY-US" for eBay.com or "EBAY-DE" for eBay.de.
A full list of sites and their global IDs could be found here:
https://developer.ebay.com/devzone/merchandising/docs/concepts/siteidtoglobalid.html

## What is an aspect?

Every eBay category as the concept of "aspects" (https://developer.ebay.com/devzone/finding/callref/types/Aspect.html),

which are, to quote from eBay's API manual:

"Characteristic of an item in a category. 
For example, "Shoes Size" or "Style" might be aspects of the Men's Shoes category, while "Genre" and "Album Type" could be aspects of the Music CDs category."

## Aspect collection

eBay doesn't reveal the aspects of every listing, which makes it difficult to collect accurate data.

To get pass this limitation in a way that doesn't contradict eBay's API rules the script will go through every aspect of the given category and filter only the items in that aspect, updating the mongodb listings with the currently filtered aspect value.

This sounds quite abstract and slightly confusing, a better way to understand the mechanism and the value of the script is by explaining the way the collection algorithm actually works:

* 1) Get all possible "aspects" of input eBay category and their possible values
* 2) build a list of all possible "aspect" - "aspect value" pairs
* 3) pop a pair of "aspect" - "aspect value" from the list
* 4) list the latest hundred listings in the category where "aspect" equals "aspect value"
** 4.1) for every listing, check if the listing is stored:
*** 4.1.1) if it is:
	 	check if contains value for "aspect", if it does not then update the listing's "aspect" with "aspect value"
*** 4.1.2) if it doesn't:
		store it with "aspect" equals "aspect value"
* 5) insert "aspect" - "aspect value" pair to beginning to the list
* 6) repeat ad-infinitum


Given listings in the category do not end in an extremely fast capacity, this method would end up collecting every listing and enriching it with the value of every aspect.

(Note: Not all listings have values for every aspect, in which case they will be marked under "Not Specified" in English sites, and the equivliant in other languages).


## Example listing
An example for an enriched listing that has been scraped:

```json
{
  "primaryCategory": {
    "categoryId": "4734",
    "categoryName": "Roman: Imperial (27 BC-476 AD)"
  },
  "viewItemURL": "http://www.ebay.com/itm/Constantius-coin-nicem-old-pagen-gods-/132302035275",
  "autoPay": "false",
  "title": "Constantius coin, nicem, old pagen gods",
  "listingInfo": {
    "bestOfferEnabled": "false",
    "buyItNowAvailable": "false",
    "endTime": "2017-09-16T13:05:01.000Z",
    "gift": "false",
    "startTime": "2017-08-21T00:54:09.000Z",
    "listingType": "StoreInventory"
  },
  "sellingStatus": {
    "convertedCurrentPrice": {
      "value": "7.0",
      "_currencyId": "USD"
    },
    "sellingState": "EndedWithSales",
    "currentPrice": {
      "value": "7.0",
      "_currencyId": "USD"
    }
  },
  "country": "US",
  "itemId": "132302035275",
  "isMultiVariationListing": "false",
  "shippingInfo": {
    "oneDayShippingAvailable": "false",
    "shippingServiceCost": {
      "value": "3.0",
      "_currencyId": "USD"
    },
    "shipToLocations": "Worldwide",
    "shippingType": "FlatDomesticCalculatedInternational",
    "expeditedShipping": "false",
    "handlingTime": "1"
  },
  "globalId": "EBAY-US",
  "galleryURL": "http://thumbs4.ebaystatic.com/m/mhpjQfgeYWeQfZvR8ZB4pgg/140.jpg",
  "returnsAccepted": "true",
  "topRatedListing": "true",
  "aspects": [
    {
      "aspectValueName": "Not Specified",
      "aspectName": "Composition"
    },
    {
      "aspectValueName": "Constantine I",
      "aspectName": "Ruler"
    },
    {
      "aspectValueName": "Not Specified",
      "aspectName": "Cleaned/Uncleaned"
    },
    {
      "aspectValueName": "Not Specified",
      "aspectName": "Grade"
    },
    {
      "aspectValueName": "Follis",
      "aspectName": "Denomination"
    },
    {
      "aspectValueName": "Not Specified",
      "aspectName": "Certification"
    }
  ],
  "paymentMethod": "PayPal",
  "postalCode": "75067",
  "location": "Lewisville,TX,USA"
}
```