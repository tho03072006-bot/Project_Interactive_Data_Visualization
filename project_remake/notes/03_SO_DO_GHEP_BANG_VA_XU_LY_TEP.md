# Sơ đồ ghép bảng và xử lý từng tệp

Tệp này trả lời trực tiếp ba câu hỏi: **raw nào đã dùng, đã làm sạch gì, và bảng nào đã ghép với bảng nào**. Bản chi tiết máy đọc được nằm tại `source_processing_map.csv` và `join_lineage_detailed.csv` trong `data/processed/quality_reports/`.

## 1. Luồng tổng quát

```text
coinmetrics_raw.tar.gz
  ├─ ticker-date có PriceUSD hợp lệ ──> crypto_base ──> calculated fields ──> fact_crypto_daily
  ├─ ticker-date có cap/volume ───────> market_clean ─> daily summary ─────> fact_market_daily
  └─ coverage + common-date rank ─────────────────────────────────────────> dim_coin

VIX + Brent + FX ──> fact_macro_daily ──> tổng hợp đúng quy tắc tháng ┐
S&P + Gold + CPI + US10Y ──> lịch tháng liên tục ─────────────────────┼─> fact_macro_monthly
BTC/ETH last-valid monthly + market monthly + fact_macro_monthly ─────┘   └─> analysis_crypto_macro_monthly

WB inflation ─┐
WB GDP ───────┼─ outer join ISO3-year ─> lọc qua dim_country ─> fact_country_yearly
WB population ┘
country_codes ─────────────────────────> dim_country ──────────┘
```

## 2. Từng raw file đã được xử lý gì

| Raw file | Grain/khóa | Làm sạch/biến đổi | Đầu ra chính |
|---|---|---|---|
| `crypto/coinmetrics_raw.tar.gz` | ticker–time | Parse date/numeric; giá/cap/supply phải dương; count/flow/volume không âm; không nội suy; giữ current/estimated riêng; null 3 volume USDC bất khả tín; tạo return/MA/volatility/drawdown/MAD flag | `dim_coin`, `fact_crypto_daily`, `fact_market_daily` |
| `macro/vix_daily.csv` | date | Positive close; giữ daily; tháng tính mean/last/max/count; regime theo mean | `fact_macro_daily`, `fact_macro_monthly`, bảng analysis |
| `macro/brent_daily.csv` | date | Positive price; tháng dùng quan sát hợp lệ cuối cùng; tính percent change | daily, monthly, analysis |
| `macro/fx_daily.csv` | date–country | Chỉ sáu currency DXY; pivot; đòi đủ sáu tỷ giá; dựng geometric index; tháng dùng last | daily, monthly, analysis |
| `macro/sp500_monthly.csv` | month | Complete calendar; giá trị không dương thành missing; tính change không fill | monthly, analysis |
| `macro/us10y_monthly.csv` | month | Complete calendar; diff percentage points; ghép CPI cùng tháng để tạo ex-post proxy | monthly, analysis |
| `macro/gold_monthly.csv` | month | Complete calendar; giá dương; percent change không fill | monthly, analysis |
| `macro/cpi_us_monthly.csv` | month | Complete calendar; positive index; shift(1)/shift(12); giữ gap 2025-10 | monthly, analysis |
| `country/wb_cpi.csv` | ISO3–year | Numeric; giữ inflation âm/cực trị; flag `|z within year| > 4` | `fact_country_yearly` |
| `country/wb_gdp.csv` | ISO3–year | Nonpositive thành missing; current USD | `fact_country_yearly` |
| `country/wb_population.csv` | ISO3–year | Nonpositive thành missing; cùng năm với GDP để tính per-capita | `fact_country_yearly` |
| `country/country_codes.csv` | ISO3 | Khóa unique; giữ `NA` là North America; map continent; loại aggregate qua phép match ISO3 | `dim_country`, `fact_country_yearly` |

## 3. Các phép ghép hợp lệ

