# Outline báo cáo Mini-Project — Viettel Digital Talent 2026 (Software Engineer)
### Đề tài: Hệ thống Helpdesk/ITSM (Ticket lifecycle, SLA, Assignment, Escalation, Event Bus)

Mục đích file này: dùng làm **chỉ dẫn cho AI agent** viết file `.docx` báo cáo hoàn chỉnh theo đúng khung mẫu `_Template__Dàn_bài_báo_cáo.docx`. Mỗi mục dưới đây liệt kê: (a) nội dung cần viết, (b) hình/bảng/đồ thị cần chèn, (c) nguồn dữ liệu để lấy nội dung đó (file thiết kế đã có, hoặc cần thao tác thêm để tạo ra).

> Lưu ý cho agent: giữ đúng cấu trúc heading của template (để Mục lục / Danh mục hình / Danh mục đồ thị tự sinh đúng), dùng `HeadingLevel` chuẩn của docx, và caption cho mọi hình/bảng (Hình 1, Bảng 1, ...) để liệt kê được vào "Danh mục hình vẽ" và "Danh mục đồ thị".

---

## 0. Trang bìa (Cover page)

**Cần điền:**
- Tên đề tài: *"Thiết kế và xây dựng hệ thống Helpdesk/ITSM quản lý ticket với cơ chế phân công tự động, SLA và event bus"* (hoặc tên ngắn gọn hơn tuỳ Hieu chọn)
- Tên sinh viên, email sinh viên — **cần hỏi người dùng**, chưa có trong dữ liệu sẵn có
- Tên mentor, đơn vị — **cần hỏi người dùng**
- Logo Viettel: giữ nguyên ảnh có sẵn trong template (`media/image1.png`)

**Hình ảnh:** không cần thêm, giữ logo gốc.

**Hành động agent cần làm nếu thiếu thông tin:** hỏi người dùng 4 trường: tên đề tài chính thức, tên/email sinh viên, tên mentor, đơn vị.

---

## 1. Lời mở đầu

**Nội dung:**
- Lý do chọn đề tài: hệ thống helpdesk thủ công/rời rạc trong doanh nghiệp gây chậm trễ xử lý sự cố, thiếu cơ chế ưu tiên theo mức độ khẩn cấp/tác động, khó theo dõi SLA.
- Bối cảnh thực tế: nhu cầu một hệ thống ITSM nội bộ có khả năng tự động phân công, leo thang (escalation), giám sát thời gian thực, tích hợp được với hệ thống ngoài qua event bus.
- Vị trí đề tài trong chương trình Viettel Digital Talent (mini-project cá nhân, lĩnh vực Software Engineer).

**Hình ảnh:** không bắt buộc, có thể chèn 1 hình minh hoạ tổng quan (Hình tổng quan hệ thống, dùng lại ở mục II.1 cũng được, hoặc rút gọn).

**Nguồn dữ liệu:** dựa trên phần mở đầu tự viết, tham chiếu tới thiết kế trong `helpdesk_system_design.md`.

---

## 2. Tóm tắt nội dung và đóng góp

**Nội dung (viết dạng gạch đầu dòng ngắn, ~1 đoạn/nửa trang):**
- Xây dựng hệ thống Helpdesk/ITSM dạng modular monolith bằng Python (FastAPI) + DuckDB.
- Cơ chế state machine cho ticket: `NEW → IN_PROGRESS → RESOLVED/REJECTED/TIMEOUT`, nhánh phụ `AWAIT_ESCALATE`/`AWAIT_REASSIGN`.
- Thuật toán phân công (assignment) dạng **plug-and-play** (Load-based, Round-robin), chọn 1 chiến lược qua config, dễ mở rộng.
- Cơ chế SLA tự động theo ma trận Urgency × Impact → Priority → thời gian phản hồi/giải quyết.
- Cơ chế escalation 3 cấp: Virtual → Human → Admin, có hàng đợi admin, và khi bị từ chối sẽ quay lại hàng đợi người yêu cầu kèm tag "REJECTED".
- Cơ chế khoá ticket (lock) có TTL, phải refresh định kỳ.
- Event Bus làm nguồn sự thật duy nhất cho lịch sử, phục vụ Kanban/Timeline/Monitor/Notification như các module con lắng nghe (subscriber), cùng nằm trong 1 gateway.
- Kết quả: hệ thống chạy được đầy đủ luồng tạo — phân công — chat — escalate/reassign — resolve — CSAT.

