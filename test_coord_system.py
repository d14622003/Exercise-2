import csv
import math
import os

def identify_coordinate_system(lat1, lon1, lat2, lon2):
    """
    根據特徵辨識坐標系統
    TWD67特徵：緯度較高、經度較低
    WGS84特徵：緯度較低、經度較高
    """
    
    lat_diff = lat1 - lat2
    lon_diff = lon1 - lon2
    
    print(f"坐標1: ({lat1:.6f}, {lon1:.6f})")
    print(f"坐標2: ({lat2:.6f}, {lon2:.6f})")
    print(f"緯度差: {lat_diff:+.6f}, 經度差: {lon_diff:+.6f}")
    
    if lat_diff > 0.0001 and lon_diff < -0.0001:
        # 坐標1緯度較高、經度較低
        system1 = "TWD67"
        system2 = "WGS84"
        print(f"結果: 坐標1是TWD67, 坐標2是WGS84")
    elif lat_diff < -0.0001 and lon_diff > 0.0001:
        # 坐標1緯度較低、經度較高
        system1 = "WGS84"
        system2 = "TWD67"
        print(f"結果: 坐標1是WGS84, 坐標2是TWD67")
    else:
        # 差異很小，基於主要趨勢判斷
        if lat_diff > 0:  # 坐標1緯度較高
            system1 = "TWD67"
            system2 = "WGS84"
            print(f"結果: 坐標1緯度較高，判斷為TWD67")
        else:  # 坐標1緯度較低
            system1 = "WGS84"
            system2 = "TWD67"
            print(f"結果: 坐標1緯度較低，判斷為WGS84")
    
    return system1, system2

def test_coordinate_identification():
    """測試坐標系統辨識"""
    
    # 查找氣象站資料檔案
    output_dir = "outputs"
    csv_files = [f for f in os.listdir(output_dir) if f.startswith('weather_stations_') and f.endswith('.csv')]
    
    if not csv_files:
        print("找不到氣象站 CSV 資料檔")
        return
    
    latest_csv = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
    csv_path = os.path.join(output_dir, latest_csv)
    print(f"使用資料檔案: {csv_path}")
    
    # 讀取前5筆資料進行測試
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            count = 0
            for row in reader:
                if count >= 5:  # 只測試前5筆
                    break
                    
                try:
                    lat1 = float(row['latitude_1'])
                    lon1 = float(row['longitude_1'])
                    lat2 = float(row['latitude_2'])
                    lon2 = float(row['longitude_2'])
                    
                    print(f"\n=== 測站 {count+1}: {row['station_name']} ===")
                    system1, system2 = identify_coordinate_system(lat1, lon1, lat2, lon2)
                    
                    # 計算距離
                    distance = haversine_distance(lat1, lon1, lat2, lon2)
                    print(f"距離: {distance:.2f} 公尺")
                    print(f"辨識結果: {system1} vs {system2}")
                    print("-" * 50)
                    
                    count += 1
                    
                except (ValueError, KeyError) as e:
                    print(f"跳過無效資料: {e}")
                    continue
                    
    except Exception as e:
        print(f"讀取檔案失敗: {e}")
        return

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
    print("開始測試坐標系統辨識...")
    print("辨識規則: TWD67緯度較高、經度較低")
    print("=" * 60)
    test_coordinate_identification()
    print("\n測試完成!")
