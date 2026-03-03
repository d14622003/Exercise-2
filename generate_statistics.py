import pandas as pd
import math
import os
from datetime import datetime

def generate_statistics():
    """生成測站差距統計"""
    
    # 查找最新的分析結果檔案
    output_dir = "outputs"
    analysis_files = [f for f in os.listdir(output_dir) if f.startswith('twd67_wgs84_analysis_') and f.endswith('.csv')]
    
    if not analysis_files:
        print("找不到 TWD67 vs WGS84 分析結果檔案")
        return
    
    latest_file = max(analysis_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
    file_path = os.path.join(output_dir, latest_file)
    print(f"讀取分析結果檔案: {file_path}")
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        print(f"成功讀取 {len(df)} 筆測站資料")
        
        # 計算統計
        distances = df['distance_meters']
        
        statistics = {
            'total_stations': len(df),
            'mean_distance': distances.mean(),
            'median_distance': distances.median(),
            'min_distance': distances.min(),
            'max_distance': distances.max(),
            'std_distance': distances.std()
        }
        
        # 分類統計
        categories = {
            'very_small': distances < 100,  # < 100公尺
            'small': (distances >= 100) & (distances < 500),  # 100-500公尺
            'medium': (distances >= 500) & (distances < 1000),  # 500-1000公尺
            'large': (distances >= 1000) & (distances < 5000),  # 1-5公里
            'very_large': distances >= 5000  # > 5公里
        }
        
        # 生成統計檔案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = f"outputs/station_distance_statistics_{timestamp}.csv"
        
        with open(stats_file, 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)
            
            # 基本統計
            writer.writerow(['=== 基本統計 ==='])
            writer.writerow(['統計項目', '數值'])
            writer.writerow(['總測站數', statistics['total_stations']])
            writer.writerow(['平均距離(公尺)', f"{statistics['mean_distance']:.2f}"])
            writer.writerow(['中位數距離(公尺)', f"{statistics['median_distance']:.2f}"])
            writer.writerow(['最小距離(公尺)', f"{statistics['min_distance']:.2f}"])
            writer.writerow(['最大距離(公尺)', f"{statistics['max_distance']:.2f}"])
            writer.writerow(['標準差(公尺)', f"{statistics['std_distance']:.2f}"])
            writer.writerow([])
            
            # 分類統計
            writer.writerow(['=== 距離分類統計 ==='])
            writer.writerow(['距離分類', '測站數量', '百分比'])
            category_names = {
                'very_small': '< 100公尺',
                'small': '100-500公尺',
                'medium': '500-1000公尺',
                'large': '1-5公里',
                'very_large': '> 5公里'
            }
            for category, condition in categories.items():
                count = condition.sum()
                percentage = (count / len(df)) * 100
                writer.writerow([category_names[category], count, f"{percentage:.1f}%"])
            writer.writerow([])
            
            # 分位數
            writer.writerow(['=== 距離分位數 ==='])
            writer.writerow(['分位數', '距離(公尺)'])
            percentiles = [25, 50, 75, 90, 95, 99]
            for p in percentiles:
                writer.writerow([f'{p}%', f"{distances.quantile(p/100):.2f}"])
            writer.writerow([])
            
            # 坐標系統組合
            writer.writerow(['=== 坐標系統組合統計 ==='])
            writer.writerow(['組合', '測站數量', '百分比'])
            combo_counts = df['coordinate_combination'].value_counts()
            for combo, count in combo_counts.items():
                percentage = (count / len(df)) * 100
                writer.writerow([combo, count, f"{percentage:.1f}%"])
            writer.writerow([])
            
            # 差距最大的前10個測站
            writer.writerow(['=== 差距最大的前10個測站 ==='])
            writer.writerow(['排名', '測站名稱', '坐標系統組合', '距離(公尺)', '距離(公里)'])
            top_10 = df.nlargest(10, 'distance_meters')
            for i, (idx, row) in enumerate(top_10.iterrows(), 1):
                writer.writerow([
                    i, 
                    row['station_name'], 
                    row['coordinate_combination'],
                    f"{row['distance_meters']:.2f}",
                    f"{row['distance_km']:.3f}"
                ])
            writer.writerow([])
            
            # 差距最小的前10個測站
            writer.writerow(['=== 差距最小的前10個測站 ==='])
            writer.writerow(['排名', '測站名稱', '坐標系統組合', '距離(公尺)', '距離(公里)'])
            small_10 = df.nsmallest(10, 'distance_meters')
            for i, (idx, row) in enumerate(small_10.iterrows(), 1):
                writer.writerow([
                    i, 
                    row['station_name'], 
                    row['coordinate_combination'],
                    f"{row['distance_meters']:.2f}",
                    f"{row['distance_km']:.3f}"
                ])
        
        print(f"測站差距統計結果已儲存至: {stats_file}")
        
        # 顯示統計摘要
        print(f"\n=== 測站差距統計摘要 ===")
        print(f"總測站數: {statistics['total_stations']}")
        print(f"平均距離: {statistics['mean_distance']:.2f} 公尺")
        print(f"中位數距離: {statistics['median_distance']:.2f} 公尺")
        print(f"最小距離: {statistics['min_distance']:.2f} 公尺")
        print(f"最大距離: {statistics['max_distance']:.2f} 公尺")
        
        print(f"\n距離分類:")
        for category, condition in categories.items():
            count = condition.sum()
            percentage = (count / len(df)) * 100
            print(f"  {category_names[category]}: {count} 個測站 ({percentage:.1f}%)")
        
        return stats_file
        
    except Exception as e:
        print(f"生成統計結果失敗: {e}")
        return None

if __name__ == "__main__":
    import csv
    generate_statistics()