**Hình ảnh:** không bắt buộc; có thể chèn 1 sơ đồ kiến trúc tổng quan thu nhỏ làm điểm nhấn.

**Nguồn dữ liệu:** tổng hợp trực tiếp từ `helpdesk_system_design.md` (mục 1, 2, 7, 8, 9, 4).

---

## 3. Mục lục / Danh mục hình vẽ / Danh mục đồ thị

Không cần soạn nội dung — để trống khung tiêu đề, dùng field TOC / List of Figures / List of Tables tự động của Word (agent tạo bằng `docx` npm package với `TableOfContents` field, và field riêng cho List of Figures dựa trên style caption).

---

## I. Giới thiệu

**Nội dung:**
1. Đặt vấn đề: hạn chế của quy trình xử lý ticket thủ công (không ưu tiên theo mức độ nghiêm trọng, không tự động phân công, thiếu giám sát SLA, khó tích hợp hệ thống ngoài).
2. Mục tiêu đề tài:
   - Tự động hoá vòng đời ticket từ khi tạo đến khi đóng.
   - Tự động tính priority & SLA từ ma trận Urgency × Impact.
   - Tự động phân công kỹ thuật viên (ưu tiên bot ảo trước, người sau) theo thuật toán có thể thay đổi.
   - Cơ chế leo thang/điều chuyển có kiểm soát qua hàng đợi admin.
   - Giám sát thời gian thực (kanban/timeline/monitor) qua event bus + WebSocket.
3. Phạm vi triển khai: giới hạn ở việc thiết kế + cài đặt phần backend (FastAPI/DuckDB) và bộ khung frontend (React); phần lọc spam để dạng module giả lập (stub).

**Hình ảnh cần chèn:**
- **Hình 1 — Sơ đồ kiến trúc tổng quan hệ thống** (Employee/Technician/Admin FE → API Gateway → Modules/Persistence/Common → Event Bus → Kanban/Timeline/Monitor/Notification).
  - *Nguồn:* vẽ lại từ sơ đồ ASCII mục 1 trong `helpdesk_system_design.md`, xuất bằng Visualizer hoặc vẽ tay trong draw.io/Excalidraw rồi export PNG/SVG.

**Nguồn dữ liệu:** `helpdesk_system_design.md` mục 1, 2, 5.

---

## II. Nội dung và phương pháp

Đây là phần **dài nhất**, tương ứng toàn bộ tài liệu thiết kế đã có. Nên chia thành các mục con (agent tự đặt heading cấp 2, ví dụ II.1, II.2, ...):

### II.1. Kiến trúc phân lớp (Layered Architecture)
**Nội dung:** trình bày 4 lớp Gateway / Common / Persistence / Modules, quy tắc import 1 chiều, lý do tách lớp (dễ test, dễ thay thế, Kanban/Timeline/Monitor/Notification chỉ là subscriber không gọi thẳng service).
**Hình ảnh:**
- **Hình 2 — Sơ đồ 4 lớp** (Gateway → Modules → Persistence → Common, mũi tên chiều phụ thuộc).
  *Nguồn:* mục 2 trong `helpdesk_system_design.md`.

