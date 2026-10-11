# Hàm Python và kỹ thuật đã sử dụng

Tệp này giải thích **hàm nào được dùng, dùng ở đâu, nhằm giải quyết vấn đề gì**. Danh mục máy đọc được tái tạo tại `data/processed/quality_reports/function_technique_catalog.csv`.

## 1. Kiểm kê và truy nguyên raw — notebook 00

| Hàm/kỹ thuật | Cách dùng | Lý do |
|---|---|---|
| `tarfile` | Đọc từng CSV thành viên trong `coinmetrics_raw.tar.gz` mà không sửa archive | Giữ snapshot raw nguyên vẹn và lấy đúng ticker từ member name. |
| `hashlib.sha256` | Tính SHA-256 cho 12 nguồn | Chứng minh notebook sau đọc đúng byte đã kiểm kê. |
| `DataFrame.dtypes`, `isna`, `nunique`, `duplicated` | Profile schema, missing và khóa | Phát hiện sai kiểu hoặc khóa trùng trước khi xử lý. |

## 2. Làm sạch — notebook 01 đến 03

| Hàm/kỹ thuật | Cách dùng | Vấn đề được giải quyết |
|---|---|---|
| `pd.to_datetime(errors="coerce")` | Chuẩn hóa ngày; parse lỗi thành `NaT` | Không để chuỗi ngày lỗi âm thầm tham gia join. |
| `pd.to_numeric(errors="coerce")` | Chuẩn hóa số; parse lỗi thành `NaN` | Tách lỗi dữ liệu khỏi giá trị 0 hợp lệ. |
| `Series.where` | Giữ giá/cap/supply dương, count/flow không âm; null volume phi thực tế | Bảo toàn dòng và khóa trong khi vô hiệu hóa riêng giá trị sai. |
| `dropna(subset=...)` | Tạo panel giá chỉ từ `PriceUSD` hợp lệ | Tránh nội suy và tránh lợi suất giả. |
| `sort_values` + `assert_unique_key` | Sắp theo ticker–date hoặc ISO3–year và chặn khóa trùng | Bảo đảm đầu vào cho time series và merge. |
| `merge(validate="one_to_one")` | Nối rank chung ngày, inflation–GDP–population | Chặn nhân dòng do duplicate key. |
| `merge(validate="many_to_one")` | Nối dimension quốc gia vào panel năm | Mỗi ISO3 ở dimension chỉ có một dòng. |
| `how="outer"` | Ghép ba chỉ tiêu World Bank | Không vứt country-year chỉ vì thiếu một chỉ tiêu. |
| Complete calendar bằng `date_range(..., freq="ME")` + `reindex` | Tạo đủ tháng kể cả 2025-10 thiếu CPI | `shift(12)` thật sự là cùng tháng năm trước. |
| `resample("ME").agg` | VIX mean/last/max/count; Brent/DXY last | Tổng hợp daily→monthly theo đúng ý nghĩa từng biến. |
| `pivot` + geometric weighted formula | Dựng DXY từ sáu tỷ giá | Đồng nhất hướng foreign-currency-per-USD và trọng số. |

## 3. Calculated fields — notebook 04

| Trường | Hàm/công thức | Ghi chú khoa học |
|---|---|---|
| `log_return` | `groupby(ticker).transform(lambda s: log(s).diff())` | Không trộn ranh giới giữa hai ticker. |
| `daily_return_pct` | `groupby(ticker).pct_change(fill_method=None) * 100` | Không tự forward-fill missing. Snapshot không có gap ngày trong price panel. |
| `ma7/30/90_usd` | `rolling(window, min_periods=window).mean()` | Chỉ có giá trị khi đủ toàn bộ số quan sát. |
| `volatility_30d_annualized_pct` | `rolling(30).std() * sqrt(365) * 100` trên log return | Dùng 365 vì crypto giao dịch liên tục. |
| `drawdown_pct` | `(price / cummax(price) - 1) * 100` | Luôn không dương; QA kiểm tra miền này. |
| `turnover_ratio` | reported spot volume / current cap | Không tính khi tử hoặc mẫu missing; không dùng estimated cap. |
| `return_robust_z_365` | `shift(1)` + rolling median + rolling exact MAD | MAD của mỗi cửa sổ bằng `median(abs(x - median(x)))`; hệ số 1.4826 đưa MAD về thang chuẩn. |
| `is_return_outlier` | `abs(robust_z) > 6` | Gắn cờ và giữ dòng; không winsorize biến động thị trường thật. |
| `current_market_share...` | cap coin / tổng current cap khả dụng cùng ngày | Tổng thị phần được QA bằng 100%. |
| `btc_dominance...` | BTC current cap / cùng mẫu số current cap | Nhãn trường ghi rõ available universe. |
| `cpi_mom_pct`, `cpi_yoy_pct` | `shift(1)`, `shift(12)` trên calendar tháng | Gap CPI làm kết quả liên quan missing thay vì nhảy tháng. |
| `real_rate_pct` | US10Y − CPI YoY | Chỉ là proxy ex-post. |

