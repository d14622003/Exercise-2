import csv
import math
import os

def test_basic_functionality():
    """測試基本功能"""
    print("開始測試...")
    
    # 檢查 outputs 目錄
    if os.path.exists("outputs"):
        print("outputs 目錄存在")
        files = os.listdir("outputs")
        print(f"outputs 目錄中的檔案: {files}")
    else:
        print("outputs 目錄不存在")
        return
    
    # 查找 CSV 檔案
    csv_files = [f for f in os.listdir("outputs") if f.startswith('weather_stations_') and f.endswith('.csv')]
    print(f"找到的 CSV 檔案: {csv_files}")
    
    if not csv_files:
        print("找不到氣象站 CSV 資料檔")
        return
    
    # 讀取 CSV 檔案
    latest_csv = max(csv_files, key=lambda x: os.path.getmtime(os.path.join("outputs", x)))
    csv_path = os.path.join("outputs", latest_csv)
    print(f"使用資料檔案: {csv_path}")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            headers = reader.fieldnames
            print(f"CSV 欄位: {headers}")
            
            # 讀取前幾行
            count = 0
            for row in reader:
                if count < 5:
                    print(f"第 {count+1} 行: {row}")
                    count += 1
                else:
                    break
                    
    except Exception as e:
        print(f"讀取檔案失敗: {e}")
    
    print("測試完成")

if __name__ == "__main__":
    test_basic_functionality()