### II.2. Mô hình dữ liệu (Database Schema)
**Nội dung:** liệt kê các bảng chính (users, tickets, ticket_messages, escalation_requests, reassign_requests, sla_policy, priority_matrix, csat_surveys, events, ...), giải thích các trường quan trọng, giải thích vì sao lock không nằm trong DB mà ở bộ nhớ (in-memory, có TTL).
**Hình ảnh:**
- **Hình 3 — Sơ đồ ERD** (users, tickets, ticket_messages, escalation_requests, reassign_requests, tags, csat_surveys, events, sla_policy, priority_matrix — với các khoá ngoại).
  *Nguồn:* dựng từ DDL mục 3 trong `helpdesk_system_design.md`; có thể dùng công cụ như dbdiagram.io hoặc Visualizer để vẽ.
- **Bảng 1 — Ma trận Urgency × Impact → Priority.**
  *Nguồn:* mục 6/11 file thiết kế (bảng P1–P4).
- **Bảng 2 — Bảng SLA theo Priority** (first response / resolve / near-breach %).
  *Nguồn:* mục 6/11 file thiết kế.

### II.3. Vòng đời ticket (State Machine)
**Nội dung:** giải thích 7 trạng thái, quy tắc terminal state không được mở lại, cơ chế timeout 30 phút không có tin nhắn mới, breach là bản ghi chứ không phải trạng thái.
**Hình ảnh:**
- **Hình 4 — Sơ đồ trạng thái ticket** (state diagram: NEW → IN_PROGRESS → RESOLVED/REJECTED/TIMEOUT, nhánh AWAIT_ESCALATE/AWAIT_REASSIGN).
  *Nguồn:* mục 6 file thiết kế; vẽ bằng Mermaid state diagram rồi export ảnh.

### II.4. Thuật toán phân công (Assignment) — kiến trúc plug-and-play
**Nội dung:** registry pattern, enum `AssignmentAlgorithm`, 2 chiến lược mặc định (Load-based, Round-robin), cách thêm chiến lược mới chỉ cần 1 file + 1 dòng đăng ký, cấu hình chọn 1 chiến lược duy nhất tại 1 thời điểm.
**Hình ảnh:**
- **Hình 5 — Sơ đồ lớp (class diagram) Strategy Pattern cho Assignment** (`AssignmentStrategy` ABC ← `LoadBasedStrategy`, `RoundRobinStrategy`; `AssignmentService` → `STRATEGY_REGISTRY`).
  *Nguồn:* mục 7 file thiết kế.
- **Hình 6 — Sơ đồ luồng phân công** (thử Virtual online trước → Human online → unassigned/sweep lại).
  *Nguồn:* mục 7 file thiết kế.

### II.5. Cơ chế Escalation & Reassignment
**Nội dung:** chuỗi leo thang Virtual → Human → Admin, hàng đợi admin gộp escalation + reassign + SLA near-breach, và cơ chế khi admin từ chối thì yêu cầu quay lại hàng đợi của người gửi kèm tag REJECTED.
**Hình ảnh:**
- **Hình 7 — Sequence diagram: luồng escalation** (Technician → EscalationService → Admin Queue → Admin quyết định → (approve: reassign lên tier trên) / (reject: quay lại hàng đợi requester, tag REJECTED) → Notification).
  *Nguồn:* mục 8 file thiết kế.

### II.6. Cơ chế khoá ticket (Lock) có TTL
**Nội dung:** lock lưu in-memory dict, có `expires_at`, technician/admin phải gọi refresh định kỳ, admin có quyền force-release, job quét lock hết hạn.
**Hình ảnh:**
- **Hình 8 — Sequence diagram vòng đời một lock** (toggle acquire → refresh (lặp lại) → release / hết hạn tự động → force-release bởi admin).
  *Nguồn:* mục 9 file thiết kế.

### II.7. Event Bus & hệ thống sự kiện
**Nội dung:** vai trò event bus là nguồn sự thật duy nhất, danh sách nhóm sự kiện chính, cách Kanban/Timeline/Monitor/Notification là các subscriber độc lập trong cùng 1 tiến trình gateway (không gọi thẳng service), khả năng thay thế bằng RabbitMQ khi cần tách tiến trình.
**Hình ảnh:**
- **Hình 9 — Sơ đồ publish/subscribe của Event Bus** (Service → EventBus.publish → [Kanban, Timeline, Monitor, Notification, Event Repository] subscribers).
  *Nguồn:* mục 4/10 file thiết kế.

