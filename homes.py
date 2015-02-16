import re
import urllib.parse
import urllib.request
import operator
import sys

zips = ["89138","89135"]
homes = []

for zip in zips:
    url = "http://www.zillow.com/homes/" + zip + "_rb/"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    respData = resp.read()

    prices = re.findall(r'<dt class="price-large zsg-h2">(.*?)</dt>', str(respData))
    addresses = re.findall(r'class="hdp-link hdp-link routable">(.*?)</a>', str(respData))
    specs = re.findall(r'<dt class="property-data">(.*?)</dt>', str(respData))
    homedetails = re.findall(r'<a href="/homedetails/(.*?)_zpid', str(respData))
    print("Found " + str(prices.__len__()) + " homes in " + zip + " for sale. Fetching details...")
    i = 0

    for price in prices:
        if not 'mo' in price:
            home_url = "http://www.zillow.com/homedetails/" + homedetails[i*2] + "_zpid/"
            req = urllib.request.Request(home_url)
            resp = urllib.request.urlopen(req)
            home_resp_data = resp.read()
            last_sold = re.findall(r'<li>Last sold: (.*?)</li>', str(home_resp_data))
            sqft = re.findall('class="addr_bbs">(\d,\d*?) sqft</span>', str(home_resp_data))

            if(last_sold):
                h_price = "".join(last_sold).split(" for ")
                last_sold_date = h_price[0]
                last_sold_price = int(re.sub('[^\d]', '', h_price[1]))
                price = int(re.sub('[^\d]', '', price))
                valuation = last_sold_price / price
                if sqft:
                    sqft = int(re.sub(',', '', sqft[0]))
                    homes.append({
                        'price': price,
                        'address': addresses[i] + " " + zip,
                        'url': home_url,
                        'last_sold_date': last_sold_date,
                        'last_sold_price': last_sold_price,
                        'valuation': valuation,
                        'price_per_sqft': price / sqft,
                        'sqft': sqft
                    })

        sys.stdout.write('.')
        sys.stdout.flush()
        i += 1

homes_by_appreciation = sorted(homes, key=operator.itemgetter('price_per_sqft'))
print("\n")
for home in homes_by_appreciation:
    print("Current Price: $" + str(home['price']))
    print("Last Sold For: $" + str(home['last_sold_price']) + " at " + home['last_sold_date'])
    print("Address: " + home['address'])
    print("URL: " + home['url'])
    print("Change in price: " + str(home['valuation']))
    if 'price_per_sqft' in home:
        print("Price per sqft: $" + str(home['price_per_sqft']))
        print("Sq Ft:  " + str(home['sqft']))
    print("\n")
