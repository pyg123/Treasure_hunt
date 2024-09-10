import requests
import json
from tqdm import tqdm
import numpy as np

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

def calculate_manhattan_distance(lat1, lon1, lat2, lon2):
    return abs(lat1 - lat2) + abs(lon1 - lon2)

def find_suitable_location():
    token = get_onemap_token()
    
    print("正在搜索新加坡国立大学内的建筑...")
    nus_buildings = search_amenities(token, "nus", "1.295755,103.776695", 1.500)
    
    print("正在搜索停车场...")
    carparks = search_amenities(token, "carpark", "1.295755,103.776695", 1.500)
    
    suitable_locations = {}
    
    print("正在分析位置...")
    for building in tqdm(nus_buildings, desc="分析建筑"):
        building_lat = float(building['LATITUDE'])
        building_lon = float(building['LONGITUDE'])
        
        for carpark in tqdm(carparks, desc="分析停车场", leave=False):
            carpark_lat = float(carpark['LATITUDE'])
            carpark_lon = float(carpark['LONGITUDE'])
            
            key = (building['BUILDING'], carpark['BUILDING'])
            suitable_locations[key] = []
            
            # 计算满足条件的位置
            for lat in tqdm(range(int(min(building_lat, carpark_lat)*10000), int(max(building_lat, carpark_lat)*10000)), desc="搜索纬度", leave=False):
                for lon in range(int(min(building_lon, carpark_lon)*10000), int(max(building_lon, carpark_lon)*10000)):
                    lat, lon = lat/10000, lon/10000
                    distance_to_building = calculate_manhattan_distance(lat, lon, building_lat, building_lon)
                    distance_to_carpark = calculate_manhattan_distance(lat, lon, carpark_lat, carpark_lon)
                    
                    if distance_to_building <=0.3 and distance_to_carpark <=0.6:
                        suitable_locations[key].append((lat, lon))
    
    print(f"找到 {len(suitable_locations)} 对建筑和停车场的组合")
    
    # 计算每对建筑和停车场的中心点
    center_locations = []
    for (building, carpark), locations in suitable_locations.items():
        if locations:
            center_lat = np.mean([loc[0] for loc in locations])
            center_lon = np.mean([loc[1] for loc in locations])
            center_locations.append({
                "latitude": center_lat,
                "longitude": center_lon,
                "building": building,
                "carpark": carpark
            })
    
    print(f"计算得到 {len(center_locations)} 个中心点")
    
    # 将结果保存为JSON文件
    with open('suitable_locations.json', 'w', encoding='utf-8') as f:
        json.dump(center_locations, f, ensure_ascii=False, indent=4)
    
    print("合适的地点已保存为 suitable_locations.json")

find_suitable_location()
