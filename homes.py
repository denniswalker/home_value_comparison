# Find Valuable Homes

import re
import urllib.parse
import urllib.request
import operator
import sqlite3

DEFAULT_ZIPCODES = ("89138", "89135")


def get_db_connection(filename="homes.db"):
    return sqlite3.connect(filename)


def db_setup(filename="homes.db"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE homes (current_price real, last_price real, last_sold_date text, address text, url text, price_change real, price_per_sqft real, sqft  real, beds real, baths real) ''')
    conn.commit()
    conn.close()


def add_house_to_db(cursor, house):
    cursor.execute('''INSERT INTO homes VALUES (?,?,?,?,?,?,?,?,?,?)''',
                   (
                       house['price'],
                       house['last_sold_price'],
                       house['last_sold_date'],
                       house['address'],
                       house['url'],
                       house['valuation'],
                       house['price_per_sqft'],
                       house['sqft'],
                       house['beds'],
                       house['baths'],
                   ))


def store_houses_in_db(houses):
    conn = get_db_connection()
    c = conn.cursor()
    for house in houses:
        try:
            add_house_to_db(c, house)
            conn.commit()
        except sqlite3.OperationalError:
            pass
    conn.close()


def process_listing(zipcode, price, address, homedetails):
    print("Processing: {}, {}".format(address, price))
    home_url = "http://www.zillow.com/homedetails/" + homedetails + "_zpid/"
    req = urllib.request.Request(home_url)
    resp = urllib.request.urlopen(req)
    home_resp_data = resp.read()
    last_sold = re.findall(r'<li>Last sold: (.*?)</li>', str(home_resp_data))
    sqft = re.findall('class="addr_bbs">(\d,\d*?) sqft</span>', str(home_resp_data))
    try:
        beds = int(re.findall('class="addr_bbs">(\d*) beds</span>', str(home_resp_data))[0])
    except IndexError:
        beds = 0
    try:
        baths = int(re.findall('class="addr_bbs">(\d*) baths</span>', str(home_resp_data))[0])
    except IndexError:
        baths = 0

    if(last_sold):
        h_price = "".join(last_sold).split(" for ")
        last_sold_date = h_price[0]
        last_sold_price = int(re.sub('[^\d]', '', h_price[1]))
        price = int(re.sub('[^\d]', '', price))
        valuation = last_sold_price / price
        if sqft:
            sqft = int(re.sub(',', '', sqft[0]))
            price_per_sqft = price / sqft
        else:
            sqft = 1
            price_per_sqft = 1
        return {
            'price': price,
            'address': str(address) + " " + zipcode,
            'url': home_url,
            'last_sold_date': last_sold_date,
            'last_sold_price': last_sold_price,
            'valuation': valuation,
            'price_per_sqft': price_per_sqft,
            'sqft': sqft,
            'beds': beds,
            'baths': baths
        }
    return None


def crawl_zip(zipcode):
    print("Searching {}".format(zipcode), end="", flush=True)
    homes = []
    url = "http://www.zillow.com/homes/" + zipcode + "_rb/"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    respData = resp.read()

    prices = re.findall(r'<dt class="price-large zsg-h2">(.*?)</dt>', str(respData))
    addresses = re.findall(r'class="hdp-link hdp-link routable">(.*?)</a>', str(respData))
    homedetails = re.findall(r'<a href="/homedetails/(.*?)_zpid', str(respData))
    print("...{} houses found".format(len(prices)), flush=True)
    for price in prices:
        if 'mo' not in price:
            index_of_price = prices.index(price)
            homes.append(
                process_listing(
                    zipcode,
                    price,
                    addresses[index_of_price],
                    homedetails[index_of_price*2]
                )
            )
    return [x for x in homes if x is not None]


def iterate_zipcodes(zips=DEFAULT_ZIPCODES):
    homes = []
    for zipcode in zips:
        homes.extend(crawl_zip(zipcode))
    return homes


def print_by_appreciation(homes):
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
            print("Beds :  " + str(home['beds']))
            print("Baths :  " + str(home['baths']))
        print("\n")

if __name__ == "__main__":
    try:
        db_setup()
    except sqlite3.OperationalError:
        pass
    houses = iterate_zipcodes()
    store_houses_in_db(houses)
    print_by_appreciation(houses)
