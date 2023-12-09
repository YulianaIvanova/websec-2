from flask import Flask, render_template,  request
import requests
import xml.etree.ElementTree as ET
import os.path
import hashlib
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

@app.route("/prediction")
def prediction():
    global counter
    counter += 1
    KS_ID = request.args.getlist("stopId")
    COUNT = 20

    #create xml
    first = ET.Element('request')
    method = ET.SubElement(first, 'method')
    parameters = ET.SubElement(first, 'parameters')
    stop_id = ET.SubElement(parameters, 'KS_ID')
    count = ET.SubElement(parameters, 'COUNT')
    method.text = 'getFirstArrivalToStop'
    stop_id.text = KS_ID[0]
    count.text = str(COUNT)
    
    hash_object = hashlib.sha1(ET.tostring(first, encoding="utf-8") + 
                               bytes("just_f0r_tests", encoding="utf-8")).hexdigest()

    data = {"message": ET.tostring(first, encoding="utf-8"),
            "os": "web",
            "clientId": "test",
            "authKey": hash_object}
    
    prediction = requests.post("https://tosamara.ru/api/v2/xml", data=data)
    content = prediction.content.decode()
    root = ET.fromstring(content)
    predictions = []
    for i in root:
        if i[15].text == "Метро" or i[15].text =="Железная дорога":
            i[16].text = '-'
            i[1].text = '-'
        result = {"id_transport": i[9].text,
                  "time": i[12].text,
                  "type": i[15].text,
                  "number": i[6].text,
                  "distance": i[16].text,
                    "stop": i[1].text}
        predictions.append(result)

    check_update("stops.xml", 5)
    stops = ET.parse("stops.xml")
    stops_root = stops.getroot()
    stop=""

    for i in stops_root:
        if KS_ID[0] == i[0].text:
            if i[2].text == None:
                i[2].text = ""
            if i[3].text == None:
                i[3].text == ""
            stop = i[1].text + "\n" + i[2].text + " " + i[3].text
    
    
    return render_template("prediction.html", predictions=predictions, stop=stop)


@app.route("/route")
def route():
    global counter
    counter += 1
    HULLNO = request.args.getlist("transportId")
    first = ET.Element('request')
    method = ET.SubElement(first, 'method')
    parameters = ET.SubElement(first, 'parameters')
    hullno = ET.SubElement(parameters, 'HULLNO')
    method.text = 'getTransportPosition'
    hullno.text = HULLNO[0]
    hash_object = hashlib.sha1(ET.tostring(
        first, encoding="utf-8") + bytes("just_f0r_tests", encoding="utf-8")).hexdigest()
    data = {"message": ET.tostring(first, encoding="utf-8"),
            "os": "web",
            "clientId": "test",
            "authKey": hash_object}
    
    route = requests.post("http://tosamara.ru/api/v2/xml", data=data)
    with open("tmp.xml", "wb") as f:
                f.write(route.content)
    content = route.content.decode()
    root_route = ET.fromstring(content)

    if root_route.tag == "ExceptionReport":
         return render_template("error_route.html")
    route_list = []
    route_id = root_route[0].text
    check_update('routes.xml',2)
    tree = ET.parse('routes.xml')
    root_r = tree.getroot()
    for i in root_r:
        if route_id == i[0].text:
            route_id = i[1].text + "  " +  i[6].text
    
    
    for i in root_route:
        for j in i:
            result= {"stop_id":j[0].text, "time":str(round(float(j[1].text)/60))}
            route_list.append(result)
    check_update("stops.xml", 5)
    tree = ET.parse('stops.xml')
    root_stops = tree.getroot()
    for i in route_list:
        for j in root_stops:
            if i["stop_id"] == j[0].text:
                i["stop_id"] = j[1].text
    #print(route_list)
   
    
    return render_template("route.html", route_id=route_id, route_list=route_list) 
    
    
if __name__ == "__main__":
    app.run(debug=True)
