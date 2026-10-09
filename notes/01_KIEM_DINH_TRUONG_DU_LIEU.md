# Kiểm định ý nghĩa trường dữ liệu

Tài liệu này chốt cách diễn giải các trường dùng trong phần của **Thắng**. Mục tiêu là ngăn việc cột có tên hợp lý nhưng bị dùng sai ý nghĩa thị trường, sai đơn vị hoặc sai timing.

## 1. Kết luận kiểm định

- Khóa và grain của tám bảng processed là hợp lệ; không có khóa null hoặc trùng sau khi pipeline chạy.
- `CapMrktCurUSD` và `CapMrktEstUSD` được giữ riêng. Không có phép `coalesce` hai khái niệm này.
- Xếp hạng, thị phần và BTC dominance chỉ dùng current cap tại cùng ngày và cùng universe quan sát được.
- `volume_reported_spot_usd_1d` đúng là reported spot volume, không phải dòng tiền on-chain. Ba lỗi độ lớn của USDC được gắn cờ và chuyển missing trong processed; raw không đổi.
- Bảng tương quan nối đúng grain tháng với tháng. Country-year được giữ riêng, không nhân bản sang crypto-day.
- Các biến mức có xu hướng được đổi thành return/change trước khi tính tương quan. Kết quả chỉ là liên hệ thống kê, không phải quan hệ nhân quả.

## 2. Trường cryptocurrency và thị trường

| Trường processed | Trường raw/công thức | Ý nghĩa được phép dùng | Kiểm định và giới hạn |
|---|---|---|---|
| `price_usd` | `PriceUSD` | Giá tham chiếu USD cho một đơn vị tài sản | Chỉ giữ giá dương; không nội suy. Coin Metrics Reference Rate là thước đo giá USD, không phải giá đóng cửa của một sàn đơn lẻ. |
| `market_cap_current_usd` | `CapMrktCurUSD` | Giá trị vốn hóa theo current supply | Trường chính cho rank/share/dominance. Theo Coin Metrics, về khái niệm bằng `SplyCur × PriceUSD`. Kiểm tra local cho sai lệch tối đa dưới 0,5%; đa số chỉ sai số số thực. Không tự ghi đè raw metric bằng tích tính lại. |
| `market_cap_estimated_usd` | `CapMrktEstUSD` | Vốn hóa theo estimated/circulating supply từ nguồn mở rộng | Có độ phủ rộng hơn nhưng phụ thuộc ước lượng bên thứ ba. Chỉ giữ để đánh giá độ phủ; không thay current cap. |
| `reported_spot_volume_usd` | `volume_reported_spot_usd_1d` | Tổng reported spot trading volume một ngày theo nguồn | Không phải adjusted transfer value, không phải on-chain volume. Ba raw value USDC `>10^15 USD/ngày` bị coi là lỗi độ lớn và đặt missing trong processed. |
| `reported_spot_volume_invalid_flag` | quy tắc `raw volume > 10^15` | Bằng chứng dòng raw có volume bất khả tín về độ lớn | Đúng cho ba ngày USDC: 2026-05-05, 2026-05-20, 2026-05-22. Không xóa dòng; chỉ null trường volume. |
| `supply_current_native` | `SplyCur` | Current supply theo đơn vị gốc của tài sản | Dùng để kiểm tra chéo current cap; không dùng thay circulating estimated supply. |
| `active_addresses` | `AdrActCnt` | Số địa chỉ active theo định nghĩa nguồn | Chỉ áp dụng khi mạng/metric được Coin Metrics hỗ trợ; missing không đồng nghĩa bằng 0. |
| `tx_count` | `TxCnt` | Số giao dịch on-chain | Không đồng nghĩa số giao dịch trên sàn. |
| `transfer_count` | `TxTfrCnt` | Số transfer on-chain | Có thể khác `tx_count` vì một transaction có thể chứa nhiều transfer. |
| `hashrate` | `HashRate` | Hash rate của mạng khi áp dụng | Không so trực tiếp giữa các thuật toán/mạng như cùng một đơn vị kinh tế. |
| `mvrv_current` | `CapMVRVCur` | Tỷ lệ market value/realized value current | Chỉ dùng khi source cung cấp; không lấp thiếu giữa coin. |
| `exchange_inflow_usd`, `exchange_outflow_usd` | `FlowInExUSD`, `FlowOutExUSD` | Dòng vào/ra các địa chỉ sàn được nguồn nhận diện | Phụ thuộc coverage/label của nguồn; không phải toàn bộ dòng vốn thị trường. |
| `turnover_ratio` | reported volume / current cap | Cường độ reported spot volume so với current cap trong ngày | Chỉ tính khi cả tử và mẫu hợp lệ. Không diễn giải là tốc độ luân chuyển on-chain. |
| `btc_dominance_current_available_universe_pct` | BTC current cap / tổng current cap khả dụng | Tỷ trọng BTC trong **63 tài sản raw và phần có current cap ngày đó** | Không được gọi là dominance toàn thị trường toàn cầu. Mẫu số thay đổi theo coverage ngày. |
| `current_market_share_available_pct` | current cap coin / cùng mẫu số ngày | Thị phần nội bộ trong universe quan sát được | Tổng bằng 100% mỗi ngày có current cap; không thay thế market share toàn ngành. |
| `daily_return_pct` | `pct_change(PriceUSD)` theo ticker | Lợi suất đơn ngày | Panel giá không có gap lịch ngày trong snapshot; không bị biến thành lợi suất nhiều ngày. |
| `volatility_30d_annualized_pct` | std 30 log-return × √365 × 100 | Biến động năm hóa cho thị trường giao dịch 365 ngày | Là estimate mô tả dựa trên 30 quan sát, không phải forecast. |
| `return_robust_z_365` | median/MAD của 365 quan sát quá khứ | Mức cực trị của return so với lịch sử gần | MAD được tính chính xác quanh median của từng cửa sổ; `shift(1)` loại look-ahead; tối thiểu 60 quan sát. |

