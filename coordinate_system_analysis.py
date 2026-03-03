#!/usr/bin/env python3
"""
氣象站坐標系統分析腳本
根據特徵辨識 TWD67 vs WGS84：TWD67緯度較高、經度較低
"""

import csv
import math
import os
from datetime import datetime

def identify_coordinate_system_by_pattern(lat1, lon1, lat2, lon2):
    """
    根據坐標特徵辨識坐標系統
    TWD67特徵：緯度較高、經度較低
    WGS84特徵：緯度較低、經度較高
    """
    
    # 比較緯度和經度
    lat_diff = lat1 - lat2
    lon_diff = lon1 - lon2
    
    # 判斷邏輯：
    # 如果坐標1的緯度較高且經度較低 → 坐標1是TWD67，坐標2是WGS84
    # 如果坐標1的緯度較低且經度較高 → 坐標1是WGS84，坐標2是TWD67
    # 如果差異很小或模式不明確，基於主要特徵判斷
    
    if lat_diff > 0.0001 and lon_diff < -0.0001:
        # 坐標1緯度較高、經度較低
        system1 = "TWD67"
        system2 = "WGS84"
    elif lat_diff < -0.0001 and lon_diff > 0.0001:
        # 坐標1緯度較低、經度較高
        system1 = "WGS84"
        system2 = "TWD67"
    else:
        # 差異很小，基於主要趨勢判斷
        if lat_diff > 0:  # 坐標1緯度較高
            system1 = "TWD67"
            system2 = "WGS84"
        else:  # 坐標1緯度較低
            system1 = "WGS84"
            system2 = "TWD67"
    
    return system1, system2

def analyze_coordinate_systems():
    """分析並辨識坐標系統"""
    
    # 查找最新的氣象站資料檔案
    output_dir = "outputs"
    csv_files = [f for f in os.listdir(output_dir) if f.startswith('weather_stations_') and f.endswith('.csv')]
    
    if not csv_files:
        print("找不到氣象站 CSV 資料檔")
        return
    
    latest_csv = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
    csv_path = os.path.join(output_dir, latest_csv)
    print(f"使用資料檔案: {csv_path}")
    
    # 讀取並分析資料
    stations = []
    system_combinations = {}
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    lat1 = float(row['latitude_1'])
                    lon1 = float(row['longitude_1'])
                    lat2 = float(row['latitude_2'])
                    lon2 = float(row['longitude_2'])
                    
                    # 辨識坐標系統
                    system1, system2 = identify_coordinate_system_by_pattern(lat1, lon1, lat2, lon2)
                    
                    # 統計組合
                    combo = f"{system1} vs {system2}"
                    system_combinations[combo] = system_combinations.get(combo, 0) + 1
                    
                    # 計算距離
                    distance = haversine_distance(lat1, lon1, lat2, lon2)
                    
                    stations.append({
                        'station_id': row['station_id'],
                        'station_name': row['station_name'],
                        'coord1': (lat1, lon1),
                        'coord2': (lat2, lon2),
                        'coord1_system': system1,
                        'coord2_system': system2,
                        'distance_meters': distance
                    })
                    
                except (ValueError, KeyError):
                    continue
                    
    except Exception as e:
        print(f"讀取檔案失敗: {e}")
        return
    
    print(f"有效雙坐標資料: {len(stations)} 筆")
    
    if not stations:
        print("沒有有效的雙坐標資料")
        return
    
    # 顯示分析結果
    print("\n" + "="*60)
    print("坐標系統辨識結果 (基於 TWD67緯度較高、經度較低 特徵)")
    print("="*60)
    
    print(f"\n坐標系統組合分布:")
    for combo, count in system_combinations.items():
        percentage = (count / len(stations)) * 100
        print(f"  {combo}: {count} 個測站 ({percentage:.1f}%)")
    
    # 顯示前10個測站的詳細資訊
    print(f"\n前10個測站的坐標系統辨識結果:")
    for i, station in enumerate(stations[:10], 1):
        lat1, lon1 = station['coord1']
        lat2, lon2 = station['coord2']
        lat_diff = lat1 - lat2
        lon_diff = lon1 - lon2
        
        print(f"  {i}. {station['station_name']}")
        print(f"     坐標1: ({lat1:.6f}, {lon1:.6f}) - {station['coord1_system']}")
        print(f"     坐標2: ({lat2:.6f}, {lon2:.6f}) - {station['coord2_system']}")
        print(f"     緯度差: {lat_diff:+.6f}, 經度差: {lon_diff:+.6f}")
        print(f"     距離: {station['distance_meters']:.2f} 公尺")
        print()
    
    # 儲存辨識結果
    save_identification_results(stations, system_combinations)
    
    # 創建標示坐標系統的地圖
    create_coordinate_system_map(stations)
    
    print("坐標系統辨識完成!")

