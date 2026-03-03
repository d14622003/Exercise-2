@echo off
echo 氣象站坐標差距統計分析
echo ================================
echo.

echo 計算基本統計資料...
for /f "skip=1 tokens=9" %%i in ('type outputs\coordinate_distance_analysis_20260303_164624.csv ^| find /v ""') do (
    if not "%%i"=="" set /a count+=1
)

echo 資料檔案: outputs\coordinate_distance_analysis_20260303_164624.csv
echo 互動式地圖: outputs\dual_coordinate_map_20260303_164623.html
echo.
echo 請開啟互動式地圖檔案查看兩種坐標系統的視覺化比較
echo 藍色標記代表坐標系1，紅色標記代表坐標系2
echo 橘色連線表示差距大於1公里的測站
echo.
pause
