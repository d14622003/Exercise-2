#!/usr/bin/env python3
"""
氣象站雙坐標系統分析腳本
分析每個測站的兩組坐標，並在地圖上顯示差異
"""

import pandas as pd
import folium
from folium.plugins import MarkerCluster
import math
import os
from datetime import datetime

class DualCoordinateAnalyzer:
    def __init__(self):
        pass
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間的大圓距離（公尺）"""
        # 將十進制度轉換為弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine 公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公尺）
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
        
        # 計算距離
        distances = []
        for idx, row in valid_df.iterrows():
            distance = self.haversine_distance(
                row['latitude_1'], row['longitude_1'],
                row['latitude_2'], row['longitude_2']
            )
            
            distances.append({
                'station_id': row['station_id'],
                'station_name': row['station_name'],
                'coord1': (row['latitude_1'], row['longitude_1']),
                'coord2': (row['latitude_2'], row['longitude_2']),
                'coord1_name': row.get('coord1_name', '坐標系1'),
                'coord2_name': row.get('coord2_name', '坐標系2'),
                'distance_meters': distance,
                'distance_km': distance / 1000
            })
        
        distance_df = pd.DataFrame(distances)
        return valid_df, distance_df
    
    def print_statistics(self, distance_df):
        """印出距離統計資料"""
        print("\n" + "="*60)
        print("氣象站坐標差距統計分析")
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
        
        # 差距最大的前10個測站
        print(f"\n差距最大的前10個測站:")
        top_10 = distance_df.nlargest(10, 'distance_meters')
        for idx, row in top_10.iterrows():
            print(f"  {row['station_name']}: {row['distance_meters']:.2f} 公尺 ({row['distance_km']:.3f} 公里)")
        
        # 差距最小的前10個測站（排除零距離）
        print(f"\n差距最小的前10個測站:")
        small_diff = distance_df[distance_df['distance_meters'] > 0].nsmallest(10, 'distance_meters')
        for idx, row in small_diff.iterrows():
            print(f"  {row['station_name']}: {row['distance_meters']:.2f} 公尺")
    
    def create_dual_coordinate_map(self, df, distance_df, output_file=None):
        """建立雙坐標系統地圖"""
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
        
        # 建立兩個標記群組
        coord1_cluster = MarkerCluster(name='坐標系1').add_to(m)
        coord2_cluster = MarkerCluster(name='坐標系2').add_to(m)
        
        # 加入坐標系1的標記（藍色）
        for idx, row in df.iterrows():
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{row['station_name']}</h4>
                <p style="margin: 5px 0;"><strong>坐標系1</strong></p>
                <p style="margin: 5px 0;">緯度: {row['latitude_1']:.6f}</p>
                <p style="margin: 5px 0;">經度: {row['longitude_1']:.6f}</p>
                <p style="margin: 5px 0;">系統名稱: {row.get('coord1_name', '坐標系1')}</p>
            </div>
            """
            
            folium.Marker(
                location=[row['latitude_1'], row['longitude_1']],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(coord1_cluster)
        
        # 加入坐標系2的標記（紅色）
        for idx, row in df.iterrows():
            popup_content = f"""
            <div style="font-family: Arial, sans-serif; width: 250px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">{row['station_name']}</h4>
                <p style="margin: 5px 0;"><strong>坐標系2</strong></p>
                <p style="margin: 5px 0;">緯度: {row['latitude_2']:.6f}</p>
                <p style="margin: 5px 0;">經度: {row['longitude_2']:.6f}</p>
                <p style="margin: 5px 0;">系統名稱: {row.get('coord2_name', '坐標系2')}</p>
            </div>
            """
            
            folium.Marker(
                location=[row['latitude_2'], row['longitude_2']],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(coord2_cluster)
        
        # 為差距較大的測站連線
        for idx, row in distance_df.iterrows():
            if row['distance_meters'] > 1000:  # 只顯示差距大於1公里的連線
                folium.PolyLine(
                    locations=[[row['coord1'][0], row['coord1'][1]], 
                              [row['coord2'][0], row['coord2'][1]]],
                    color='orange',
                    weight=2,
                    opacity=0.6,
                    popup=f"距離: {row['distance_meters']:.1f} 公尺"
                ).add_to(m)
        
        # 加入圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 150px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4 style="margin: 0 0 10px 0;">圖例</h4>
        <p style="margin: 5px 0;"><i class="fa fa-info-circle" style="color:blue"></i> 坐標系1</p>
        <p style="margin: 5px 0;"><i class="fa fa-info-circle" style="color:red"></i> 坐標系2</p>
        <p style="margin: 5px 0;"><span style="color:orange;">━━━</span> 大差距連線</p>
        <p style="margin: 5px 0; font-size: 12px;">(>1公里)</p>
        </div>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 加入圖層控制
        folium.LayerControl().add_to(m)
        
        # 儲存地圖
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/dual_coordinate_map_{timestamp}.html"
        
        m.save(output_file)
        print(f"雙坐標地圖已儲存至: {output_file}")
        
        return output_file
    
    def save_analysis_results(self, distance_df, output_file=None):
        """儲存分析結果"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/coordinate_distance_analysis_{timestamp}.csv"
        
        # 重新組織資料以便儲存
        save_data = []
        for idx, row in distance_df.iterrows():
            save_data.append({
                'station_id': row['station_id'],
                'station_name': row['station_name'],
                'coord1_name': row['coord1_name'],
                'coord2_name': row['coord2_name'],
                'latitude_1': row['coord1'][0],
                'longitude_1': row['coord1'][1],
                'latitude_2': row['coord2'][0],
                'longitude_2': row['coord2'][1],
                'distance_meters': row['distance_meters'],
                'distance_km': row['distance_km']
            })
        
        save_df = pd.DataFrame(save_data)
        save_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"分析結果已儲存至: {output_file}")
        
        return output_file

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
    analyzer = DualCoordinateAnalyzer()
    
    # 載入並分析資料
    print("\n正在載入並分析資料...")
    df, distance_df = analyzer.load_and_analyze_data(csv_path)
    
    if df is None or distance_df is None:
        print("資料分析失敗")
        return
    
    # 印出統計資料
    analyzer.print_statistics(distance_df)
    
    # 建立雙坐標地圖
    print("\n正在建立雙坐標系統地圖...")
    map_file = analyzer.create_dual_coordinate_map(df, distance_df)
    
    # 儲存分析結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = analyzer.save_analysis_results(distance_df)
    
    print(f"\n=== 分析完成 ===")
    print(f"雙坐標地圖: {map_file}")
    print(f"分析結果: {results_file}")
    print("\n可以在瀏覽器中開啟 HTML 檔案查看地圖")

if __name__ == "__main__":
    main()
