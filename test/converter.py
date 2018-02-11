import json

with open('../data/train_station.txt', 'r', encoding='UTF-8') as file:
    data = {}
    for line in file.readlines():
        station = line.split(sep='\t')
        data[station[0].strip()] = station[1].strip()
    with open('../data/train_station_json.txt', 'w', encoding='UTF-8') as file1:
        file1.write(json.dumps(data, ensure_ascii=False))