| Bước | Bảng trái → bảng phải | Khóa | Kiểu/cardinality | Mục đích và lý do đúng |
|---:|---|---|---|---|
| 1 | metadata coin → current-cap rank tại ngày chung | `ticker` | left, 1:1 | Mỗi coin nhận tối đa một rank. Không dùng ngày mới nhất riêng của từng coin. |
| 2 | `market_clean` → daily current-cap summary | `date` | left, many:1 | Nhiều ticker cùng nhận đúng một tổng thị trường của ngày; số dòng không tăng. |
| 3 | `crypto_base` → daily current-cap summary | `date` | left, many:1 | Gắn context thị trường cho ticker-date mà không nhân bản quan sát giá. |
| 4 | daily summary → BTC current cap | `date` | left, 1:1 | Tử số BTC và mẫu số universe cùng ngày. |
| 5 | complete month calendar → BTC monthly | `month` | left, 1:1 | Calendar là xương sống; tháng hiện tại chưa hoàn chỉnh bị loại trước. |
| 6 | analysis month → ETH monthly | `month` | left, 1:1 | So BTC/ETH ở cùng tháng lịch, mỗi bên một quan sát. |
| 7 | analysis month → market monthly | `month` | left, 1:1 | Gắn snapshot thị trường cuối quan sát hợp lệ trong tháng. |
| 8 | analysis crypto monthly → macro monthly | `month` | left, 1:1 | Chỉ ghép sau khi cả hai cùng grain tháng; không forward-fill daily. |
| 9 | WB inflation → WB GDP | `iso3, year` | outer, 1:1 | Giữ country-year có một trong hai chỉ tiêu; missing vẫn nhìn thấy. |
| 10 | inflation–GDP → population | `iso3, year` | outer, 1:1 | GDP/người chỉ chia đúng cùng quốc gia và cùng năm. |
| 11 | country indicator panel → `dim_country` | `iso3` | filter + left, many:1 | Loại aggregate không có ISO3 trong dimension và gắn địa lý duy nhất. |

Mỗi `merge` quan trọng dùng `validate="one_to_one"` hoặc `validate="many_to_one"`. Nếu phía “one” có khóa trùng, pipeline dừng thay vì âm thầm nhân dòng.

## 4. Các bảng cố ý không ghép

- Không ghép `fact_country_yearly` vào `fact_crypto_daily`: crypto raw không có khóa quốc gia, còn grain năm–ngày không tương thích.
- Không ghép macro tháng vào mỗi ngày crypto bằng forward-fill: làm vậy tạo nhiều bản sao của một quan sát tháng và thổi phồng cỡ mẫu.
- Không ghép current cap với estimated cap thành một cột: hai nguồn supply khác nhau.
- Không lấy “latest” riêng từng coin để xếp hạng: các ngày khác nhau không so sánh ngang hàng.

## 5. Ý nghĩa tám bảng processed

| Bảng | Khóa | Dùng khi nào |
|---|---|---|
| `dim_coin` | ticker | Coverage, taxonomy mô tả, rank same-date |
| `fact_crypto_daily` | ticker–date | Price/on-chain/calculated fields theo tài sản-ngày |
| `fact_market_daily` | ticker–date | Cap/volume/share và coverage của universe thị trường |
| `fact_macro_daily` | date | Chỉ biến thực sự quan sát ở tần suất ngày |
| `fact_macro_monthly` | month | Chuỗi tháng đầy đủ và daily variables đã tổng hợp |
| `analysis_crypto_macro_monthly` | month | EDA và correlation BTC/ETH–macro |
| `dim_country` | ISO3 | Thuộc tính địa lý |
| `fact_country_yearly` | ISO3–year | Bối cảnh GDP/dân số/lạm phát hằng năm |

## 6. Cách kiểm tra lại nhanh

1. Mở `raw_inventory.csv` và `raw_key_checks.csv` để xác nhận 12 nguồn và khóa raw.
2. Mở `crypto_cleaning_audit.csv`, `macro_cleaning_audit.csv`, `macro_month_gap_audit.csv` để xem đã làm sạch/missing gì.
3. Mở `join_lineage_detailed.csv` để kiểm tra số dòng trước/sau, unmatched và cardinality từng phép ghép.
4. Mở `data_dictionary_processed.csv` để xem định nghĩa, đơn vị, nguồn/công thức và missing của từng trường.
5. Mở `qa_summary.csv`; mọi dòng phải `PASS` sau khi chạy toàn bộ notebook.