### II.8. Thông báo thời gian thực (Notification module)
**Nội dung:** notification là 1 subscriber đặc biệt, dịch sự kiện thành thông báo theo user_id, đẩy qua kênh WebSocket riêng của từng user.
**Hình ảnh:** có thể gộp chung với Hình 9, hoặc thêm 1 bảng liệt kê "loại sự kiện → nội dung thông báo".
- **Bảng 3 — Bảng ánh xạ EventType → Thông báo người dùng.**
  *Nguồn:* mục 10 file thiết kế (`_ROUTE_TABLE`).

### II.9. API & WebSocket
**Nội dung:** tóm tắt các nhóm route REST (auth, ticket, message, escalation, admin queue/all-tickets, csat...) và các kênh WebSocket (ticket room, kanban, timeline, monitor, notifications).
**Hình ảnh:** không bắt buộc hình, có thể để dạng bảng liệt kê endpoint chính (Bảng 4, tuỳ chọn).

### II.10. Giao diện người dùng (Frontend)
**Nội dung:** tóm tắt cấu trúc frontend theo vai trò (Employee/Technician/Admin), các thành phần dùng chung (StatusStepper, LockBadge, ChatRoom kiểu Messenger).
**Hình ảnh:**
- **Hình 10 — Sơ đồ cây thư mục / route frontend rút gọn theo vai trò.**
  *Nguồn:* mục 17 file thiết kế.

---

## III. Kết quả thực hiện và đánh giá

**Đây là phần bắt buộc phải có ảnh chụp màn hình thực tế / kết quả chạy thử — cần Hieu build và chạy hệ thống trước khi viết phần này**, vì thiết kế hiện tại mới ở dạng tài liệu, chưa có phần cài đặt/chạy thử. Agent cần liệt kê rõ các ảnh còn thiếu và đánh dấu "cần bổ sung sau khi có bản chạy thử":

**Nội dung:**
- Mô tả môi trường triển khai (Python version, FastAPI, DuckDB, React/Vite).
- Mô tả kịch bản thử nghiệm: tạo ticket → hệ thống tính priority/SLA → tự động gán cho technician ảo → escalate lên người → admin duyệt/từ chối → resolve → CSAT.
- Đánh giá: thời gian phản hồi hệ thống, độ chính xác phân công, độ ổn định lock TTL, khả năng mở rộng thuật toán phân công (thêm 1 strategy mới chỉ mất bao nhiêu dòng code — có thể trích dẫn cụ thể).

**Hình ảnh cần chèn (⚠ cần chụp từ hệ thống thật, hiện chưa có):**
- **Hình 11 — Màn hình tạo ticket (Employee)** với chọn Urgency/Impact.
- **Hình 12 — Màn hình chat room kiểu Messenger** (bubble, reply, đính kèm file).
- **Hình 13 — Màn hình Kanban board (Admin)** theo 7 trạng thái.
- **Hình 14 — Màn hình Timeline sự kiện (Admin)**.
- **Hình 15 — Màn hình hàng đợi Admin (Escalation/Reassign/SLA near-breach)**.
- **Hình 16 — Màn hình khoá ticket (Lock badge hiển thị thời gian còn lại)**.
- **Hình 17 — Màn hình CSAT sau khi resolve**.
- **Bảng 5 — Bảng kết quả kiểm thử** (test case, input, expected, actual, pass/fail) cho các luồng: assignment, escalation reject-to-requester-queue, lock TTL expiry, SLA breach record.
- **Đồ thị 1 — Biểu đồ so sánh thời gian phản hồi trung bình theo Priority (P1–P4)** nếu có log thực tế, hoặc dữ liệu mô phỏng có ghi chú rõ là mô phỏng.

