-- =====================================================
-- 紧急修复：更新所有用户密码（密码=账号）
-- 执行方式: mysql -u root -p znt < fix_passwords.sql
-- =====================================================

USE znt;

-- 删除所有旧账号，保留正确的账号
DELETE FROM users WHERE username NOT IN ('2021001000', '2021001001', '2021001002', '2021001003', 'T001', 'T002');

-- 如果账号不存在则插入，存在则更新密码
INSERT INTO users (id, username, password, role, status, last_login_at) VALUES
(1, '2021001000', '$2b$12$47jmlkBWIgOE5WKkfpMhYOKOmwdJEZsXeGKDx13SfoQZzlmF1GrEq', 'student', 1, NOW()),
(2, '2021001001', '$2b$12$zVX4yDZE2Pw7kzNUKxJBVeCE.gwh.c33HtMd1bP79FW62i9irSJby', 'student', 1, NOW()),
(3, '2021001002', '$2b$12$uPyu/xgipyPvz4uZCIaiXe0gMiyPbINhCAFW4iwR03SCzqvV5ywSq', 'student', 1, NULL),
(4, '2021001003', '$2b$12$P63lWH8K9wOJTpzqYAkRhOEvup9/uLThN9iFF/tNMwUl9BO./8coW', 'student', 1, NULL),
(5, 'T001', '$2b$12$ok0MEi2D2i6WDqK/11o.7OWBp1Vby13BC4B7Xke00mx0OGgMbWQ5q', 'teacher', 1, NULL),
(6, 'T002', '$2b$12$pmKeRDAEbVvWIp4DwHh/.e14mqP.bfo5hhEPxRmuWb3uFaiqn44DO', 'teacher', 1, NULL)
ON DUPLICATE KEY UPDATE 
    password = VALUES(password),
    status = 1;

-- 确保学生信息正确
INSERT INTO students (user_id, student_no, name, major, class_name, grade, phone, email, dormitory) VALUES
(1, '2021001000', '张同学', '计算机科学与技术', '计科2101', 2021, '13900139000', 'zhang@student.edu.cn', 'A1-301'),
(2, '2021001001', '刘同学', '软件工程', '软工2102', 2021, '13900139001', 'liu@student.edu.cn', 'A1-302'),
(3, '2021001002', '陈同学', '计算机科学与技术', '计科2101', 2021, '13900139002', 'chen@student.edu.cn', 'A1-303'),
(4, '2021001003', '赵同学', '信息安全', '信安2101', 2021, '13900139003', 'zhao@student.edu.cn', 'A2-101')
ON DUPLICATE KEY UPDATE 
    user_id = VALUES(user_id),
    name = VALUES(name);

-- 确保教师信息正确
INSERT INTO teachers (user_id, name, teacher_no, department, title, phone, email, office) VALUES
(5, '王教授', 'T001', '计算机科学与技术学院', '教授', '13800138000', 'wang@university.edu.cn', '科技楼A301'),
(6, '李讲师', 'T002', '软件工程学院', '讲师', '13800138001', 'li@university.edu.cn', '科技楼B205')
ON DUPLICATE KEY UPDATE 
    user_id = VALUES(user_id),
    name = VALUES(name);

-- 验证结果
SELECT '修复后的用户列表：' AS message;
SELECT id, username, role, status FROM users ORDER BY role, username;
