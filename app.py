# Instrument Rental is a free instrument library + people renting their instruments to others.
# The owner gets most of the money and the website keeps a small fee.

import json
import os
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

FEE = 0.10  # the website keeps 10%
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

# ---------------- Data ----------------
# Each instrument is a dictionary. "price" of 0 means it's from the free library.
instruments = [
    {"id": 1, "name": "Guitar", "owner": "Library", "price": 0, "available": True},
    {"id": 2, "name": "Violin", "owner": "Library", "price": 0, "available": True},
    {"id": 3, "name": "Guitar", "owner": "Alex", "price": 5, "available": True},
    {"id": 4, "name": "Guitar", "owner": "Sam", "price": 4, "available": True},
    {"id": 5, "name": "Keyboard", "owner": "Jordan", "price": 6, "available": True},
]
rentals = []


def save_data():
    file = open(DATA_FILE, "w")
    json.dump({"instruments": instruments, "rentals": rentals}, file)
    file.close()


def load_data():
    global instruments, rentals
    if os.path.exists(DATA_FILE):
        file = open(DATA_FILE)
        data = json.load(file)
        file.close()
        instruments = data["instruments"]
        rentals = data["rentals"]


def find_instrument(id):
    for item in instruments:
        if item["id"] == id:
            return item
    return None


# ---------------- Pages ----------------
STYLE = """
body { margin: 0; font-family: Arial, sans-serif; background: #f4f1fb; color: #2b2540; }
header { background: linear-gradient(135deg, #5b3cc4, #8e5cf7); color: white; padding: 22px 32px;
         display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
header h1 { margin: 0; }
nav a { color: white; text-decoration: none; margin-left: 8px; padding: 8px 14px;
        border-radius: 20px; background: rgba(255,255,255,.15); font-weight: bold; }
nav a:hover { background: rgba(255,255,255,.3); }
main { max-width: 1000px; margin: 32px auto; background: white; padding: 28px 32px;
       border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,.08); }
h2 { margin-top: 0; color: #5b3cc4; }
table { width: 100%; border-collapse: collapse; }
th { background: #ede7fd; color: #4a2fa8; text-align: left; padding: 12px; }
td { padding: 12px; border-bottom: 1px solid #eee8f7; }
tr:hover td { background: #faf8ff; }
input { padding: 8px; border: 1px solid #d3c9ef; border-radius: 8px; }
input[type=number] { width: 70px; }
button { background: #ff8a3d; color: white; border: none; padding: 9px 18px;
         border-radius: 8px; font-weight: bold; cursor: pointer; }
button:hover { background: #f06f1c; }
.free { color: #1a9e5c; font-weight: bold; }
.box { background: #f4f1fb; border-left: 5px solid #8e5cf7; padding: 16px 20px; border-radius: 8px; }
"""


def make_page(content):
    html = "<html><head><title>Instrument Rental</title><style>" + STYLE + "</style></head><body>"
    html += "<header><h1>&#127925; Instrument Rental</h1><nav>"
    html += "<a href='/'>Browse</a><a href='/list'>List an Instrument</a><a href='/rentals'>My Rentals</a>"
    html += "</nav></header><main>" + content + "</main></body></html>"
    return html


def browse_page(search):
    html = "<h2>Available Instruments</h2>"
    html += "<form action='/'>Search instrument: <input name='q' value='" + search + "'> <button>Search</button></form><br>"
    html += "<table><tr><th>Instrument</th><th>From</th><th>Price</th><th>Rent</th></tr>"

    found = False
    for item in instruments:
        if item["available"] and search.lower() in item["name"].lower():
            found = True
            if item["price"] == 0:
                price = "<span class='free'>Library (free)</span>"
            else:
                price = "$" + format(item["price"], ".2f") + "/day"
            html += "<tr><td>" + item["name"] + "</td><td>" + item["owner"] + "</td><td>" + price + "</td>"
            html += "<td><form method='post' action='/rent'>"
            html += "<input type='hidden' name='id' value='" + str(item["id"]) + "'>"
            html += "Your name: <input name='renter' required> "
            html += "Days: <input name='days' type='number' min='1' value='1' required> "
            html += "<button>Rent</button></form></td></tr>"

    if not found:
        html += "<tr><td colspan='4'>No instruments available.</td></tr>"
    html += "</table>"
    return make_page(html)


