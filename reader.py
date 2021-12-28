import datetime
import sys
import threading
import bluepy.btle as btle
import json

smartwatch = btle.Peripheral()
smartData = {"healthSportData": {}, "sleepData": {}, "hearthRate": {}}



def handle(cHandle, data):
    global smartData
    data = data.hex()
    # print(f"A notification was received: handler:{hex(cHandle)}, data: {data}")
    if data[0:4] == "0803":
        if data[4:6] == "01":
            # the first message "cleans" eventual remaining data from last use
            print("healthSportData")
            smartData["healthSportData"]["hex"] = data[
                                                  8:]  # removing useless header 08030n from the message, only data present
        else:
            smartData["healthSportData"]["hex"] += data[8:]
    elif data[0:4] == "0804":
        if data[4:6] == "01":
            print("sleepData")
            smartData["sleepData"]["hex"] = data[8:]
        else:
            smartData["sleepData"]["hex"] += data[8:]
    elif data[0:4] == "0807":
        if data[4:6] == "01":
            print("hearthRate")
            smartData["hearthRate"]["hex"] = data[8:]
        else:
            smartData["hearthRate"]["hex"] += data[8:]


def parse(request):
    smartwatch.writeCharacteristic(0x0018, request, True)
    request = request.hex()
    while smartwatch.waitForNotifications(3):
        pass

    bigEndianList = []
    if request[0:4] == "0803":
        for i in range(0, len(smartData["healthSportData"]["hex"]), 2):
            bigEndianList.insert(0, smartData["healthSportData"]["hex"][i:i + 2])
        smartData["healthSportData"]["hex"] = bigEndianList
        smartData["healthSportData"]["year"] = int("0x" + "".join(smartData["healthSportData"]["hex"][-2:]), 16)
        smartData["healthSportData"]["month"] = int("0x" + "".join(smartData["healthSportData"]["hex"][-3:-2]), 16)
        smartData["healthSportData"]["day"] = int("0x" + "".join(smartData["healthSportData"]["hex"][-4:-3]), 16)
        smartData["healthSportData"]["totalStep"] = int("0x" + "".join(smartData["healthSportData"]["hex"][-20:-16]),
                                                        16)
        smartData["healthSportData"]["caloriesTot"] = int("0x" + "".join(smartData["healthSportData"]["hex"][-24:-20]),
                                                          16)
        smartData["healthSportData"]["distanceTotMeters"] = int(
            "0x" + "".join(smartData["healthSportData"]["hex"][-28:-24]), 16)
        smartData["healthSportData"]["secondsActivitiesTot"] = int(
            "0x" + "".join(smartData["healthSportData"]["hex"][-32:-28]), 16)

    elif request[0:4] == "0804":
        # analyzing the first 2 message
        for i in range(0, len(smartData["sleepData"]["hex"]), 2):
            bigEndianList.insert(0, smartData["sleepData"]["hex"][i:i + 2])
        smartData["sleepData"]["hex"] = bigEndianList
        smartData["sleepData"]["year"] = int("0x" + "".join(smartData["sleepData"]["hex"][-2:]), 16)
        smartData["sleepData"]["month"] = int("0x" + "".join(smartData["sleepData"]["hex"][-3:-2]), 16)
        smartData["sleepData"]["day"] = int("0x" + "".join(smartData["sleepData"]["hex"][-4:-3]), 16)
        hour = int("0x" + "".join(smartData["sleepData"]["hex"][-5:-4]), 16)
        minutes = int("0x" + "".join(smartData["sleepData"]["hex"][-6:-5]), 16)
        smartData["sleepData"]["wakeup"]= f"{hour}:{minutes}"
        smartData["sleepData"]["sleepingTime"] = int("0x" + "".join(smartData["sleepData"]["hex"][-8:-6]), 16)
        smartData["sleepData"]["boh"] = int("0x" + "".join(smartData["sleepData"]["hex"][-9:-8]), 16)
        wake = datetime.datetime.timestamp(datetime.datetime.strptime(
            f"{smartData['sleepData']['day']}/{smartData['sleepData']['month']}/{smartData['sleepData']['year']},"
            f"{smartData['sleepData']['wakeup']}", "%d/%m/%Y,%H:%M"))
        timeFallenAsleep = wake - (smartData["sleepData"]["sleepingTime"]*60) + (2*3600) # *3600 is to compensate for GTM +2. 
        smartData["sleepData"]["timeFallenAsleep"] = str(datetime.timedelta(seconds=timeFallenAsleep))[-8:-3].replace(" ", "0")
        smartData["sleepData"]["lightSleepPhases"] = int("0x" + "".join(smartData["sleepData"]["hex"][-17:-16]), 16)
        smartData["sleepData"]["deepSleepPhases"] = int("0x" + "".join(smartData["sleepData"]["hex"][-18:-17]), 16)
        smartData["sleepData"]["awakeSleepPhases"] = int("0x" + "".join(smartData["sleepData"]["hex"][-19:-18]), 16)
        smartData["sleepData"]["lightSleepMinutes"] = int("0x" + "".join(smartData["sleepData"]["hex"][-21:-19]), 16)
        smartData["sleepData"]["deepSleepMinutes"] = int("0x" + "".join(smartData["sleepData"]["hex"][-23:-21]), 16)
        smartData["sleepData"]["awakeSleepMinutes"] = smartData["sleepData"]["sleepingTime"] - (
                smartData["sleepData"]["lightSleepMinutes"] + smartData["sleepData"]["deepSleepMinutes"])
        smartData["sleepData"]["phases"] = {}

        # analyzing remaining messages and saving them in a dict {time:kind of sleep.}
        # 1 is awake, 2 is light, 3 is deep
        time = 0
        for i in range(len(bigEndianList) - 33, 0, -2):
            time += int("0x" + bigEndianList[i - 1], 16)
            smartData["sleepData"]["phases"][time] = int("0x" + bigEndianList[i], 16)

    elif request[0:4] == "0807":
        for i in range(0, len(smartData["hearthRate"]["hex"]), 2):
            bigEndianList.insert(0, smartData["hearthRate"]["hex"][i:i + 2])
        smartData["hearthRate"]["hex"] = bigEndianList
        smartData["hearthRate"]["year"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-2:]), 16)
        smartData["hearthRate"]["month"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-3:-2]), 16)
        smartData["hearthRate"]["day"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-4:-3]), 16)
        smartData["hearthRate"]["startTime"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-6:-4]), 16)
        smartData["hearthRate"]["silentHeart"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-7]), 16)
        


        smartData["hearthRate"]["aerobicThreshold"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-17]), 16)
        smartData["hearthRate"]["burnFatThreshold"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-18]), 16)
        smartData["hearthRate"]["limitThreshold"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-19]), 16)
        smartData["hearthRate"]["fatBurningMinutes"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-21:-19]), 16)
        smartData["hearthRate"]["aerobicMinutes"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-23:-21]), 16)
        smartData["hearthRate"]["???Minutes"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-25:-23]), 16)
        smartData["hearthRate"]["warmupThreshold"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-26]), 16)
        smartData["hearthRate"]["warmupMinutes"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-28:-26]), 16)
        smartData["hearthRate"]["anaerobicThreshold"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-29]), 16)
        smartData["hearthRate"]["??Minutes"] = int("0x" + "".join(smartData["hearthRate"]["hex"][-31:-29]), 16)
        smartData["hearthRate"]["time"] = {}

        time = 0
        for i in range(len(bigEndianList) - 33, 0, -2):
            time += int("0x" + bigEndianList[i], 16)
            smartData["hearthRate"]["time"][time] = int("0x" + bigEndianList[i+1], 16)
        pass


def setup(addr):
    global smartwatch
    smartwatch = btle.Peripheral(addr, btle.ADDR_TYPE_RANDOM)
    smartwatch.delegate.handleNotification = handle
    smartwatch.writeCharacteristic(0x0016, b'\x01\x00', True)


def readAll():
    parse(b'\x08\x04\x01')
    parse(b'\x08\x03\x01')
    parse(b'\x08\x07\x01')


def save(filepath):
    dumpDict = {}

    try:
        with open(filepath, 'r') as f:
            dumpDict.update(json.load(f))
    except FileNotFoundError:
        print(f"file {filepath} doesn't exist, creating it")
        pass

    thread.join()
    for val in smartData:
        del smartData[val]['hex']
    dumpDict[datetime.datetime.now().date().isoformat()] = smartData
    with open(filepath, 'w') as f:
        json.dump(dumpDict, f, indent=4)

    pass

thread = threading.Thread(target=readAll)

def main(address="e7:40:b8:61:56:5e", filepath=sys.argv[1]):
    setup(address)
    thread.start()
    save(filepath)
    smartwatch.disconnect()


if __name__ == '__main__':
    main()
