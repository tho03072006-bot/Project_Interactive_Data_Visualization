# Nguồn dữ liệu raw và minh chứng

Các file trong thư mục này là snapshot dùng cho phần làm lại của Thắng. File dữ liệu gốc không được chỉnh sửa. Notebook `00_kiem_ke_nguon_va_schema_raw.ipynb` tạo `SOURCE_MANIFEST.csv`, `checksums_sha256.txt` và profile schema để chứng minh đúng snapshot được sử dụng.

Ngày truy cập được tài liệu bàn giao cũ ghi nhận: **21/09/2026**. Lịch sử tải ban đầu không lưu commit hoặc URL tải chính xác của mọi snapshot, vì vậy project không tuyên bố file local trùng byte với revision trực tuyến hiện tại. SHA-256 local là định danh chính của dữ liệu được phân tích.

## Cryptocurrency

- File: `crypto/coinmetrics_raw.tar.gz`
- Nguồn: Coin Metrics Community Data
- Kho: https://github.com/coinmetrics/data
- Dữ liệu: giá, vốn hóa current/estimated, reported spot trading volume và chỉ số on-chain theo coin-ngày.
- Giấy phép: CC BY-NC 4.0 theo README nguồn.
- Giới hạn: chỉ một phần coin có `PriceUSD` đủ dài; không thay giá thiếu bằng dữ liệu ước lượng.
- Trường volume dùng trong project là `volume_reported_spot_usd_1d`; không được diễn giải là adjusted on-chain transfer value.
- Snapshot có ba giá trị USDC bất khả tín về độ lớn tại `2026-05-05`, `2026-05-20`, `2026-05-22` (`>10^15 USD/ngày`, thực tế ở mức `10^47–10^53`). Raw được giữ nguyên làm bằng chứng; processed gắn cờ và chuyển riêng ba giá trị này thành missing.

## Kinh tế vĩ mô

- `vix_daily.csv`: https://github.com/datasets/finance-vix
- `brent_daily.csv`: https://github.com/datasets/oil-prices
- `fx_daily.csv`: https://github.com/datasets/exchange-rates
- `sp500_monthly.csv`: https://github.com/datasets/s-and-p-500
- `us10y_monthly.csv`: https://github.com/datasets/bond-yields-us-10y
- `gold_monthly.csv`: https://github.com/datasets/gold-prices
- `cpi_us_monthly.csv`: https://github.com/datasets/cpi-us

Package `datasets/exchange-rates` hiện đảo các series được FRED báo USD/ngoại tệ sang ngoại tệ/USD trước khi xuất. Code nguồn dùng làm minh chứng: https://github.com/datasets/exchange-rates/blob/main/exchange_rates_flow.py. Vì vậy cột local được đặt tên `foreign_currency_per_usd`. DXY vẫn được ghi là **dựng lại** và cần so chuỗi độc lập trước khi dùng cho kết luận chính.

`sp500_monthly.csv` chứa mức S&P 500 tháng. Mô tả upstream cho biết phần lịch sử Shiller là trung bình tháng của giá đóng cửa ngày; phần mở rộng gần đây dùng chuỗi FRED `SP500` và không nên bị gắn nhãn blanket là monthly average. `gold_monthly.csv` là mức giá vàng tháng; dữ liệu 1960+ đến từ World Bank Commodity Markets, còn phần trước 1960 lặp giá trung bình năm ở từng tháng. Cửa sổ phân tích 2013+ không chịu giới hạn tiền-1960. Project không tự gắn nhãn hai nguồn này là month-end và không gọi phần trăm thay đổi của chúng là total return.

`cpi_us_monthly.csv` thiếu tháng `2025-10`. Pipeline bắt buộc tạo lịch tháng đầy đủ trước khi tính MoM/YoY; các biến cần tháng bị thiếu được để missing, không dịch theo vị trí dòng và không nội suy.

## Quốc gia

- `wb_cpi.csv`: World Bank chỉ tiêu `FP.CPI.TOTL.ZG`, lạm phát CPI hằng năm (%), không phải mức chỉ số CPI. https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG
- `wb_gdp.csv`: World Bank GDP mirror. https://github.com/datasets/gdp
- `wb_population.csv`: World Bank population mirror. https://github.com/datasets/population
- `country_codes.csv`: mã ISO và địa lý. https://github.com/datasets/country-codes

URL tải/mirror chính xác ban đầu của `wb_cpi.csv` không được lưu. Hạn chế này phải xuất hiện trong báo cáo, không được tự tạo provenance thay thế.

## Quy tắc sử dụng

1. Không ghi đè file raw.
2. Không nối bằng tên hiển thị khi đã có ISO3 hoặc ticker.
3. Không đổi missing thành 0 nếu 0 có ý nghĩa thực.
4. Không forward-fill chuỗi tháng sang ngày để tính tương quan.
5. Không nối quốc gia-năm với crypto-ngày khi raw không có khóa địa lý cho cryptocurrency.
6. Mọi calculated field và phép nối phải được lưu trong notebook cùng audit trước/sau.