**Nguồn dữ liệu:** cần chạy thử hệ thống thật; **agent nên hỏi người dùng** có sẵn ảnh chụp màn hình / log kết quả chưa, nếu chưa thì để placeholder rõ ràng `[Chèn ảnh sau khi chạy thử]` thay vì bịa số liệu.

---

## IV. Kết luận

**Nội dung:**
- Tóm tắt lại các cơ chế đã thiết kế/cài đặt: state machine, SLA tự động, assignment plug-and-play, escalation 3 cấp có phản hồi tag REJECTED, lock TTL, event-bus-driven monitoring.
- Đánh giá mức độ hoàn thành so với mục tiêu ban đầu.
- Hạn chế: DuckDB in-memory không bền vững qua restart, lock/round-robin cursor mất khi restart, spam filter còn là stub.
- Hướng phát triển: chuyển lock sang Redis khi scale nhiều instance, thêm chiến lược assignment mới (skill-based), triển khai spam filter thật, xuất dữ liệu DuckDB định kỳ.

**Hình ảnh:** không bắt buộc.

**Nguồn dữ liệu:** tổng hợp từ toàn bộ file thiết kế + phần III.

---

## Tài liệu tham khảo

**Nội dung cần agent tự bổ sung link/tài liệu thật (không tự bịa số liệu/tên tài liệu):**
- Tài liệu FastAPI chính thức.
- Tài liệu DuckDB chính thức.
- Tài liệu ITIL/ITSM về SLA, Priority Matrix (nếu Hieu có tham khảo khung ITIL).
- Tài liệu Event-driven architecture / Pub-Sub pattern.
- (Các tài liệu môn học / công trình liên quan nếu có, do Hieu cung cấp).

---

## Tổng hợp danh sách hình/bảng/đồ thị cần thiết (checklist cho agent)

| # | Loại | Tên | Có thể vẽ ngay từ thiết kế? | Cần chạy thử hệ thống? |
|---|---|---|---|---|
| Hình 1 | Sơ đồ | Kiến trúc tổng quan | ✅ | — |
| Hình 2 | Sơ đồ | 4 lớp Gateway/Common/Persistence/Modules | ✅ | — |
| Hình 3 | ERD | Sơ đồ dữ liệu | ✅ | — |
| Bảng 1 | Bảng | Ma trận Urgency×Impact→Priority | ✅ | — |
| Bảng 2 | Bảng | SLA theo Priority | ✅ | — |
| Hình 4 | Sơ đồ | State machine ticket | ✅ | — |
| Hình 5 | Sơ đồ | Class diagram Assignment Strategy | ✅ | — |
| Hình 6 | Sơ đồ | Luồng phân công | ✅ | — |
| Hình 7 | Sequence | Luồng escalation + reject-to-requester | ✅ | — |
| Hình 8 | Sequence | Vòng đời lock TTL | ✅ | — |
| Hình 9 | Sơ đồ | Pub/Sub Event Bus | ✅ | — |
| Bảng 3 | Bảng | EventType → Notification | ✅ | — |
| Hình 10 | Sơ đồ | Cây route frontend | ✅ | — |
| Hình 11–17 | Screenshot | Các màn hình chức năng thật | ❌ | ✅ cần build & chạy |
| Bảng 5 | Bảng | Kết quả kiểm thử | ❌ | ✅ cần chạy test |
| Đồ thị 1 | Chart | Thời gian phản hồi theo Priority | ❌ | ✅ cần log thực tế |

**Kết luận cho agent thực thi:** các Hình 1–10 và Bảng 1–3 có thể tạo ngay bằng cách vẽ lại nội dung có sẵn trong `helpdesk_system_design.md` (không cần chạy code). Phần III (Hình 11–17, Bảng 5, Đồ thị 1) bắt buộc phải có bản demo/kết quả chạy thử thật — agent không được tự tạo số liệu hay ảnh giả cho phần này, phải hỏi người dùng cung cấp hoặc yêu cầu hỗ trợ build trước.
