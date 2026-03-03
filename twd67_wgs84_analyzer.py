#!/usr/bin/env python3
"""
氣象站坐標系統分析腳本 (完整版)
在讀取資料時就判斷坐標系統，直接顯示 TWD67/WGS84
"""

import pandas as pd
import folium
from folium.plugins import MarkerCluster
import math
import os
from datetime import datetime

class CoordinateSystemAnalyzer:
    def __init__(self):
        pass
    
    def identify_coordinate_system_at_read(self, lat1, lon1, lat2, lon2):
        """
        在讀取資料時就判斷坐標系統
        TWD67特徵：緯度較高、經度較低
        WGS84特徵：緯度較低、經度較高
        """
        
        lat_diff = lat1 - lat2
        lon_diff = lon1 - lon2
        
        if lat_diff > 0.0001 and lon_diff < -0.0001:
            # 坐標1緯度較高、經度較低
            return "TWD67", "WGS84"
        elif lat_diff < -0.0001 and lon_diff > 0.0001:
            # 坐標1緯度較低、經度較高
            return "WGS84", "TWD67"
        else:
            # 差異很小，基於主要趨勢判斷
            if lat_diff > 0:  # 坐標1緯度較高
                return "TWD67", "WGS84"
            else:  # 坐標1緯度較低
                return "WGS84", "TWD67"
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間的大圓距離（公尺）"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000
        return c * r
    
    def load_and_analyze_data(self, csv_file):
        """載入並分析氣象站坐標資料"""
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            print(f"成功讀取 {len(df)} 筆測站資料")
        except Exception as e:
            print(f"讀取 CSV 檔案失敗: {e}")
            return None, None
        
        # 過濾有效坐標資料
        valid_df = df.dropna(subset=['latitude_1', 'longitude_1', 'latitude_2', 'longitude_2'])
        print(f"有效雙坐標資料: {len(valid_df)} 筆")
        
        if len(valid_df) == 0:
            print("沒有有效的雙坐標資料")
            return None, None
        
        # 計算距離並在讀取時就判斷坐標系統
        distances = []
        for idx, row in valid_df.iterrows():
            lat1 = row['latitude_1']
            lon1 = row['longitude_1']
            lat2 = row['latitude_2']
            lon2 = row['longitude_2']
            
            # 在讀取時就判斷坐標系統
            coord1_system, coord2_system = self.identify_coordinate_system_at_read(lat1, lon1, lat2, lon2)
            
            distance = self.haversine_distance(lat1, lon1, lat2, lon2)
            
            distances.append({
                'station_id': row['station_id'],
                'station_name': row['station_name'],
                'coord1': (lat1, lon1),
                'coord2': (lat2, lon2),
                'coord1_system': coord1_system,  # 直接使用辨識結果
                'coord2_system': coord2_system,  # 直接使用辨識結果
                'distance_meters': distance,
                'distance_km': distance / 1000
            })
        
        distance_df = pd.DataFrame(distances)
        return valid_df, distance_df
    
    def print_statistics(self, distance_df):
        """印出距離統計資料"""
        print("\n" + "="*60)
        print("氣象站坐標差距統計分析 (TWD67 vs WGS84)")
        print("="*60)
        
        distances = distance_df['distance_meters']
        
        print(f"\n基本統計:")
        print(f"  測站總數: {len(distance_df)}")
        print(f"  平均距離: {distances.mean():.2f} 公尺")
        print(f"  中位數距離: {distances.median():.2f} 公尺")
        print(f"  最小距離: {distances.min():.2f} 公尺")
        print(f"  最大距離: {distances.max():.2f} 公尺")
        print(f"  標準差: {distances.std():.2f} 公尺")
        
        # 分位數
        print(f"\n距離分位數:")
        percentiles = [25, 50, 75, 90, 95, 99]
        for p in percentiles:
            print(f"  {p}%: {distances.quantile(p/100):.2f} 公尺")
        
        # 分類統計
        categories = [
            ('< 100公尺', distance_df['distance_meters'] < 100),
            ('100-500公尺', (distance_df['distance_meters'] >= 100) & (distance_df['distance_meters'] < 500)),
            ('500-1000公尺', (distance_df['distance_meters'] >= 500) & (distance_df['distance_meters'] < 1000)),
            ('1-5公里', (distance_df['distance_meters'] >= 1000) & (distance_df['distance_meters'] < 5000)),
            ('> 5公里', distance_df['distance_meters'] >= 5000)
        ]
        
        print(f"\n距離分類:")
        for category, condition in categories:
            count = condition.sum()
            percentage = (count / len(distance_df)) * 100
            print(f"  {category}: {count} 個測站 ({percentage:.1f}%)")
        
        # 坐標系統統計
        print(f"\n坐標系統分布:")
        coord1_counts = distance_df['coord1_system'].value_counts()
        coord2_counts = distance_df['coord2_system'].value_counts()
        
        print("  坐標系1分布:")
        for system, count in coord1_counts.items():
            print(f"    {system}: {count} 個測站 ({count/len(distance_df)*100:.1f}%)")
        
        print("  坐標系2分布:")
        for system, count in coord2_counts.items():
            print(f"    {system}: {count} 個測站 ({count/len(distance_df)*100:.1f}%)")
        
        # 差距最大的前10個測站
        print(f"\n差距最大的前10個測站:")
        top_10 = distance_df.nlargest(10, 'distance_meters')
        for idx, row in top_10.iterrows():
            print(f"  {row['station_name']}: {row['distance_meters']:.2f} 公尺 ({row['distance_km']:.3f} 公里)")
            print(f"    {row['coord1_system']} vs {row['coord2_system']}")
        
        # 差距最小的前10個測站
        print(f"\n差距最小的前10個測站:")
        small_10 = distance_df.nsmallest(10, 'distance_meters')
        for idx, row in small_10.iterrows():
            print(f"  {row['station_name']}: {row['distance_meters']:.2f} 公尺")
            print(f"    {row['coord1_system']} vs {row['coord2_system']}")
    
    def create_coordinate_system_map(self, df, distance_df, output_file=None):
        """建立 TWD67 vs WGS84 坐標系統地圖"""
        # 計算地圖中心點
        all_lats = list(df['latitude_1']) + list(df['latitude_2'])
        all_lons = list(df['longitude_1']) + list(df['longitude_2'])
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
        
        # 建立地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 建立坐標系統標記群組
        twd67_cluster = MarkerCluster(name='TWD67 坐標').add_to(m)
        wgs84_cluster = MarkerCluster(name='WGS84 坐標').add_to(m)
        
        # 統計各坐標系統數量
        twd67_count = 0
        wgs84_count = 0
        
        # 加入坐標系統1標記
        for idx, row in distance_df.iterrows():
            lat, lon = row['coord1']
            system = row['coord1_system']
            
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{row['station_name']}</h4>
                <p style="margin: 5px 0;"><strong>坐標系統:</strong> {system}</p>
                <p style="margin: 5px 0;">緯度: {lat:.6f}</p>
                <p style="margin: 5px 0;">經度: {lon:.6f}</p>
                <p style="margin: 5px 0;">距離: {row['distance_meters']:.1f} 公尺</p>
            </div>
            """
            
            if system == 'TWD67':
                color = 'red'
                twd67_count += 1
            else:
                color = 'blue'
                wgs84_count += 1
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(twd67_cluster if system == 'TWD67' else wgs84_cluster)
        
        # 加入坐標系統2標記
        for idx, row in distance_df.iterrows():
            lat, lon = row['coord2']
            system = row['coord2_system']
            
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{row['station_name']}</h4>
                <p style="margin: 5px 0;"><strong>坐標系統:</strong> {system}</p>
                <p style="margin: 5px 0;">緯度: {lat:.6f}</p>
                <p style="margin: 5px 0;">經度: {lon:.6f}</p>
                <p style="margin: 5px 0;">距離: {row['distance_meters']:.1f} 公尺</p>
            </div>
            """
            
            if system == 'TWD67':
                color = 'red'
                twd67_count += 1
            else:
                color = 'blue'
                wgs84_count += 1
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(twd67_cluster if system == 'TWD67' else wgs84_cluster)
        
        # 為不同坐標系統的測站連線
        for idx, row in distance_df.iterrows():
            if row['coord1_system'] != row['coord2_system']:
                folium.PolyLine(
                    locations=[[row['coord1'][0], row['coord1'][1]], 
                              [row['coord2'][0], row['coord2'][1]]],
                    color='orange',
                    weight=2,
                    opacity=0.6,
                    popup=f"坐標系統差異: {row['coord1_system']} vs {row['coord2_system']}<br>距離: {row['distance_meters']:.1f} 公尺"
                ).add_to(m)
        
        # 加入圖例
        legend_html = f'''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4 style="margin: 0 0 10px 0;">TWD67 vs WGS84</h4>
        <p style="margin: 5px 0;"><i class="fa fa-info-circle" style="color:red"></i> TWD67 ({twd67_count}個)</p>
        <p style="margin: 5px 0;"><i class="fa fa-info-circle" style="color:blue"></i> WGS84 ({wgs84_count}個)</p>
        <p style="margin: 5px 0;"><span style="color:orange;">━━━</span> 坐標系統差異</p>
        <p style="margin: 5px 0; font-size: 12px;">(不同坐標系統間的連線)</p>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 加入圖層控制
        folium.LayerControl().add_to(m)
        
        # 儲存地圖
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/twd67_wgs84_map_{timestamp}.html"
        
        m.save(output_file)
        print(f"TWD67 vs WGS84 地圖已儲存至: {output_file}")
        
        return output_file
    
    def save_analysis_results(self, distance_df, output_file=None):
        """儲存分析結果"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/twd67_wgs84_analysis_{timestamp}.csv"
        
        # 重新組織資料以便儲存
        save_data = []
        for idx, row in distance_df.iterrows():
            save_data.append({
                'station_id': row['station_id'],
                'station_name': row['station_name'],
                'twd67_lat': row['coord1'][0] if row['coord1_system'] == 'TWD67' else row['coord2'][0],
                'twd67_lon': row['coord1'][1] if row['coord1_system'] == 'TWD67' else row['coord2'][1],
                'wgs84_lat': row['coord1'][0] if row['coord1_system'] == 'WGS84' else row['coord2'][0],
                'wgs84_lon': row['coord1'][1] if row['coord1_system'] == 'WGS84' else row['coord2'][1],
                'distance_meters': row['distance_meters'],
                'distance_km': row['distance_km'],
                'coordinate_combination': f"{row['coord1_system']} vs {row['coord2_system']}"
            })
        
        save_df = pd.DataFrame(save_data)
        save_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"TWD67 vs WGS84 分析結果已儲存至: {output_file}")
        
        # 生成統計結果
        stats_file = self.generate_station_statistics(distance_df)
        
        return output_file, stats_file
    
    def generate_station_statistics(self, distance_df):
        """生成每個測站的差距統計"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats_file = f"outputs/station_distance_statistics_{timestamp}.csv"
        
        # 計算基本統計
        distances = distance_df['distance_meters']
        
        statistics = {
            'total_stations': len(distance_df),
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
        
        category_counts = {}
        for category, condition in categories.items():
            count = condition.sum()
            category_counts[category] = {
                'count': count,
                'percentage': (count / len(distance_df)) * 100
            }
        
        # 坐標系統組合統計
        combo_counts = distance_df['coordinate_combination'].value_counts()
        
        # 分位數
        percentiles = {}
        for p in [25, 50, 75, 90, 95, 99]:
            percentiles[f'p{p}'] = distances.quantile(p/100)
        
        try:
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
                for category, data in category_counts.items():
                    writer.writerow([
                        category_names[category], 
                        data['count'], 
                        f"{data['percentage']:.1f}%"
                    ])
                writer.writerow([])
                
                # 分位數
                writer.writerow(['=== 距離分位數 ==='])
                writer.writerow(['分位數', '距離(公尺)'])
                for p, value in percentiles.items():
                    writer.writerow([f'{p[1:]}%', f"{value:.2f}"])
                writer.writerow([])
                
                # 坐標系統組合
                writer.writerow(['=== 坐標系統組合統計 ==='])
                writer.writerow(['組合', '測站數量', '百分比'])
                for combo, count in combo_counts.items():
                    percentage = (count / len(distance_df)) * 100
                    writer.writerow([combo, count, f"{percentage:.1f}%"])
                writer.writerow([])
                
                # 差距最大的前10個測站
                writer.writerow(['=== 差距最大的前10個測站 ==='])
                writer.writerow(['排名', '測站名稱', '坐標系統組合', '距離(公尺)', '距離(公里)'])
                top_10 = distance_df.nlargest(10, 'distance_meters')
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
                small_10 = distance_df.nsmallest(10, 'distance_meters')
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
            for category, data in category_counts.items():
                print(f"  {category_names[category]}: {data['count']} 個測站 ({data['percentage']:.1f}%)")
            
        except Exception as e:
            print(f"生成統計結果失敗: {e}")
            return None
        
        return stats_file

def main():
    """主程式"""
    # 查找最新的 CSV 檔案
    output_dir = "outputs"
    csv_files = [f for f in os.listdir(output_dir) if f.startswith('weather_stations_') and f.endswith('.csv')]
    
    if not csv_files:
        print("找不到氣象站 CSV 資料檔，請先執行 cwa_weather_api.py")
        return
    
    # 使用最新的檔案
    latest_csv = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
    csv_path = os.path.join(output_dir, latest_csv)
    print(f"使用資料檔案: {csv_path}")
    
    # 建立分析器
    analyzer = CoordinateSystemAnalyzer()
    
    # 載入並分析資料
    print("\n正在載入並分析資料...")
    df, distance_df = analyzer.load_and_analyze_data(csv_path)
    
    if df is None or distance_df is None:
        print("資料分析失敗")
        return
    
    # 印出統計資料
    analyzer.print_statistics(distance_df)
    
    # 建立地圖
    print("\n正在建立 TWD67 vs WGS84 地圖...")
    map_file = analyzer.create_coordinate_system_map(df, distance_df)
    
    # 儲存分析結果
    results_file = analyzer.save_analysis_results(distance_df)
    
    print(f"\n=== TWD67 vs WGS84 分析完成 ===")
    print(f"地圖檔案: {map_file}")
    print(f"分析結果: {results_file}")
    print("\n可以在瀏覽器中開啟 HTML 檔案查看地圖")

if __name__ == "__main__":
    main()
