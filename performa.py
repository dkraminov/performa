# coding: utf-8
from tornado import httpclient, ioloop
import sys
import os
import time

concurrency = 100
count = 1000
answers = 0
fetchers = 0
test_counter = 0
url = ""

timers = {
    "minimal": 10000000000.0,
    "maximal": 0.,
    "average": 0.0
}
rates = {
    "minimal": 10000000000.0,
    "maximal": 0.,
    "average": 0.0
}
errors = {
    "200": 0,
    "301": 0,
    "304": 0,
    "404": 0,
    "500": 0,
    "501": 0,
    "502": 0,
    "503": 0,
    "504": 0,
    "599": 0
}
infos = {
    "slowest_request": "",
    "fails": 0

}


def answer(data):
    global fetchers, answers, count, timers, errors, start_time, rates, infos, test_counter, concurrency
    if data.code == 200:
        errors["200"] += 1
    if data.code == 301:
        errors["301"] += 1
    if data.code == 304:
        errors["304"] += 1
    if data.code == 404:
        errors["404"] += 1
    if data.code == 500:
        errors["500"] += 1
    if data.code == 501:
        errors["501"] += 1
    if data.code == 502:
        errors["502"] += 1
    if data.code == 503:
        errors["503"] += 1
    if data.code == 504:
        errors["504"] += 1
    if data.code == 599:
        errors["599"] += 1
    finish_time = time.time()
    e_time = finish_time - start_time
    rate = round(answers / e_time, 2)
    sys.stdout.write("Concurrency: {}, answers: {}, fetchers: {}, rate: {} req/sec                         \r".format(concurrency, answers, fetchers, rate))
    if data.code != 200:
        infos["fails"] += 1
    fetchers = fetchers - 1
    answers = answers + 1
    if data.request_time < timers["minimal"]:
        timers["minimal"] = data.request_time
    if data.request_time > timers["maximal"]:
        timers["maximal"] = data.request_time
        infos["slowest_request"] = data.effective_url
    timers["average"] = (timers["average"] + data.request_time) / 2
    finish_time = time.time()
    e_time = finish_time - start_time
    rate = round(answers / e_time, 2)
    if data.code == 200:
        if rate < rates["minimal"]:
            rates["minimal"] = rate
        if rate > rates["maximal"]:
            rates["maximal"] = rate
        rates["average"] = (rates["average"] + rate) / 2
    if answers == count:
        stop_all()
        return True
    create_fetch()


def get_url_from_file():
    global url
    try:
        line = url.readline().strip()
        if " " in line:
            line = line.split(" ")[0]
        return line
    except:
        return False


def get_url():
    global url
    return url


def create_fetch():
    global fetchers
    work_url = get_url_func()
    if not work_url:
        stop_all()
        return
    http_client = httpclient.AsyncHTTPClient(max_clients=concurrency)
    # http_client = curl_httpclient.CurlAsyncHTTPClient()
    http_client.fetch(work_url, answer, request_timeout=6)
    http_client.close()
    fetchers = fetchers + 1


def stop_all():
    show_stat()
    ioloop.stop()
    exit()


def show_stat():
    global timers, errors, start_time, answers, rates, infos
    finish_time = time.time()
    e_time = finish_time - start_time
    print("\r                                                                      ")
    print("Total requests : {}".format(answers))
    print("Concurrency    : {}".format(concurrency))
    print("Elapsed time   : {:.4f}".format(e_time))
    print("")
    print("Transactions")
    print("   total       : {}".format(answers))
    print("   fail        : {}".format(infos["fails"]))
    print("   OK          : {}".format(answers - infos["fails"]))
    print("")
    print("Response time")
    print("   minimal     : {:.4f}".format(timers["minimal"]))
    print("   maximal     : {:.4f}".format(timers["maximal"]))
    print("   average     : {:.4f}".format(timers["average"]))
    print("")
    print("Transaction rate")
    print("   minimal     : {:.4f}".format(rates["minimal"]))
    print("   maximal     : {:.4f}".format(rates["maximal"]))
    print("   average     : {:.4f}".format(rates["average"]))
    print("")
    print("Errors")
    print("   200  (OK)                  : {}".format(errors["200"]))
    print("   301  (Moved)               : {}".format(errors["301"]))
    print("   304  (Not modified)        : {}".format(errors["304"]))
    print("   404  (Not found)           : {}".format(errors["404"]))
    print("   500  (Server error)        : {}".format(errors["500"]))
    print("   501  (??)                  : {}".format(errors["501"]))
    print("   502  (Bad gateway)         : {}".format(errors["502"]))
    print("   503  (Service Unavailable) : {}".format(errors["503"]))
    print("   504  (Gateway timeout)     : {}".format(errors["504"]))
    print("   599  (Operation timeout)   : {}".format(errors["599"]))
    print("")
    print("Slowest request: {}".format(infos["slowest_request"]))
    print("")

if len(sys.argv) < 2:
    sys.stderr.write("\nUSAGE: " + os.path.basename(sys.argv[0]) + " <URL>|<FILE_URL_LIST> [CONCURRENCY] [COUNT]\n\n")
    exit()

if sys.argv[1][:7] == "http://":
    url = sys.argv[1]
    get_url_func = get_url
elif not os.path.exists(sys.argv[1]):
    sys.stderr.write("\nFile " + os.path.basename(sys.argv[1]) + " doesn't exists\n\n")
    exit()
else:
    url = open(sys.argv[1])
    get_url_func = get_url_from_file
    count = 100000000000000

ioloop = ioloop.IOLoop.instance()
for i in range(concurrency):
    create_fetch()

start_time = time.time()
try:
    ioloop.start()
except KeyboardInterrupt:
    stop_all()
    pass
