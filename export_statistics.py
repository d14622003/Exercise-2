import csv
import math
import os
from datetime import datetime

def export_statistics_to_csv():
    """匯出統計結果到 CSV 檔案"""
    
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
    
    # 生成統計檔案
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats_file = f"outputs/coordinate_statistics_{timestamp}.csv"
    
    try:
        with open(stats_file, 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            
            # 基本統計
            writer.writerow(['統計項目', '數值', '單位'])
            writer.writerow(['測站總數', len(stations), '個'])
            writer.writerow(['平均距離', sum(distances)/len(distances), '公尺'])
            writer.writerow(['中位數距離', sorted(distances)[len(distances)//2], '公尺'])
            writer.writerow(['最小距離', min(distances), '公尺'])
            writer.writerow(['最大距離', max(distances), '公尺'])
            
            # 計算標準差
            mean_dist = sum(distances) / len(distances)
            variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances)
            std_dev = math.sqrt(variance)
            writer.writerow(['標準差', std_dev, '公尺'])
            
            writer.writerow([])  # 空行
            
            # 分位數
            writer.writerow(['分位數', '距離', '單位'])
            sorted_distances = sorted(distances)
            n = len(sorted_distances)
            percentiles = [25, 50, 75, 90, 95, 99]
            for p in percentiles:
                idx = int((p / 100) * n)
                if idx >= n:
                    idx = n - 1
                writer.writerow([f'{p}%', sorted_distances[idx], '公尺'])
            
            writer.writerow([])  # 空行
            
            # 分類統計
            writer.writerow(['距離分類', '測站數量', '百分比'])
            categories = [
                ('< 100公尺', 0, 100),
                ('100-500公尺', 100, 500),
                ('500-1000公尺', 500, 1000),
                ('1-5公里', 1000, 5000),
                ('> 5公里', 5000, float('inf'))
            ]
            
            for category, min_dist, max_dist in categories:
                if max_dist == float('inf'):
                    count = sum(1 for d in distances if d >= min_dist)
                else:
                    count = sum(1 for d in distances if min_dist <= d < max_dist)
                percentage = (count / len(stations)) * 100
                writer.writerow([category, count, f'{percentage:.1f}%'])
            
            writer.writerow([])  # 空行
            
            # 差距最大的前10個測站
            writer.writerow(['差距最大的前10個測站'])
            writer.writerow(['排名', '測站名稱', '距離(公尺)', '距離(公里)'])
            stations_sorted = sorted(stations, key=lambda x: x['distance_meters'], reverse=True)
            for i, station in enumerate(stations_sorted[:10], 1):
                writer.writerow([i, station['station_name'], 
                               f"{station['distance_meters']:.2f}", 
                               f"{station['distance_km']:.3f}"])
            
            writer.writerow([])  # 空行
            
            # 差距最小的前10個測站
            writer.writerow(['差距最小的前10個測站'])
            writer.writerow(['排名', '測站名稱', '距離(公尺)', '距離(公里)'])
            for i, station in enumerate(stations_sorted[-10:], 1):
                writer.writerow([i, station['station_name'], 
                               f"{station['distance_meters']:.2f}", 
                               f"{station['distance_km']:.3f}"])
            
            writer.writerow([])  # 空行
            
            # 坐標系統資訊
            coord1_names = set(s['coord1_name'] for s in stations)
            coord2_names = set(s['coord2_name'] for s in stations)
            writer.writerow(['坐標系統資訊'])
            writer.writerow(['坐標系統1', list(coord1_names)[0] if coord1_names else '未知'])
            writer.writerow(['坐標系統2', list(coord2_names)[0] if coord2_names else '未知'])
        
        print(f"\n統計結果已匯出至: {stats_file}")
        
        # 顯示基本統計
        print("\n基本統計摘要:")
        print(f"  測站總數: {len(stations)}")
        print(f"  平均距離: {sum(distances)/len(distances):.2f} 公尺")
        print(f"  最小距離: {min(distances):.2f} 公尺")
        print(f"  最大距離: {max(distances):.2f} 公尺")
        
    except Exception as e:
        print(f"匯出統計結果失敗: {e}")

if __name__ == "__main__":
    export_statistics_to_csv()
