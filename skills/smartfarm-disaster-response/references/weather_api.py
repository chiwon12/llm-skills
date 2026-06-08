"""기상청 단기예보 API — 위경도→격자 변환 + API 호출"""
import math, requests
from datetime import datetime, timedelta

def latlon_to_grid(lat: float, lon: float) -> tuple[int, int]:
    RE,GRID=6371.00877,5.0; SLAT1,SLAT2,OLON,OLAT,XO,YO=30.0,60.0,126.0,38.0,43,136
    D=math.pi/180; re=RE/GRID
    sn=math.log(math.cos(SLAT1*D)/math.cos(SLAT2*D))/math.log(math.tan(math.pi*.25+SLAT2*D*.5)/math.tan(math.pi*.25+SLAT1*D*.5))
    sf=(math.tan(math.pi*.25+SLAT1*D*.5)**sn)*math.cos(SLAT1*D)/sn
    ro=re*sf/(math.tan(math.pi*.25+OLAT*D*.5)**sn)
    ra=re*sf/(math.tan(math.pi*.25+lat*D*.5)**sn)
    theta=(lon*D-OLON*D)*sn
    if theta>math.pi: theta-=2*math.pi
    if theta<-math.pi: theta+=2*math.pi
    return int(ra*math.sin(theta)+XO+.5), int(ro-ra*math.cos(theta)+YO+.5)

def get_base_time():
    now=datetime.now(); bts=[2,5,8,11,14,17,20,23]; v=[t for t in bts if t<=now.hour]
    if not v: now-=timedelta(days=1); bh=23
    else: bh=v[-1]
    return now.strftime("%Y%m%d"), f"{bh:04d}"

def get_weather_forecast(lat: float, lon: float, api_key: str) -> dict:
    nx,ny=latlon_to_grid(lat,lon); bd,bt=get_base_time()
    url="http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    p=dict(serviceKey=api_key,pageNo=1,numOfRows=1000,dataType="JSON",base_date=bd,base_time=bt,nx=nx,ny=ny)
    resp=requests.get(url,params=p,timeout=10); resp.raise_for_status()
    items=resp.json()["response"]["body"]["items"]["item"]
    r={"nx":nx,"ny":ny,"snow_depth":"0","precip_type":0}
    for i in items:
        c,v=i["category"],i["fcstValue"]
        if c=="TMN": r["min_temp"]=float(v)
        elif c=="TMX": r["max_temp"]=float(v)
        elif c=="WSD": r["wind_speed"]=max(r.get("wind_speed",0),float(v))
        elif c=="SNO" and v!="적설없음": r["snow_depth"]=v
        elif c=="PTY": r["precip_type"]=int(v)
    return r
