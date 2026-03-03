import csv
import math
import os

def show_analysis_summary():
    """顯示分析結果摘要"""
    
    # 查找最新的分析結果檔案
    output_dir = "outputs"
    analysis_files = [f for f in os.listdir(output_dir) if f.startswith('coordinate_distance_analysis_') and f.endswith('.csv')]
    
    if not analysis_files:
        print("找不到分析結果檔案")
        return
    
    latest_file = max(analysis_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
    file_path = os.path.join(output_dir, latest_file)
    print(f"讀取分析結果檔案: {file_path}")
    
    # 讀取分析結果
    stations = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['distance_meters']:  # 確保有距離資料
                    stations.append({
                        'station_name': row['station_name'],
                        'coord1_name': row['coord1_name'],
                        'coord2_name': row['coord2_name'],
                        'distance_meters': float(row['distance_meters']),
                        'distance_km': float(row['distance_km'])
                    })
    except Exception as e:
        print(f"讀取檔案失敗: {e}")
        return
    
    if not stations:
        print("沒有有效的分析資料")
        return
    
    # 計算統計資料
    distances = [s['distance_meters'] for s in stations]
    
    print("\n" + "="*60)
    print("氣象站坐標差距統計分析")
    print("="*60)
    
    print(f"\n基本統計:")
    print(f"  測站總數: {len(stations)}")
    print(f"  平均距離: {sum(distances)/len(distances):.2f} 公尺")
    print(f"  中位數距離: {sorted(distances)[len(distances)//2]:.2f} 公尺")
    print(f"  最小距離: {min(distances):.2f} 公尺")
    print(f"  最大距離: {max(distances):.2f} 公尺")
    
    # 計算標準差
    mean_dist = sum(distances) / len(distances)
    variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
    std_dev = math.sqrt(variance)
    print(f"  標準差: {std_dev:.2f} 公尺")
    
    # 分位數
    sorted_distances = sorted(distances)
    n = len(sorted_distances)
    percentiles = [25, 50, 75, 90, 95, 99]
    print(f"\n距離分位數:")
    for p in percentiles:
        idx = int((p / 100) * n)
        if idx >= n:
            idx = n - 1
        print(f"  {p}%: {sorted_distances[idx]:.2f} 公尺")
    
    # 分類統計
    categories = [
        ('< 100公尺', 0, 100),
        ('100-500公尺', 100, 500),
        ('500-1000公尺', 500, 1000),
        ('1-5公里', 1000, 5000),
        ('> 5公里', 5000, float('inf'))
    ]
    
    print(f"\n距離分類:")
    for category, min_dist, max_dist in categories:
        if max_dist == float('inf'):
            count = sum(1 for d in distances if d >= min_dist)
        else:
            count = sum(1 for d in distances if min_dist <= d < max_dist)
        percentage = (count / len(stations)) * 100
        print(f"  {category}: {count} 個測站 ({percentage:.1f}%)")
    
    # 按距離排序
    stations.sort(key=lambda x: x['distance_meters'], reverse=True)
    
    print(f"\n差距最大的前10個測站:")
    for i, station in enumerate(stations[:10], 1):
        print(f"  {i}. {station['station_name']}: {station['distance_meters']:.2f} 公尺 ({station['distance_km']:.3f} 公里)")
    
    print(f"\n差距最小的前10個測站:")
    for i, station in enumerate(stations[-10:], 1):
        print(f"  {i}. {station['station_name']}: {station['distance_meters']:.2f} 公尺")
    
    # 檢查坐標系統名稱
    coord1_names = set(s['coord1_name'] for s in stations)
    coord2_names = set(s['coord2_name'] for s in stations)
    
    print(f"\n坐標系統名稱:")
    print(f"  坐標系1: {coord1_names}")
    print(f"  坐標系2: {coord2_names}")
    
    # 檢查地圖檔案
    map_files = [f for f in os.listdir(output_dir) if f.startswith('dual_coordinate_map_') and f.endswith('.html')]
    if map_files:
        latest_map = max(map_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
        print(f"\n互動式地圖檔案: outputs/{latest_map}")
        print("可以在瀏覽器中開啟此檔案查看雙坐標系統地圖")
    
    print("\n分析完成!")

if __name__ == "__main__":
    show_analysis_summary()
