from flask import Flask, render_template,  request
import requests
import xml.etree.ElementTree as ET
import os.path
counter = 0
date_update = 0
new_date_update = 0

app = Flask(__name__)


def check_update(file_path, type):
    if (os.path.exists("update.xml") == False):
            info = requests.get("https://tosamara.ru/api/v2/classifiers")
            with open("update.xml", "wb") as f:
                f.write(info.content)
            tree = ET.parse('update.xml')
            root = tree.getroot()
            global date_update
            date_update = root[5][0].text
    global counter
    if (counter == 100):
        info = requests.get("https://tosamara.ru/api/v2/classifiers")
        content = info.content.decode()
        root = ET.fromstring(content)
        global new_date_update 
        new_date_update = root[type][0].text
                   
    if (os.path.exists(file_path) == False or new_date_update > date_update):
        if file_path == "stops.xml":
            a = requests.get("https://tosamara.ru/api/v2/classifiers/stopsFullDB.xml")
        if file_path == "routes.xml":
            a = requests.get("http://tosamara.ru/api/v2/classifiers/routes.xml")
        with open(file_path, "wb") as f:
            f.write(a.content)
        date_update = new_date_update

@app.route("/")
def main():
    stops_info = []
    search_text = request.args.getlist("busStop")
    if len(search_text) == 0:
        return render_template("index.html")
    else:
        check_update("stops.xml", 5)
        search_text[0] = search_text[0].capitalize()
        global counter
        counter += 1
        #print(counter)
        tree = ET.parse('stops.xml')
        root = tree.getroot()
        for i in root:
            if i[1].text.find(search_text[0]) >= 0:
                if i[2].text == None: 
                    i[2].text = ""
                if i[3].text == None: 
                    i[3].text = ""
                tmp = {"stop_id": i[0].text, "title": i[1].text,
                       "location": i[2].text, "side": i[3].text}
                stops_info.append(tmp)
        return render_template("stops.html", stops=stops_info)

@app.route("/predication")
    
    
    


if __name__ == "__main__":
    app.run(debug=True)
