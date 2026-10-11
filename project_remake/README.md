# Project remake - Phần dữ liệu và EDA của Thắng

Thư mục này xây dựng lại độc lập phần dữ liệu cho đề tài **Phân tích thị trường tiền điện tử (Cryptocurrency) và mối tương quan với các chỉ số kinh tế vĩ mô**. Không notebook nào đọc bảng processed hoặc kết quả EDA của project cũ.

## Cấu trúc

```text
project_remake/
├── data/
│   ├── raw/          # Snapshot nguồn, manifest, checksum và minh chứng
│   └── processed/    # Bảng mới, báo cáo chất lượng và hình EDA
├── notes/            # Ghi chú kiểm định trường, hàm/kỹ thuật và lineage phép ghép
└── scripts/          # Notebook đánh số theo đúng thứ tự thực hiện
```

`data/raw/` là vùng bất biến. Notebook chỉ đọc raw và chỉ ghi vào `data/processed/`, ngoại trừ notebook 00 cập nhật manifest/checksum minh chứng ngay cạnh snapshot raw.

## Thứ tự notebook

1. `00_kiem_ke_nguon_va_schema_raw.ipynb`: kiểm kê nguồn, checksum, grain, khóa và schema.
2. `01_lam_sach_du_lieu_crypto.ipynb`: làm sạch Coin Metrics, không nội suy giá; giữ riêng current/estimated cap và đặt đúng nghĩa reported spot volume.
3. `02_lam_sach_du_lieu_vi_mo.ipynb`: làm sạch VIX, dầu, tỷ giá, DXY và các chuỗi tháng trên lịch tháng liên tục.
4. `03_lam_sach_du_lieu_quoc_gia.ipynb`: chuẩn hóa panel World Bank bằng ISO3.
5. `04_tao_truong_va_ket_bang.ipynb`: calculated fields và các phép nối đã kiểm soát cardinality.
6. `05_kiem_tra_chat_luong_processed.ipynb`: kiểm tra khóa, miền giá trị, quan hệ tham chiếu và mục đích từng bảng.
7. `06_eda_thi_truong_crypto.ipynb`: EDA tĩnh cho thị trường cryptocurrency.
8. `07_eda_boi_canh_vi_mo.ipynb`: EDA tĩnh cho bối cảnh vĩ mô.
9. `08_eda_moi_tuong_quan.ipynb`: tương quan crypto-vĩ mô trên tháng hoàn chỉnh.

Mỗi notebook ghi rõ câu hỏi, trường dữ liệu, grain, phép biến đổi, lý do chọn biểu đồ, giới hạn và các suy luận không được phép.

## Bảng đầu ra có mục đích

| Bảng | Grain | Mục đích |
|---|---|---|
| `dim_coin.csv` | một ticker | Độ phủ raw/PriceUSD thực tế, taxonomy mô tả và xếp hạng current cap tại một ngày chung |
| `fact_crypto_daily.csv.gz` | ticker-ngày | Giá, on-chain, current/estimated cap riêng biệt, reported spot volume và calculated fields |
| `fact_market_daily.csv.gz` | ticker-ngày | Current/estimated cap riêng biệt, reported spot volume và thị phần current-cap trên universe quan sát được |
| `fact_macro_daily.csv` | ngày | Chỉ giữ biến thực sự có tần suất ngày; không forward-fill biến tháng |
| `fact_macro_monthly.csv` | tháng | Lịch tháng liên tục; chuỗi tháng và biến ngày đã tổng hợp đúng tần suất |
| `analysis_crypto_macro_monthly.csv` | tháng hoàn chỉnh | Bảng phân tích 1:1 cho tương quan BTC/ETH-vĩ mô, kết thúc ở tháng crypto hoàn chỉnh gần nhất |
| `dim_country.csv` | ISO3 | Thuộc tính quốc gia dùng cho bản đồ |
| `fact_country_yearly.csv` | ISO3-năm | GDP, dân số, lạm phát; không nội suy giá trị thiếu |

Không nối bảng quốc gia-năm vào crypto-ngày vì không có khóa hay grain có ý nghĩa. Không nối biến macro tháng vào từng ngày crypto bằng forward-fill vì sẽ tạo quan sát giả cho phân tích tương quan.

## Quy ước khoa học quan trọng

- `CapMrktCurUSD` là biến chính cho xếp hạng, thị phần và BTC dominance. `CapMrktEstUSD` chỉ được giữ như trường độ phủ thay thế; hai loại không bị coalesce.
- `volume_reported_spot_usd_1d` là reported spot trading volume, không phải adjusted on-chain transfer value. Ba giá trị USDC ở mức `10^47–10^53 USD/ngày` được giữ nguyên trong raw nhưng gắn cờ và chuyển thành missing trong processed.
- CPI MoM/YoY được tính trên lịch tháng liên tục. Nếu thiếu tháng, các phép biến đổi phụ thuộc tháng đó để missing; không dùng “12 dòng trước”.
- S&P 500 là mức tháng theo nguồn: lịch sử Shiller là trung bình tháng của giá đóng cửa, phần mở rộng mới dùng chuỗi FRED `SP500`. Vàng trong cửa sổ phân tích 2013+ là giá tháng World Bank. Thay đổi của hai chuỗi không phải total return và không được gọi chung là quan sát cuối tháng.
- Real-rate là proxy ex-post `US10Y - CPI YoY`, không phải real yield kỳ vọng. DXY là chuỗi dựng lại, không phải feed ICE chính thức.
- Cực trị lợi suất crypto dùng MAD chính xác của từng cửa sổ quá khứ và được giữ lại; lạm phát quốc gia cực trị cũng chỉ gắn cờ. Mọi chính sách missing/outlier/join được xuất ở `data/processed/quality_reports/cleaning_policy.csv`.
- Cửa sổ tương quan chính bắt đầu 01/2018; `eda_window_sensitivity.csv` cung cấp đối chiếu từ 01/2015.

## Tài liệu kiểm định và truy nguyên

- `notes/01_KIEM_DINH_TRUONG_DU_LIEU.md`: ý nghĩa thực tế, đơn vị, timing và giới hạn của các trường quan trọng.
- `notes/02_HAM_VA_KY_THUAT_XU_LY.md`: hàm Python, kỹ thuật làm sạch, calculated fields, kiểm định và EDA đã dùng.
- `notes/03_SO_DO_GHEP_BANG_VA_XU_LY_TEP.md`: từng raw file được xử lý gì, bảng nào ghép với bảng nào, khóa và cardinality.
- Các bản máy đọc tương ứng nằm tại `data/processed/quality_reports/source_processing_map.csv`, `join_lineage_detailed.csv` và `function_technique_catalog.csv`.

## Chạy tái lập

```powershell
.\.venv\Scripts\python.exe scripts\run_all_notebooks.py
```

Notebook phải chạy được từ kernel sạch theo đúng thứ tự trên. Bất kỳ vi phạm khóa, cardinality hoặc miền giá trị nào đều làm pipeline dừng thay vì âm thầm sửa.