Nguồn định nghĩa chính: [Coin Metrics market capitalization](https://gitbook-docs.coinmetrics.io/network-data/network-data-overview/market/market-capitalization), [Coin Metrics market-cap tutorial](https://gitbook-docs.coinmetrics.io/tutorials-and-examples/tutorials/ndp_marketcap_metrics), [Coin Metrics Reference Rates methodology](https://coinmetrics.io/wp-content/uploads/2021/05/reference-rates-methodology.pdf).

## 3. Trường vĩ mô

| Trường | Ý nghĩa/timing chính xác | Điều không được suy diễn |
|---|---|---|
| `sp500_level` | Quan sát price-level S&P 500 theo tháng của tệp nguồn. Phần Shiller lịch sử là monthly average của daily closes; phần mở rộng gần đây dùng FRED `SP500`. | Không gọi toàn bộ chuỗi là month-end hoặc monthly average; không phải total-return index. |
| `sp500_return_pct` | Phần trăm thay đổi giữa hai mức tháng liên tiếp của nguồn | Không bao gồm cổ tức; khác convention timing với BTC last-valid-price. |
| `gold_usd_per_oz` | Giá vàng tháng World Bank trong cửa sổ 2013+ | Phần trước 1960 của upstream lặp annual average theo tháng; không dùng phần đó cho EDA hiện tại. |
| `cpi_mom_pct` | Thay đổi CPI so với tháng lịch ngay trước | Nếu tháng trước thiếu thì kết quả thiếu; không nhảy qua khoảng trống. |
| `cpi_yoy_pct` | Thay đổi CPI so với cùng tháng năm trước bằng `shift(12)` trên lịch liên tục | Không dùng “12 dòng trước” trên dữ liệu có gap. |
| `us10y_yield_pct` | Lợi suất danh nghĩa Treasury 10 năm theo chuỗi tháng nguồn | Không phải return của trái phiếu. |
| `real_rate_pct` | Proxy ex-post `US10Y − CPI YoY` | Không phải expected real yield, TIPS yield hoặc causal driver. |
| `vix_mean`, `vix_last`, `vix_max` | Trung bình, cuối cùng và cực đại của daily VIX close trong tháng | `risk_regime` dựa trên `vix_mean` là quy ước mô tả của project, không phải chuẩn pháp định. |
| `brent_usd_per_barrel` tháng | Quan sát Brent hợp lệ cuối cùng trong tháng | Không phải monthly average. |
| `dxy_reconstructed` | DXY proxy dựng từ sáu tỷ giá foreign-currency-per-USD và trọng số cố định | Không phải feed ICE chính thức; chỉ dùng sau khi ghi rõ đây là reconstruction. |
| `month` | Khóa ngày cuối tháng để nối các bảng tháng | Không chứng minh mỗi giá trị nguồn được quan sát đúng ngày cuối tháng. |

Nguồn semantics: [S&P 500 Core Data README](https://github.com/datasets/s-and-p-500/blob/main/README.md), [Gold Prices Core Data README](https://github.com/datasets/gold-prices), [ICE U.S. Dollar Index methodology](https://www.ice.com/publicdocs/data/ICE_FX_Indexes_Methodology.pdf).

## 4. Trường quốc gia

| Trường | Ý nghĩa | Quy tắc |
|---|---|---|
| `inflation_annual_pct` | World Bank `FP.CPI.TOTL.ZG`, lạm phát CPI hằng năm (%) | Là rate, không phải mức CPI. Hyperinflation được giữ và gắn cờ. |
| `gdp_current_usd` | GDP current USD | Không dùng như real GDP growth. |
| `population` | Dân số cùng ISO3–year | Không nội suy. |
| `gdp_per_capita_usd` | GDP current USD / population đúng cùng ISO3–year | Chỉ tính khi cả hai dương và có cùng khóa. |
| `gdp_per_capita_growth_pct` | Thay đổi current-USD GDP/người theo quốc gia | Trộn tăng trưởng thực, lạm phát và tỷ giá; chỉ dùng mô tả. |
| `continent_code = NA` | North America | Phải đọc như chuỗi, không coi là missing. |

## 5. Ba giới hạn phải nêu trong báo cáo

1. Universe crypto là danh sách tài sản có trong archive, nên dominance/share là của universe khả dụng, không phải toàn cầu.
2. Các series tháng có timing convention khác nhau; cùng khóa `month` chỉ bảo đảm cùng tháng lịch, không biến chúng thành cùng thời điểm trong tháng.
3. Tương quan Pearson/Spearman và hồi quy HAC mô tả liên hệ đồng thời; không chứng minh chỉ số vĩ mô gây ra biến động crypto.
