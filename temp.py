import requests
import json
import time
from tqdm import tqdm
from datetime import datetime

def get_onemap_token():
    print("正在获取OneMap令牌...")
    url = "https://www.onemap.gov.sg/api/auth/post/getToken"
    payload = {
        "email": "598281453@qq.com",
        "password": "Panyurui@123"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception("获取令牌失败")

def search_amenities(token, keyword, location, radius):
    print(f"正在搜索 {keyword}...")
    url = "https://www.onemap.gov.sg/api/common/elastic/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "searchVal": keyword,
        "returnGeom": "Y",
        "getAddrDetails": "Y"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()['results']
    else:
        raise Exception(f"搜索 {keyword} 失败")

def calculate_walking_time(distance):
    return distance / (5000 / 60)

def get_route(token, start, end):
    print(f"正在获取从 {start} 到 {end} 的路线...")
    url = "https://www.onemap.gov.sg/api/public/routingsvc/route"
    headers = {"Authorization": f"Bearer {token}"}
    current_time = datetime.now()
    params = {
        "start": start,
        "end": end,
        "routeType": "walk",
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S"),
        "mode": "TRANSIT",
        "numItineraries": 1
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # 如果状态码不是200，会抛出异常
    data = response.json()
    print(data)
    return data

def find_location():
    token = get_onemap_token()
    
    print("正在搜索新加坡国立大学内的建筑...")
    nus_buildings = search_amenities(token, "nus", "1.296568,103.776428", 2500)
    
    print("正在搜索停车场...")
    carparks = search_amenities(token, "carpark", "1.296568,103.776428", 2500)
    
    print("正在搜索热饮店...")
    drink_shops = search_amenities(token, "coffee", "1.296568,103.776428", 2500)
    
    suitable_locations = []
    
    print("正在分析位置...")
    for building in tqdm(nus_buildings):
        building_location = f"{building['LATITUDE']},{building['LONGITUDE']}"
        for carpark in carparks:
            carpark_location = f"{carpark['LATITUDE']},{carpark['LONGITUDE']}"
            
            route_to_carpark = get_route(token, building_location, carpark_location)
            if route_to_carpark is None:
                print(f"无法获取从 {building['BUILDING']} 到 {carpark['BUILDING']} 的路线")
                continue
            
            building_to_carpark_time = route_to_carpark['route_summary']['total_time']/ 60
            
            if 5.5 < building_to_carpark_time < 6.5:
                for shop in drink_shops:
                    shop_location = f"{shop['LATITUDE']},{shop['LONGITUDE']}"
                    
                    route_to_shop = get_route(token, building_location, shop_location)
                    if route_to_shop is None:
                        print(f"无法获取从 {building['BUILDING']} 到 {shop['BUILDING']} 的路线")
                        continue
                    
                    building_to_shop_time = route_to_shop['route_summary']['total_time'] / 60
                    
                    if 2.5 < building_to_shop_time < 3.5:
                        suitable_locations.append({
                            "building": building['BUILDING'],
                            "carpark": carpark['BUILDING'],
                            "drink_shop": shop['BUILDING'],
                            "building_to_carpark_time": building_to_carpark_time,
                            "building_to_shop_time": building_to_shop_time
                        })
    
    print("\n符合条件的位置：")
    for location in suitable_locations:
        print(f"新加坡国立大学建筑: {location['building']}")
        print(f"附近停车场: {location['carpark']}")
        print(f"附近热饮店: {location['drink_shop']}")
        print(f"建筑到停车场步行时间: {location['building_to_carpark_time']:.2f} 分钟")
        print(f"建筑到热饮店步行时间: {location['building_to_shop_time']:.2f} 分钟")
        print("---")

if __name__ == "__main__":
    find_location()
