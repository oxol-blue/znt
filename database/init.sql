-- =====================================================
-- 智慧校园多Agent双端智能体系统 - 数据库初始化脚本
-- 数据库: MySQL 8.0+
-- 包含: 9张业务表 + 测试数据
-- 更新: 2024-04-24 账号改为学号/工号，密码与账号相同
-- =====================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS znt 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE znt;

-- =====================================================
-- 1. 用户基础表 (users)
-- =====================================================
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名(学号/工号)',
    password VARCHAR(255) NOT NULL COMMENT '密码(BCrypt加密)',
    role ENUM('student', 'teacher', 'admin') NOT NULL DEFAULT 'student' COMMENT '角色',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 0-禁用, 1-启用',
    last_login_at TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户基础表';

-- =====================================================
-- 2. 教师信息表 (teachers)
-- =====================================================
DROP TABLE IF EXISTS teachers;
CREATE TABLE teachers (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '教师ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '关联用户ID',
    name VARCHAR(50) NOT NULL COMMENT '教师姓名',
    teacher_no VARCHAR(20) NOT NULL UNIQUE COMMENT '工号',
    department VARCHAR(100) NOT NULL COMMENT '所属院系',
    title VARCHAR(50) DEFAULT NULL COMMENT '职称',
    phone VARCHAR(20) DEFAULT NULL COMMENT '联系电话',
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    office VARCHAR(100) DEFAULT NULL COMMENT '办公室',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_teacher_no (teacher_no),
    INDEX idx_department (department)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师信息表';

-- =====================================================
-- 3. 学生信息表 (students)
-- =====================================================
DROP TABLE IF EXISTS students;
CREATE TABLE students (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '学生ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '关联用户ID',
    student_no VARCHAR(20) NOT NULL UNIQUE COMMENT '学号',
    name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    major VARCHAR(100) NOT NULL COMMENT '专业',
    class_name VARCHAR(50) NOT NULL COMMENT '班级',
    grade INT NOT NULL COMMENT '年级',
    phone VARCHAR(20) DEFAULT NULL COMMENT '联系电话',
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    dormitory VARCHAR(50) DEFAULT NULL COMMENT '宿舍',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_student_no (student_no),
    INDEX idx_major (major),
    INDEX idx_class (class_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生信息表';

-- =====================================================
-- 4. 图书表 (books)
-- =====================================================
DROP TABLE IF EXISTS books;
CREATE TABLE books (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '图书ID',
    isbn VARCHAR(20) NOT NULL UNIQUE COMMENT 'ISBN号',
    title VARCHAR(200) NOT NULL COMMENT '书名',
    author VARCHAR(100) NOT NULL COMMENT '作者',
    publisher VARCHAR(100) DEFAULT NULL COMMENT '出版社',
    publish_date DATE DEFAULT NULL COMMENT '出版日期',
    category VARCHAR(50) NOT NULL COMMENT '分类',
    location VARCHAR(50) DEFAULT NULL COMMENT '存放位置',
    total_quantity INT NOT NULL DEFAULT 1 COMMENT '总库存',
    available_quantity INT NOT NULL DEFAULT 1 COMMENT '可借数量',
    description TEXT DEFAULT NULL COMMENT '简介',
    status ENUM('available', 'borrowed', 'reserved', 'damaged') DEFAULT 'available' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_isbn (isbn),
    INDEX idx_title (title),
    INDEX idx_author (author),
    INDEX idx_category (category),
    INDEX idx_status (status),
    FULLTEXT INDEX ft_title_author (title, author)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书馆图书表';

-- =====================================================
-- 5. 借阅记录表 (borrows)
-- =====================================================
DROP TABLE IF EXISTS borrows;
CREATE TABLE borrows (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '借阅ID',
    book_id BIGINT UNSIGNED NOT NULL COMMENT '图书ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '借阅用户ID',
    borrow_date DATE NOT NULL COMMENT '借阅日期',
    due_date DATE NOT NULL COMMENT '应还日期',
    return_date DATE DEFAULT NULL COMMENT '实际归还日期',
    renew_count INT DEFAULT 0 COMMENT '续借次数',
    status ENUM('borrowed', 'returned', 'overdue') DEFAULT 'borrowed' COMMENT '状态',
    fine_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '罚款金额',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_user_id (user_id),
    INDEX idx_book_id (book_id),
    INDEX idx_status (status),
    INDEX idx_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图书借阅记录表';

-- =====================================================
-- 6. 场地资源表 (venues)
-- =====================================================
DROP TABLE IF EXISTS venues;
CREATE TABLE venues (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '场地ID',
    name VARCHAR(100) NOT NULL COMMENT '场地名称',
    type ENUM('library', 'lab', 'classroom', 'meeting_room', 'gym') NOT NULL COMMENT '类型',
    building VARCHAR(100) NOT NULL COMMENT '所在楼宇',
    floor INT DEFAULT 1 COMMENT '楼层',
    room_no VARCHAR(20) NOT NULL COMMENT '房间号',
    capacity INT NOT NULL COMMENT '容纳人数',
    facilities JSON DEFAULT NULL COMMENT '设施配置',
    open_time TIME DEFAULT '08:00:00' COMMENT '开放开始时间',
    close_time TIME DEFAULT '22:00:00' COMMENT '开放结束时间',
    status ENUM('available', 'occupied', 'maintenance') DEFAULT 'available' COMMENT '状态',
    description TEXT DEFAULT NULL COMMENT '场地说明',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_type (type),
    INDEX idx_status (status),
    INDEX idx_building (building),
    UNIQUE KEY uk_room (building, room_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='校园场地资源表';

-- =====================================================
-- 7. 预约记录表 (reservations)
-- =====================================================
DROP TABLE IF EXISTS reservations;
CREATE TABLE reservations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '预约ID',
    venue_id BIGINT UNSIGNED NOT NULL COMMENT '场地ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '预约用户ID',
    reserve_date DATE NOT NULL COMMENT '预约日期',
    start_time TIME NOT NULL COMMENT '开始时间',
    end_time TIME NOT NULL COMMENT '结束时间',
    purpose VARCHAR(255) DEFAULT NULL COMMENT '用途说明',
    participants INT DEFAULT 1 COMMENT '参与人数',
    status ENUM('pending', 'approved', 'rejected', 'cancelled', 'completed') DEFAULT 'pending' COMMENT '状态',
    approver_id BIGINT UNSIGNED DEFAULT NULL COMMENT '审批人ID',
    approved_at TIMESTAMP NULL DEFAULT NULL COMMENT '审批时间',
    reject_reason VARCHAR(255) DEFAULT NULL COMMENT '拒绝原因',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_venue_id (venue_id),
    INDEX idx_reserve_date (reserve_date),
    INDEX idx_status (status),
    INDEX idx_time_range (reserve_date, start_time, end_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='场地预约记录表';

-- =====================================================
-- 8. 消息通知表 (notifications)
-- =====================================================
DROP TABLE IF EXISTS notifications;
CREATE TABLE notifications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '通知ID',
    sender_id BIGINT UNSIGNED DEFAULT NULL COMMENT '发送人ID(系统通知为NULL)',
    receiver_id BIGINT UNSIGNED DEFAULT NULL COMMENT '接收人ID(群发时为NULL)',
    target_type ENUM('all', 'student', 'teacher', 'specific') DEFAULT 'specific' COMMENT '目标类型',
    title VARCHAR(200) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',
    type ENUM('system', 'library', 'task', 'reservation', 'announcement') DEFAULT 'system' COMMENT '类型',
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal' COMMENT '优先级',
    is_read TINYINT DEFAULT 0 COMMENT '是否已读: 0-未读, 1-已读',
    read_at TIMESTAMP NULL DEFAULT NULL COMMENT '阅读时间',
    attachment_url VARCHAR(500) DEFAULT NULL COMMENT '附件链接',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_receiver (receiver_id),
    INDEX idx_sender (sender_id),
    INDEX idx_type (type),
    INDEX idx_is_read (is_read),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息通知表';

-- =====================================================
-- 9. 每日任务表 (tasks)
-- =====================================================
DROP TABLE IF EXISTS tasks;
CREATE TABLE tasks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    creator_id BIGINT UNSIGNED NOT NULL COMMENT '创建人ID',
    target_type ENUM('all', 'student', 'teacher', 'specific') NOT NULL COMMENT '目标类型',
    target_users JSON DEFAULT NULL COMMENT '指定用户ID列表(特定用户时)',
    title VARCHAR(200) NOT NULL COMMENT '任务标题',
    content TEXT NOT NULL COMMENT '任务内容',
    task_type ENUM('daily', 'weekly', 'assignment', 'exam', 'activity') DEFAULT 'daily' COMMENT '任务类型',
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal' COMMENT '优先级',
    start_date DATE DEFAULT NULL COMMENT '开始日期',
    end_date DATE NOT NULL COMMENT '截止日期',
    status ENUM('draft', 'published', 'cancelled') DEFAULT 'published' COMMENT '发布状态',
    attachment_url VARCHAR(500) DEFAULT NULL COMMENT '附件链接',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_creator (creator_id),
    INDEX idx_target_type (target_type),
    INDEX idx_status (status),
    INDEX idx_end_date (end_date),
    INDEX idx_task_type (task_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='每日任务表';

-- =====================================================
-- 10. 任务完成记录表 (task_completions)
-- =====================================================
DROP TABLE IF EXISTS task_completions;
CREATE TABLE task_completions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '完成记录ID',
    task_id BIGINT UNSIGNED NOT NULL COMMENT '任务ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '完成用户ID',
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '完成时间',
    completion_note TEXT DEFAULT NULL COMMENT '完成备注',
    attachment_url VARCHAR(500) DEFAULT NULL COMMENT '完成附件',
    
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_task_user (task_id, user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_completed_at (completed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务完成记录表';

-- =====================================================
-- 测试数据插入
-- =====================================================

-- 1. 用户数据（学生账号=学号，教师账号=工号，密码=账号）
-- bcrypt哈希验证通过，密码=账号
INSERT INTO users (username, password, role, status, last_login_at) VALUES
('2021001000', '$2b$12$47jmlkBWIgOE5WKkfpMhYOKOmwdJEZsXeGKDx13SfoQZzlmF1GrEq', 'student', 1, NOW()),
('2021001001', '$2b$12$zVX4yDZE2Pw7kzNUKxJBVeCE.gwh.c33HtMd1bP79FW62i9irSJby', 'student', 1, NOW()),
('2021001002', '$2b$12$uPyu/xgipyPvz4uZCIaiXe0gMiyPbINhCAFW4iwR03SCzqvV5ywSq', 'student', 1, NULL),
('2021001003', '$2b$12$P63lWH8K9wOJTpzqYAkRhOEvup9/uLThN9iFF/tNMwUl9BO./8coW', 'student', 1, NULL),
('T001', '$2b$12$ok0MEi2D2i6WDqK/11o.7OWBp1Vby13BC4B7Xke00mx0OGgMbWQ5q', 'teacher', 1, NULL),
('T002', '$2b$12$pmKeRDAEbVvWIp4DwHh/.e14mqP.bfo5hhEPxRmuWb3uFaiqn44DO', 'teacher', 1, NULL);

-- 2. 教师数据
INSERT INTO teachers (user_id, name, teacher_no, department, title, phone, email, office) VALUES
(5, '王教授', 'T001', '计算机科学与技术学院', '教授', '13800138000', 'wang@university.edu.cn', '科技楼A301'),
(6, '李讲师', 'T002', '软件工程学院', '讲师', '13800138001', 'li@university.edu.cn', '科技楼B205');

-- 3. 学生数据
INSERT INTO students (user_id, student_no, name, major, class_name, grade, phone, email, dormitory) VALUES
(1, '2021001000', '张同学', '计算机科学与技术', '计科2101', 2021, '13900139000', 'zhang@student.edu.cn', 'A1-301'),
(2, '2021001001', '刘同学', '软件工程', '软工2102', 2021, '13900139001', 'liu@student.edu.cn', 'A1-302'),
(3, '2021001002', '陈同学', '计算机科学与技术', '计科2101', 2021, '13900139002', 'chen@student.edu.cn', 'A1-303'),
(4, '2021001003', '赵同学', '信息安全', '信安2101', 2021, '13900139003', 'zhao@student.edu.cn', 'A2-101');

-- 4. 图书数据
INSERT INTO books (isbn, title, author, publisher, publish_date, category, location, total_quantity, available_quantity, description) VALUES
('978-7-111-42876-3', 'Python编程：从入门到实践', 'Eric Matthes', '人民邮电出版社', '2020-05-15', '计算机', 'A区-01-05', 5, 3, 'Python入门经典教材，适合零基础学习'),
('978-7-111-54483-8', '算法导论', 'Thomas H. Cormen', '机械工业出版社', '2019-03-20', '计算机', 'A区-02-12', 3, 2, '算法领域的权威教材'),
('978-7-115-40479-2', '深度学习', 'Ian Goodfellow', '人民邮电出版社', '2018-07-10', '人工智能', 'B区-01-03', 4, 4, 'AI深度学习经典著作'),
('978-7-302-32982-4', '操作系统概念', 'Abraham Silberschatz', '清华大学出版社', '2021-01-15', '计算机', 'A区-03-08', 6, 5, '操作系统经典教材'),
('978-7-111-51351-2', '数据结构与算法分析', 'Mark Allen Weiss', '机械工业出版社', '2020-08-20', '计算机', 'A区-02-15', 4, 3, '数据结构与算法经典教材'),
('978-7-115-40080-0', '机器学习实战', 'Peter Harrington', '人民邮电出版社', '2017-06-15', '人工智能', 'B区-01-06', 3, 2, '机器学习实践指南');

-- 5. 场地数据
INSERT INTO venues (name, type, building, floor, room_no, capacity, facilities, open_time, close_time, status, description) VALUES
('图书馆自习室-A01', 'library', '图书馆', 2, '201', 50, '["空调", "WiFi", "插座"]', '08:00:00', '22:00:00', 'available', '安静自习区域，适合个人学习'),
('图书馆自习室-A02', 'library', '图书馆', 2, '202', 40, '["空调", "WiFi", "插座"]', '08:00:00', '22:00:00', 'available', '小组讨论区域'),
('计算机实验室-1', 'lab', '科技楼', 3, '301', 30, '["电脑", "投影仪", "空调", "白板"]', '08:00:00', '21:00:00', 'available', '配备高性能计算机的实验室'),
('计算机实验室-2', 'lab', '科技楼', 3, '302', 30, '["电脑", "投影仪", "空调", "白板"]', '08:00:00', '21:00:00', 'available', '软件开发专用实验室'),
('多媒体教室-A', 'classroom', '教学楼A', 2, 'A201', 120, '["投影仪", "音响", "空调"]', '07:30:00', '22:00:00', 'available', '大型多媒体阶梯教室'),
('多媒体教室-B', 'classroom', '教学楼A', 3, 'A301', 80, '["投影仪", "音响", "空调"]', '07:30:00', '22:00:00', 'available', '中型多媒体教室'),
('会议室-1', 'meeting_room', '行政楼', 4, '401', 20, '["投影仪", "视频会议", "白板"]', '08:30:00', '18:00:00', 'available', '小型会议室，适合小组讨论'),
('会议室-2', 'meeting_room', '行政楼', 4, '402', 40, '["投影仪", "视频会议", "白板"]', '08:30:00', '18:00:00', 'available', '中型会议室');

-- 6. 借阅记录数据
INSERT INTO borrows (book_id, user_id, borrow_date, due_date, return_date, status) VALUES
(1, 1, '2026-04-10', '2026-04-24', NULL, 'borrowed'),
(2, 2, '2026-04-15', '2026-04-29', NULL, 'borrowed'),
(6, 1, '2026-04-01', '2026-04-15', '2026-04-14', 'returned');

-- 更新图书可借数量
UPDATE books SET available_quantity = available_quantity - 1 WHERE id IN (1, 2);

-- 7. 预约记录数据
INSERT INTO reservations (venue_id, user_id, reserve_date, start_time, end_time, purpose, participants, status, approver_id, approved_at) VALUES
(1, 1, '2026-04-25', '14:00:00', '16:00:00', '期末复习', 1, 'approved', 5, NOW()),
(3, 2, '2026-04-26', '09:00:00', '11:00:00', '小组项目开发', 5, 'pending', NULL, NULL);

-- 8. 消息通知数据
INSERT INTO notifications (sender_id, receiver_id, target_type, title, content, type, priority, is_read) VALUES
(NULL, 1, 'specific', '图书馆借阅到期提醒', '您借阅的《Python编程：从入门到实践》将于2026-04-24到期，请及时归还或续借。', 'library', 'normal', 0),
(NULL, NULL, 'all', '五一劳动节放假通知', '根据国家规定，2026年五一劳动节放假安排如下：5月1日至5月3日放假调休，共3天。', 'announcement', 'normal', 0),
(5, NULL, 'student', '计算机学院学术讲座', '本周五下午2点在科技楼报告厅举办人工智能前沿技术讲座，欢迎同学们参加。', 'announcement', 'normal', 0),
(5, 1, 'specific', '任务提醒：课程设计提交', '请记得在4月30日前提交数据库课程设计报告。', 'task', 'high', 0);

-- 9. 任务数据
INSERT INTO tasks (creator_id, target_type, target_users, title, content, task_type, priority, start_date, end_date, status) VALUES
(5, 'all', NULL, '阅读一本专业书籍', '请在本周内阅读至少一本与专业相关的书籍，并做好读书笔记。', 'daily', 'normal', '2026-04-21', '2026-04-27', 'published'),
(5, 'student', '[1, 2, 3]', '完成数据库实验报告', '请完成实验三：SQL高级查询，并提交实验报告。', 'assignment', 'high', '2026-04-20', '2026-04-25', 'published'),
(6, 'student', '[4]', '准备信息安全竞赛', '请准备好参加下个月的校内信息安全技能竞赛。', 'activity', 'urgent', '2026-04-15', '2026-05-15', 'published'),
(5, 'all', NULL, '校园安全教育学习', '请所有师生完成校园安全教育在线学习模块。', 'daily', 'normal', '2026-04-20', '2026-04-30', 'published');

-- 10. 任务完成记录
INSERT INTO task_completions (task_id, user_id, completed_at, completion_note) VALUES
(1, 1, '2026-04-23 15:30:00', '已完成《Python编程》阅读'),
(1, 2, '2026-04-22 10:15:00', '阅读了《算法导论》第三章');

-- =====================================================
-- 完成
-- =====================================================
SELECT '数据库初始化完成！' AS message;
SELECT CONCAT('用户表: ', COUNT(*), ' 条记录') FROM users;
SELECT CONCAT('教师表: ', COUNT(*), ' 条记录') FROM teachers;
SELECT CONCAT('学生表: ', COUNT(*), ' 条记录') FROM students;
SELECT CONCAT('图书表: ', COUNT(*), ' 条记录') FROM books;
SELECT CONCAT('借阅表: ', COUNT(*), ' 条记录') FROM borrows;
SELECT CONCAT('场地表: ', COUNT(*), ' 条记录') FROM venues;
SELECT CONCAT('预约表: ', COUNT(*), ' 条记录') FROM reservations;
SELECT CONCAT('通知表: ', COUNT(*), ' 条记录') FROM notifications;
SELECT CONCAT('任务表: ', COUNT(*), ' 条记录') FROM tasks;
SELECT CONCAT('任务完成表: ', COUNT(*), ' 条记录') FROM task_completions;