def list_page():
    html = "<h2>List Your Instrument</h2>"
    html += "<form method='post' action='/list'>"
    html += "Instrument: <input name='name' required><br><br>"
    html += "Your name: <input name='owner' required><br><br>"
    html += "Price per day ($): <input name='price' type='number' step='0.01' min='0' required><br><br>"
    html += "<button>List Instrument</button></form>"
    return make_page(html)


def rentals_page():
    html = "<h2>Current Rentals</h2>"
    html += "<table><tr><th>Instrument</th><th>From</th><th>Renter</th><th>Days</th><th>Total</th><th></th></tr>"
    if len(rentals) == 0:
        html += "<tr><td colspan='6'>No current rentals.</td></tr>"
    for i in range(len(rentals)):
        r = rentals[i]
        html += "<tr><td>" + r["name"] + "</td><td>" + r["owner"] + "</td><td>" + r["renter"] + "</td>"
        html += "<td>" + str(r["days"]) + "</td><td>$" + format(r["total"], ".2f") + "</td>"
        html += "<td><form method='post' action='/return'><input type='hidden' name='num' value='" + str(i) + "'>"
        html += "<button>Return</button></form></td></tr>"
    html += "</table>"
    return make_page(html)


def confirm_page(r):
    html = "<h2>Rental Confirmed</h2>"
    html += "<p>You rented a <b>" + r["name"] + "</b> from <b>" + r["owner"] + "</b> for " + str(r["days"]) + " day(s).</p>"
    html += "<p class='box'>Total: $" + format(r["total"], ".2f") + "<br>"
    html += "Owner receives: $" + format(r["owner_gets"], ".2f") + "<br>"
    html += "Platform fee: $" + format(r["fee"], ".2f") + "</p>"
    return make_page(html)


# ---------------- Actions ----------------
def rent_instrument(id, renter, days):
    item = find_instrument(id)
    if item == None or item["available"] == False:
        return make_page("<p>Sorry, that instrument is no longer available.</p>")
    total = item["price"] * days
    fee = round(total * FEE, 2)
    owner_gets = round(total - fee, 2)
    item["available"] = False
    rental = {"id": id, "name": item["name"], "owner": item["owner"], "renter": renter,
              "days": days, "total": total, "owner_gets": owner_gets, "fee": fee}
    rentals.append(rental)
    save_data()
    return confirm_page(rental)


def add_instrument(name, owner, price):
    new_id = len(instruments) + 1
    instruments.append({"id": new_id, "name": name, "owner": owner, "price": price, "available": True})
    save_data()


def return_instrument(num):
    rental = rentals.pop(num)
    item = find_instrument(rental["id"])
    item["available"] = True
    save_data()


# ---------------- Server ----------------
class Handler(BaseHTTPRequestHandler):

    def show(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def go_to(self, page):
        self.send_response(303)
        self.send_header("Location", page)
        self.end_headers()

    # Opening a page
    def do_GET(self):
        if self.path.startswith("/?"):
            query = parse_qs(self.path[2:])
            search = ""
            if "q" in query:
                search = query["q"][0]
            self.show(browse_page(search))
        elif self.path == "/":
            self.show(browse_page(""))
        elif self.path == "/list":
            self.show(list_page())
        elif self.path == "/rentals":
            self.show(rentals_page())
        else:
            self.send_error(404)

    # Clicking a button
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        form = parse_qs(self.rfile.read(length).decode())

        if self.path == "/rent":
            id = int(form["id"][0])
            renter = form["renter"][0]
            days = int(form["days"][0])
            self.show(rent_instrument(id, renter, days))
        elif self.path == "/list":
            add_instrument(form["name"][0], form["owner"][0], float(form["price"][0]))
            self.go_to("/")
        elif self.path == "/return":
            return_instrument(int(form["num"][0]))
            self.go_to("/rentals")


# ---------------- Start ----------------
load_data()
try:
    server = HTTPServer(("", 8000), Handler)
    print("Running at http://localhost:8000  (press Ctrl+C to stop)")
    webbrowser.open("http://localhost:8000")
    server.serve_forever()
except OSError:
    print("The website is already running. Opening it...")
    webbrowser.open("http://localhost:8000")
except KeyboardInterrupt:
    print("Stopped.")