def save_identification_results(stations, system_combinations):
    """儲存辨識結果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/coordinate_system_identification_{timestamp}.csv"
    
    try:
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as file:
            fieldnames = ['station_id', 'station_name', 
                         'coord1_system', 'coord1_lat', 'coord1_lon',
                         'coord2_system', 'coord2_lat', 'coord2_lon',
                         'lat_diff', 'lon_diff', 'distance_meters']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for station in stations:
                lat1, lon1 = station['coord1']
                lat2, lon2 = station['coord2']
                writer.writerow({
                    'station_id': station['station_id'],
                    'station_name': station['station_name'],
                    'coord1_system': station['coord1_system'],
                    'coord1_lat': lat1,
                    'coord1_lon': lon1,
                    'coord2_system': station['coord2_system'],
                    'coord2_lat': lat2,
                    'coord2_lon': lon2,
                    'lat_diff': lat1 - lat2,
                    'lon_diff': lon1 - lon2,
                    'distance_meters': station['distance_meters']
                })
        
        print(f"\n辨識結果已儲存至: {output_file}")
        
        # 儲存統計摘要
        stats_file = f"outputs/coordinate_system_stats_{timestamp}.csv"
        with open(stats_file, 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            
            writer.writerow(['坐標系統分析摘要'])
            writer.writerow(['坐標系統組合', '測站數量', '百分比', '平均距離(公尺)'])
            
            for combo, count in system_combinations.items():
                combo_stations = [s for s in stations 
                                 if f"{s['coord1_system']} vs {s['coord2_system']}" == combo]
                avg_distance = sum(s['distance_meters'] for s in combo_stations) / len(combo_stations)
                percentage = (count / len(stations)) * 100
                writer.writerow([combo, count, f"{percentage:.1f}%", f"{avg_distance:.2f}"])
        
        print(f"統計摘要已儲存至: {stats_file}")
        
    except Exception as e:
        print(f"儲存辨識結果失敗: {e}")

def create_coordinate_system_map(stations):
    """創建標示坐標系統的地圖"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = f"outputs/coordinate_system_map_{timestamp}.html"
    
    # 計算中心點
    all_lats = [s['coord1'][0] for s in stations] + [s['coord2'][0] for s in stations]
    all_lons = [s['coord1'][1] for s in stations] + [s['coord2'][1] for s in stations]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>氣象站坐標系統分析 - TWD67 vs WGS84</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        #map {{ height: 600px; width: 100%; }}
        .info {{ margin: 10px; padding: 10px; background: white; border-radius: 5px; }}
        .legend {{ margin: 10px; padding: 10px; background: white; border-radius: 5px; }}
        .twd67 {{ color: #FF4444; font-weight: bold; }}
        .wgs84 {{ color: #4444FF; font-weight: bold; }}
        .coordinate-info {{ font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <h1>氣象站坐標系統分析</h1>
    <div class="info">
        <p><strong>坐標系統辨識規則:</strong></p>
        <div class="legend">
            <p><span class="twd67">● TWD67</span> - 緯度較高、經度較低</p>
            <p><span class="wgs84">● WGS84</span> - 緯度較低、經度較高</p>
        </div>
        <p><strong>說明:</strong> 根據坐標特徵自動辨識TWD67和WGS84坐標系統</p>
    </div>
    <div id="map"></div>
    
    <script>
        var map = L.map('map').set([{center_lat}, {center_lon}], 7);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // 坐標系統圖層
        var twd67Group = L.layerGroup();
        var wgs84Group = L.layerGroup();
    """
    
    # 添加 TWD67 坐標標記
    twd67_count = 0
    for station in stations:
        if station['coord1_system'] == 'TWD67':
            lat, lon = station['coord1']
            twd67_count += 1
            html_content += f"""
        L.marker([{lat}, {lon}], {{icon: L.divIcon({{className: 'twd67-marker', html: '●', iconSize: [20, 20]}})}})
            .bindPopup('<b>{station['station_name']}</b><br><strong class="twd67">TWD67 坐標</strong><br>緯度: {lat:.6f}<br>經度: {lon:.6f}<br><span class="coordinate-info">特徵: 緯度較高、經度較低</span><br>距離: {station['distance_meters']:.1f} 公尺')
            .addTo(twd67Group);
            """
        
        if station['coord2_system'] == 'TWD67':
            lat, lon = station['coord2']
            twd67_count += 1
            html_content += f"""
        L.marker([{lat}, {lon}], {{icon: L.divIcon({{className: 'twd67-marker', html: '●', iconSize: [20, 20]}})}})
            .bindPopup('<b>{station['station_name']}</b><br><strong class="twd67">TWD67 坐標</strong><br>緯度: {lat:.6f}<br>經度: {lon:.6f}<br><span class="coordinate-info">特徵: 緯度較高、經度較低</span><br>距離: {station['distance_meters']:.1f} 公尺')
            .addTo(twd67Group);
            """
    
    # 添加 WGS84 坐標標記
    wgs84_count = 0
    for station in stations:
        if station['coord1_system'] == 'WGS84':
            lat, lon = station['coord1']
            wgs84_count += 1
            html_content += f"""
        L.marker([{lat}, {lon}], {{icon: L.divIcon({{className: 'wgs84-marker', html: '●', iconSize: [20, 20]}})}})
            .bindPopup('<b>{station['station_name']}</b><br><strong class="wgs84">WGS84 坐標</strong><br>緯度: {lat:.6f}<br>經度: {lon:.6f}<br><span class="coordinate-info">特徵: 緯度較低、經度較高</span><br>距離: {station['distance_meters']:.1f} 公尺')
            .addTo(wgs84Group);
            """
        
        if station['coord2_system'] == 'WGS84':
            lat, lon = station['coord2']
            wgs84_count += 1
            html_content += f"""
        L.marker([{lat}, {lon}], {{icon: L.divIcon({{className: 'wgs84-marker', html: '●', iconSize: [20, 20]}})}})
            .bindPopup('<b>{station['station_name']}</b><br><strong class="wgs84">WGS84 坐標</strong><br>緯度: {lat:.6f}<br>經度: {lon:.6f}<br><span class="coordinate-info">特徵: 緯度較低、經度較高</span><br>距離: {station['distance_meters']:.1f} 公尺')
            .addTo(wgs84Group);
            """
    
    # 添加連線（對於不同坐標系統的測站）
    for station in stations:
        if station['coord1_system'] != station['coord2_system']:
            lat1, lon1 = station['coord1']
            lat2, lon2 = station['coord2']
            html_content += f"""
        L.polyline([[{lat1}, {lon1}], [{lat2}, {lon2}]], {{color: 'orange', weight: 2, opacity: 0.6, dashArray: '5, 5'}})
            .bindPopup('<b>{station['station_name']}</b><br>坐標系統差異<br>{station['coord1_system']} vs {station['coord2_system']}<br>距離: {station['distance_meters']:.1f} 公尺')
            .addTo(map);
            """
    
    html_content += f"""
        // 添加圖層到地圖
        twd67Group.addTo(map);
        wgs84Group.addTo(map);
        
        // 圖層控制
        var overlayMaps = {{
            'TWD67 坐標 ({twd67_count}個)': twd67Group,
            'WGS84 坐標 ({wgs84_count}個)': wgs84Group
        }};
        
        L.control.layers(null, overlayMaps).addTo(map);
        
        // 自定義圖標樣式
        var style = document.createElement('style');
        style.innerHTML = `
            .twd67-marker {{ 
                color: #FF4444; 
                font-size: 16px; 
                text-shadow: 0 0 3px white;
            }}
            .wgs84-marker {{ 
                color: #4444FF; 
                font-size: 16px; 
                text-shadow: 0 0 3px white;
            }}
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
    """
    
    # 儲存 HTML 檔案
    with open(html_file, 'w', encoding='utf-8') as file:
        file.write(html_content)
    
    print(f"坐標系統地圖已儲存至: {html_file}")

def haversine_distance(lat1, lon1, lat2, lon2):
    """計算兩點間的大圓距離（公尺）"""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000
    return c * r

if __name__ == "__main__":
    analyze_coordinate_systems()