## 4. Kiểm tra chất lượng — notebook 05

- `assert` kiểm tra khóa unique/non-null, miền giá trị, foreign-key subset và tháng cuối hoàn chỉnh.
- `np.allclose` tính lại độc lập return, MA7, drawdown, rolling MAD, turnover, CPI, thị phần và DXY.
- Current cap được so với `PriceUSD × SplyCur`; sai lệch local phải dưới 0,5%. Đây là kiểm tra nhất quán, không dùng để thay raw metric.
- `merge(..., indicator=True)` đếm dòng left-only/right-only.
- Manifest được băm lại và so SHA-256 trước khi chấp nhận processed.
- Mọi kiểm tra quan trọng dùng fail-fast: sai thì notebook dừng, không chỉ in cảnh báo.

## 5. EDA và thống kê — notebook 06 đến 08

| Kỹ thuật | Trường hợp dùng | Vì sao phù hợp |
|---|---|---|
| Line chart trục log | BTC/ETH price dài hạn | Tỷ lệ tăng nhiều bậc độ lớn; log giúp so biến động theo tỷ lệ. |
| Histogram + KDE | Phân phối return | Thấy độ lệch, đuôi dày và mật độ; không dùng thay kiểm định. |
| Q–Q plot | So return với phân phối chuẩn | Cho thấy trực tiếp lệch ở hai đuôi. |
| Area/line drawdown | Mức giảm từ đỉnh | Thể hiện độ sâu và thời gian stress tốt hơn price level. |
| Bar chart cùng ngày as-of | Xếp hạng vốn hóa | Tránh trộn giá trị “mới nhất” của các ngày khác nhau. |
| Small multiples | Các chỉ số vĩ mô khác đơn vị | Không ép chung một trục y gây diễn giải sai. |
| Heatmap correlation | Nhiều cặp biến đã biến đổi | Tóm tắt hướng/cường độ; chỉ tính với số quan sát tối thiểu. |
| Scatter + OLS HAC(3) | BTC return và S&P price-level change | Scatter bộc lộ phân tán/outlier; HAC giảm nhạy với phương sai thay đổi và tự tương quan ngắn. Không phải causal model. |
| Rolling correlation | Độ ổn định quan hệ BTC–S&P | Cho thấy hệ số thay đổi theo thời gian thay vì che bằng một hệ số toàn kỳ. |
| Box/strip theo VIX regime | Phân phối BTC return ở các chế độ | Hiển thị median, IQR và quan sát thật; regime là convention mô tả. |
| Pearson + Spearman | Liên hệ tuyến tính và đơn điệu | Hai góc nhìn bổ sung; dùng pairwise complete và báo `n`. |
| Benjamini–Hochberg | Nhiều kiểm định BTC–macro | Kiểm soát false discovery rate thay vì đọc từng p-value thô. |

## 6. Những kỹ thuật cố ý không dùng

- Không nội suy giá crypto, CPI hoặc chỉ tiêu quốc gia.
- Không forward-fill macro tháng vào từng ngày crypto.
- Không coalesce current cap và estimated cap.
- Không winsorize return hoặc hyperinflation thật.
- Không nối bằng tên quốc gia khi có ISO3.
- Không gọi correlation/regression là bằng chứng nhân quả.
