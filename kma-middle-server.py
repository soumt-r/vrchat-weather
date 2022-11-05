import datetime
import requests
import math
import os
import json
import re
from flask import Flask
from flask_restx import Api, Resource
from flask_apscheduler import APScheduler


NX = 149            ## X축 격자점 수
NY = 253            ## Y축 격자점 수

Re = 6371.00877     ##  지도반경
grid = 5.0          ##  격자간격 (km)
slat1 = 30.0        ##  표준위도 1
slat2 = 60.0        ##  표준위도 2
olon = 126.0        ##  기준점 경도
olat = 38.0         ##  기준점 위도
xo = 210 / grid     ##  기준점 X좌표
yo = 675 / grid     ##  기준점 Y좌표
first = 0

if first == 0 :
    PI = math.asin(1.0) * 2.0
    DEGRAD = PI/ 180.0
    RADDEG = 180.0 / PI


    re = Re / grid
    slat1 = slat1 * DEGRAD
    slat2 = slat2 * DEGRAD
    olon = olon * DEGRAD
    olat = olat * DEGRAD

    sn = math.tan(PI * 0.25 + slat2 * 0.5) / math.tan(PI * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(PI * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(PI * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)
    first = 1

def mapToGrid(lat, lon, code = 0 ):
    ra = math.tan(PI * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > PI :
        theta -= 2.0 * PI
    if theta < -PI :
        theta += 2.0 * PI
    theta *= sn
    x = (ra * math.sin(theta)) + xo
    y = (ro - ra * math.cos(theta)) + yo
    x = int(x + 1.5)
    y = int(y + 1.5)
    return x, y

def gridToMap(x, y, code = 1):
    x = x - 1
    y = y - 1
    xn = x - xo
    yn = ro - y + yo
    ra = math.sqrt(xn * xn + yn * yn)
    if sn < 0.0 :
        ra = -ra
    alat = math.pow((re * sf / ra), (1.0 / sn))
    alat = 2.0 * math.atan(alat) - PI * 0.5
    if math.fabs(xn) <= 0.0 :
        theta = 0.0
    else :
        if math.fabs(yn) <= 0.0 :
            theta = PI * 0.5
            if xn < 0.0 :
                theta = -theta
        else :
            theta = math.atan2(xn, yn)
    alon = theta / sn + olon
    lat = alat * RADDEG
    lon = alon * RADDEG

    return lat, lon


base_url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0'
Key = os.environ['KMA_SERVICE_KEY']

def getWeather(lat, lon, base_date, base_time):
  url = '/getVilageFcst'
  x, y = mapToGrid(lat, lon)

  params = {'serviceKey' : Key, 'pageNo': '1', 'numOfRows': '1000', 'dataType': 'JSON', 'base_date': base_date, 'base_time': base_time, 'nx': x, 'ny': y}
  res = requests.get(base_url + url, params=params)
  data = res.json()
  return data

def getNowWeather(lat, lon, base_date, base_time):
  url = "/getUltraSrtNcst"
  x, y = mapToGrid(lat, lon)

  params = {'serviceKey' : Key, 'pageNo': '1', 'numOfRows': '1000', 'dataType': 'JSON', 'base_date': base_date, 'base_time': base_time, 'nx': x, 'ny': y}
  #print (base_url + url + '?serviceKey=' + Key + '&pageNo=1&numOfRows=1000&dataType=JSON&base_date=' + base_date + '&base_time=' + base_time + '&nx=' + str(x) + '&ny=' + str(y))
  res = requests.get(base_url + url, params=params)
  data = res.json()
  return data


def getBaseTime(targetTime):
  baseTime = targetTime.strftime('%H%M')
  base_times = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']
  for i in range(len(base_times)):
    if baseTime < base_times[i]:
      return base_times[i-1]
  return base_times[-1]

def getUltraBaseTime(targetTime):
  # 초단기예보는 30분마다 발표 01:30, 02:30 ...
  if targetTime.minute < 40:
    targetTime = targetTime - datetime.timedelta(minutes=(targetTime.minute + 30))
  else:
    targetTime = targetTime - datetime.timedelta(minutes=(targetTime.minute - 30))
  return targetTime.strftime('%H%M')

Loc_Seoul = (37.5665, 126.9780)
Loc_Incheon = (37.4562, 126.7052)
Loc_Gangwon_west = (37.6889, 127.8789)
Loc_Gangwon_east = (37.7510, 128.8734)
Loc_Chungnam = (36.6819, 126.8500)
Loc_Chungbuk = (36.6439, 127.4894)
Loc_Ulung = (37.4813, 130.8986)
Loc_Jeonnam = (34.8194, 126.8931)
Loc_Jeonbuk = (35.7167, 127.1449)
Loc_Gyeongnam = (35.2599, 128.6647)
Loc_Gyeongbuk = (36.2486, 128.6647)
Loc_Jeju = (33.3617, 126.5292)

Locs = [Loc_Seoul, Loc_Incheon, Loc_Gangwon_west, Loc_Gangwon_east, Loc_Chungnam, Loc_Chungbuk, Loc_Ulung, Loc_Jeonnam, Loc_Jeonbuk, Loc_Gyeongnam, Loc_Gyeongbuk, Loc_Jeju]
#Locs = [Loc_Seoul]





  #filesave
  #json.dumps(Wdata[i], indent=4, sort_keys=True, ensure_ascii=False)
  #with open('Wdata'+str(i)+'.json', 'w', encoding='utf-8') as make_file:
    #json.dump(Wdata[i], make_file, indent="\t")
  #with open('Wndata'+str(i)+'.json', 'w', encoding='utf-8') as make_file:
    #json.dump(Wndata[i], make_file, indent="\t")

  
# result data : (date)*(time)*(weather)
# (weather) : (w1)/(w2) ... / (w12)
# (w1~w12) : (1:now_temp):(2:today_weather):(3:now_weather2):(4:now_reh):(5:next_weather):(6:next_weather2):(7:next_min_temp):(8:next_max_temp):(9:next_rain_prob):(10:nnext_weather):(11:nnext_weather2):(12:nnext_min_temp):(13:nnext_max_temp):(14:nnext_rain_prob)

def findWeatherType(data, type, date, dayp):
  for i in data:
    if i['category'] == type:
      if i['fcstDate'] == (date + datetime.timedelta(days=dayp)).strftime('%Y%m%d'):
        return i['fcstValue']
  return '-'
def findNowWeatherType(data, type):
  for i in data:
    if i['category'] == type:
      return i['obsrValue']
  return '-'


def refresh():
  Wdata = []
  Wndata = []
  weather = ''
  today = datetime.datetime.now()
  for i in range(len(Locs)):
    base_time = getBaseTime(today)
    Wbase_time = getUltraBaseTime(today)
    base_date = today.strftime('%Y%m%d')
    Wdata.append(getWeather(Locs[i][0], Locs[i][1], today.strftime('%Y%m%d'), base_time))
    Wndata.append(getNowWeather(Locs[i][0], Locs[i][1], today.strftime('%Y%m%d'), Wbase_time))
  for i in range(len(Wdata)):
    weather += findNowWeatherType(Wndata[i]['response']['body']['items']['item'], 'T1H') + ':'
    weather += findWeatherType(Wdata[i]['response']['body']['items']['item'], 'SKY',today, 0) + ':'
    weather += findNowWeatherType(Wndata[i]['response']['body']['items']['item'], 'PTY') + ':'
    weather += findNowWeatherType(Wndata[i]['response']['body']['items']['item'], 'REH') + ':' 
    for j in range(2):
      weather += findWeatherType(Wdata[i]['response']['body']['items']['item'], 'SKY',today, j+1) + ':'
      weather += findWeatherType(Wdata[i]['response']['body']['items']['item'], 'PTY',today, j+1) + ':'
      weather += findWeatherType(Wdata[i]['response']['body']['items']['item'], 'TMN',today, j+1) + ':'
      weather += findWeatherType(Wdata[i]['response']['body']['items']['item'], 'TMX',today, j+1) + ':'
      weather += findWeatherType(Wdata[i]['response']['body']['items']['item'], 'POP',today, j+1) + ':'
    
    
    weather = weather[:-1]
    weather += '/'
  weather = weather[:-1]
  result_data = today.strftime('%Y%m%d') + '*' + base_time + '*' + weather
  data = {'data':result_data}
  with open('weather.json', 'w') as outfile:
    json.dump(data, outfile)
  print('refreshed')

app = Flask(__name__)
api = Api(app)
scheduler = APScheduler()

scheduler.add_job(id = 'Scheduled Task', func=refresh, trigger="cron", minute=45)
scheduler.start()

@api.route('/api/v1/weather')
class Weather(Resource):
  def get(self):
    with open('weather.json', 'r') as outfile:
      data = json.load(outfile)
    return data

@api.route('/api/v1/refresh')
class Refresh(Resource):
  def get(self):
    refresh()
    return {'result':'refreshed'}

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=5000, debug=True)