-- =====================================================
-- 更新现有数据库：清理旧账号，更新为学号/工号
-- =====================================================

-- 先删除所有旧测试账号（除了我们要保留的）
DELETE FROM users WHERE username NOT IN ('2021001000', '2021001001', '2021001002', '2021001003', 'T001', 'T002');

-- 删除旧的学生和教师数据（他们会级联删除相关记录）
DELETE FROM students WHERE student_no NOT IN ('2021001000', '2021001001', '2021001002', '2021001003');
DELETE FROM teachers WHERE teacher_no NOT IN ('T001', 'T002');

-- 重置自增ID（可选，用于清理后重新插入）
-- ALTER TABLE users AUTO_INCREMENT = 1;

-- 现在重新插入正确的用户数据（如果删除后没有数据了）
-- 学生账号=学号，教师账号=工号，密码=账号

-- 插入学生用户（如果还不存在）
INSERT INTO users (id, username, password, role, status, last_login_at) VALUES
(1, '2021001000', '$2b$12$LnRang/HzgpysQw3LQoM3ukzwQg/zpXekycaJOccwhPgrFskypPaq', 'student', 1, NOW()),
(2, '2021001001', '$2b$12$GZskIWlPlanh5elqqPd3neVE2DkO3mbT8I46msnrM3STCqryPE84.', 'student', 1, NOW()),
(3, '2021001002', '$2b$12$a9sGOGRESeYC5GlKL0oq3O4Z/.YgEe3XCZAqQTRAFh/oma8kYciC6', 'student', 1, NULL),
(4, '2021001003', '$2b$12$aJinm/p67DePX0GZUkIZcuH2OMvMKXLYgRWbwL/RSndam4t9Al84W', 'student', 1, NULL)
ON DUPLICATE KEY UPDATE 
    username = VALUES(username),
    password = VALUES(password);

-- 插入教师用户（如果还不存在）
INSERT INTO users (id, username, password, role, status, last_login_at) VALUES
(5, 'T001', '$2b$12$Iw3oXItY93XI0cSXVFF5pOkhllyILaiYIpxTPGgKg7Q92j52uvbkS', 'teacher', 1, NULL),
(6, 'T002', '$2b$12$hmaVsgY6N.nLWAP8ojjV9uqhoEFmeRZPVazCoWJQ6zfX3.z2alj.q', 'teacher', 1, NULL)
ON DUPLICATE KEY UPDATE 
    username = VALUES(username),
    password = VALUES(password);

-- 插入或更新学生信息
INSERT INTO students (user_id, student_no, name, major, class_name, grade, phone, email, dormitory) VALUES
(1, '2021001000', '张同学', '计算机科学与技术', '计科2101', 2021, '13900139000', 'zhang@student.edu.cn', 'A1-301'),
(2, '2021001001', '刘同学', '软件工程', '软工2102', 2021, '13900139001', 'liu@student.edu.cn', 'A1-302'),
(3, '2021001002', '陈同学', '计算机科学与技术', '计科2101', 2021, '13900139002', 'chen@student.edu.cn', 'A1-303'),
(4, '2021001003', '赵同学', '信息安全', '信安2101', 2021, '13900139003', 'zhao@student.edu.cn', 'A2-101')
ON DUPLICATE KEY UPDATE
    student_no = VALUES(student_no),
    name = VALUES(name);

-- 插入或更新教师信息
INSERT INTO teachers (user_id, name, teacher_no, department, title, phone, email, office) VALUES
(5, '王教授', 'T001', '计算机科学与技术学院', '教授', '13800138000', 'wang@university.edu.cn', '科技楼A301'),
(6, '李讲师', 'T002', '软件工程学院', '讲师', '13800138001', 'li@university.edu.cn', '科技楼B205')
ON DUPLICATE KEY UPDATE
    teacher_no = VALUES(teacher_no),
    name = VALUES(name);

-- 验证更新结果
SELECT '更新后的用户列表：' AS message;
SELECT id, username, role, status FROM users ORDER BY role, username;

SELECT '学生信息：' AS message;
SELECT u.id, u.username, s.student_no, s.name, s.major 
FROM users u JOIN students s ON u.id = s.user_id;

SELECT '教师信息：' AS message;
SELECT u.id, u.username, t.teacher_no, t.name, t.department 
FROM users u JOIN teachers t ON u.id = t.user_id;
