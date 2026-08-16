# AI Observability & Incident Intelligence Suite (AIOps)

Hệ thống **Giám sát AI & Phân tích Sự cố tự động (AIOps)** dành cho doanh nghiệp. Giúp tối ưu lưu trữ log, tự động nhóm lỗi và phân tích nguyên nhân gốc bằng trí tuệ nhân tạo.

---

## 🚀 Giá Trị Doanh Nghiệp & Tính Năng Cốt Lõi

*   **Giảm 90% dung lượng lưu trữ**: Chỉ lưu trữ các log dị thường (anomaly) và sự cố (incident), tự động lọc bỏ log bình thường.
*   **Chống tràn cảnh báo (Alert Fatigue)**: Tự động gom các cảnh báo dị thường xảy ra cùng thời điểm vào chung một **Incident**.
*   **Tự động tìm nguyên nhân gốc (RCA)**: Sử dụng Vector Search (**FAISS**) và LLM chạy cục bộ (**Ollama**) để tra cứu lịch sử lỗi và giải thích nguyên nhân kèm hướng khắc phục.
*   **Dashboard thời gian thực**: Sử dụng WebSocket để cập nhật biểu đồ trực quan (Recharts) và luồng log sự kiện dưới dạng terminal.
*   **Bộ giả lập trực quan**: Cho phép tạo sự cố giả lập chỉ với 1 click ngay trên giao diện để kiểm tra hệ thống.

---

## 🎯 Đối Tượng Khách Hàng Phù Hợp

*   **Fintech, E-commerce, Ngân hàng**: Đảm bảo hệ thống hoạt động liên tục (High Availability), phát hiện lỗi giao dịch và thanh toán ngay lập tức.
*   **Doanh nghiệp SaaS & Cloud-native**: Quản lý Microservices phức tạp, tối ưu hóa chi phí lưu trữ log khổng lồ.
*   **Đội ngũ DevOps / SRE / IT Operations**: Giảm ngập cảnh báo (alert fatigue), tự động hóa khâu điều tra và lập báo cáo sự cố (RCA).

---

## 🗺️ Luồng Dữ Liệu & Kiến Trúc

```
[Log & Metrics Stream] ──(HTTP POST)──> [FastAPI Ingestion]
                                                │
                                                ▼ (Redis Pub/Sub)
                               ┌────────────────┴────────────────┐
                               ▼                                 ▼
                     [Streaming Workers]                [WebSocket Server]
                   (ML Anomaly Detection)                        │
                               │ (Trigger Incident)              ▼
                               ▼                         [React Dashboard]
                      [Celery Worker]                   (Real-time Interface)
                               │ (RAG Query)
                [PostgreSQL] <─┴─> [FAISS + Ollama (LLM)] ──> [AI Report]
```

---

## 🛠️ Công Nghệ Áp Dụng

*   **Backend**: FastAPI, Pydantic, SQLAlchemy.
*   **Database & Broker**: PostgreSQL, Redis (Pub/Sub & Caching).
*   **Asynchronous Engine**: Celery & Redis.
*   **Trí tuệ nhân tạo (AI/ML)**: Isolation Forest, FAISS (Vector DB), Ollama (Local LLM - Llama3).
*   **Frontend**: React (ES6+), Recharts (Biểu đồ tương tác), WebSockets (Real-time).
*   **DevOps**: Docker, Docker Compose.

---

## ⚡ Hướng Dẫn Chạy Nhanh

### 1. Khởi động hệ thống
```bash
# Copy cấu hình môi trường
cp .env.example .env

# Chạy Docker Compose
docker compose up --build
```

### 2. Các cổng dịch vụ
*   **React Dashboard UI**: [http://localhost:3000](http://localhost:3000)
*   **API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Database (PostgreSQL)**: Port `5432`
*   **Redis**: Port `6379`

---

## 🧪 Kiểm thử tính năng (Stress Test)
1. Truy cập **Dashboard** tại `http://localhost:3000`.
2. Kiểm tra trạng thái kết nối hiển thị màu xanh lá: **`LIVE FEED ACTIVE`**.
3. Nhấp vào nút **`⚡ Simulate Incident`** trên header.
4. Dashboard sẽ lập tức hiển thị Incident mới, tăng bộ đếm, cập nhật biểu đồ và hiển thị log chi tiết tại bảng Console thời gian thực mà không cần tải lại trang.