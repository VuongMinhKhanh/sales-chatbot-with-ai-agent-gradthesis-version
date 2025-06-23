# Sales ChatBot with AI Agents

## Giới thiệu tổng quan dự án

Dự án **Sales_ChatBot_with_AI_Agents** là hệ thống chatbot tư vấn mua hàng trực tuyến được phát triển dựa trên kiến trúc AI Agents, nhằm khắc phục các hạn chế của chatbot truyền thống trong việc tương tác linh hoạt và chủ động dẫn dắt khách hàng. 

Hệ thống chia thành nhiều AI Agents chuyên biệt, phối hợp theo mô hình “tiếp sức”:  
- **Agent 1 (Orchestrator)**: Nhận diện ngữ cảnh, xác định giai đoạn quy trình bán hàng và điều phối các agent phù hợp.  
- **Agent 2 (Product Retriever & Responser)**: Truy vấn dữ liệu sản phẩm từ Weaviate Vectorstore và phản hồi khách hàng chính xác.  
- **Agent 3 (Followup Generator)**: Tạo câu hỏi dẫn dắt tiếp theo theo quy trình bán hàng, giúp thu thập nhu cầu sâu hơn từ khách hàng.  
- **Agent 4 (User Profile Updater)**: Cập nhật thông tin khách hàng dựa trên lịch sử trò chuyện để cá nhân hóa trải nghiệm.

Hệ thống sử dụng mô hình GPT-4o-mini làm bộ não chính, kết hợp các công nghệ vectorstore Weaviate và Qdrant để lưu trữ và truy vấn dữ liệu hiệu quả. Redis được dùng để cache lịch sử chat và Chatwoot làm nền tảng quản lý hội thoại khách hàng.

Kết quả thực nghiệm cho thấy chatbot đạt độ chính xác trung bình trên 80%, thời gian phản hồi nhanh và chỉ số hài lòng khách hàng (CSAT) cao. Kiến trúc cho phép mở rộng linh hoạt bằng cách thêm mới các AI Agents mà không cần thay đổi hệ thống hiện tại, đáp ứng tốt nhu cầu tư vấn bán hàng hiện đại.

---

## Hướng dẫn cài đặt và chạy dự án (Python 3.12.x trên CMD Windows) cùng với ngrok

1. **Cài đặt Python 3.12.x**  
   - Tải và cài đặt Python 3.12.x từ: https://www.python.org/downloads/release/python-312x/  
   - Khi cài đặt, nhớ tích chọn “Add Python to PATH”.

2. **Tạo môi trường ảo**  
   - Mở CMD, gõ lệnh:  
     ```
     python -m venv .venv
     ```

3. **Kích hoạt môi trường ảo**  
   - Trên CMD, chạy lệnh:  
     ```
     .venv\Scripts\activate
     ```

4. **Cài đặt các thư viện cần thiết**  
   - Khi đã kích hoạt môi trường ảo, chạy:  
     ```
     pip install -r requirements.txt
     ```

5. **Cài đặt và cấu hình ngrok**  
   - Tải ngrok từ https://ngrok.com/download  
   - Giải nén và đặt vào thư mục dễ truy cập hoặc thêm vào PATH  
   - Đăng ký tài khoản ngrok và lấy **Auth Token**  
   - Cấu hình ngrok với lệnh (chỉ chạy 1 lần để lưu token):  
     ```
     ngrok authtoken YOUR_AUTH_TOKEN
     ```

6. **Thiết lập các biến môi trường (credentials)**  
   - Thiết lập các biến môi trường quan trọng như:  
     - `OPENAI_API_KEY`  
     - `WEAVIATE_URL`  
     - `QDRANT_API_KEY`  
     - `CHATWOOT_API_KEY` (nếu có)  
   - Có thể dùng lệnh CMD như sau để tạm thiết lập:  
     ```
     set OPENAI_API_KEY=your_openai_key_here
     set WEAVIATE_URL=your_weaviate_url_here
     set QDRANT_API_KEY=your_qdrant_api_key_here
     ```
   - Hoặc thiết lập biến môi trường trong hệ thống Windows để tự động có hiệu lực.

7. **Chạy ứng dụng Flask**  
   - Mặc định ứng dụng Flask chạy trên cổng 5000  
   - Chạy lệnh:  
     ```
     python app.py
     ```

8. **Chạy ngrok trên cùng cổng với Flask**  
   - Mở CMD mới, chạy lệnh (thay `your_subdomain.ngrok-free.app` bằng domain hoặc URL bạn muốn):  
     ```
     ngrok http --url=your_subdomain.ngrok-free.app 5000
     ```
   - Ngrok sẽ tạo tunnel tới ứng dụng Flask của bạn trên cổng 5000, cho phép truy cập từ internet.

---

**Lưu ý:**  
- Đảm bảo `ngrok` và ứng dụng Flask đều chạy trên cùng một cổng (mặc định là 5000).  
- Cập nhật URL `--url` của ngrok trùng với tên miền hoặc URL thực tế bạn muốn public.  
- Các biến môi trường phải được thiết lập chính xác để ứng dụng hoạt động ổn định.



---

## Hướng dẫn thêm mới AI Agents

1. **Tạo file agent mới**  
   - Tạo file Python theo tên `agentX.py` (X là số hoặc tên chức năng).

2. **Định nghĩa hàm chính cho agent**  
   - Định nghĩa hàm xử lý chính, biết rõ cấu trúc payload đầu vào và các tham số cần thiết.  
   - Các tham số bắt buộc phải khai báo trong file `.yml` để Agent 1 có thể lấy đúng dữ liệu.

3. **Cập nhật cấu hình agent trong `agent_register.py`**  
   - Thêm mục mới với các trường:  
     - `description` (mô tả)  
     - `when-to-use` (khi nào dùng agent này)  
     - `required_params` (tham số bắt buộc)  
     - `api_call`, `payload_schema` (tùy chọn)

4. **(Tùy chọn) Thêm mô tả workflow cho agent 1 prompt**  
   - Mô tả cách agent mới phối hợp với các agent khác trong hệ thống.

5. **Kiểm thử agent mới**  
   - Chạy thử và kiểm tra agent hoạt động chính xác, phối hợp mượt với các agent khác.

