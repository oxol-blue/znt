# -*- coding: utf-8 -*-
"""
AI 数据库工具模块
提供数据库查询功能，让AI能够获取实时数据
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import text
from utils.db import get_db_session


class DatabaseTools:
    """数据库工具类"""
    
    @staticmethod
    def query_user_info(user_id: int) -> Dict:
        """查询用户信息"""
        session = get_db_session()
        try:
            result = session.execute(
                text("""
                    SELECT u.id, u.username, u.role, u.status,
                           s.name as student_name, s.student_no, s.major, s.class_name,
                           t.name as teacher_name, t.teacher_no, t.department, t.title
                    FROM users u
                    LEFT JOIN students s ON u.id = s.user_id
                    LEFT JOIN teachers t ON u.id = t.user_id
                    WHERE u.id = :user_id
                """),
                {"user_id": user_id}
            ).fetchone()
            
            if result:
                return {
                    "id": result.id,
                    "username": result.username,
                    "role": result.role,
                    "status": result.status,
                    "name": result.student_name or result.teacher_name,
                    "no": result.student_no or result.teacher_no,
                    "department": result.major or result.department,
                    "class_name": result.class_name,
                    "title": result.title
                }
            return {"error": "用户不存在"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            session.close()
    
    @staticmethod
    def query_books(keyword: str = "", category: str = "", limit: int = 10) -> List[Dict]:
        """查询图书"""
        session = get_db_session()
        try:
            sql = """
                SELECT id, isbn, title, author, publisher, category, 
                       location, available_quantity, total_quantity, status
                FROM books 
                WHERE 1=1
            """
            params = {}
            
            if keyword:
                sql += " AND (title LIKE :keyword OR author LIKE :keyword)"
                params["keyword"] = f"%{keyword}%"
            
            if category:
                sql += " AND category = :category"
                params["category"] = category
            
            sql += " ORDER BY available_quantity DESC LIMIT :limit"
            params["limit"] = limit
            
            results = session.execute(text(sql), params).fetchall()
            
            return [{
                "id": r.id,
                "isbn": r.isbn,
                "title": r.title,
                "author": r.author,
                "publisher": r.publisher,
                "category": r.category,
                "location": r.location,
                "available": r.available_quantity,
                "total": r.total_quantity,
                "status": r.status
            } for r in results]
        except Exception as e:
            return [{"error": str(e)}]
        finally:
            session.close()
    
    @staticmethod
    def query_user_borrows(user_id: int) -> List[Dict]:
        """查询用户借阅记录"""
        session = get_db_session()
        try:
            print(f"[DB_TOOLS] 查询用户 {user_id} 的借阅记录")
            
            # 首先验证用户是否存在
            user_check = session.execute(
                text("SELECT id, username, role FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            ).fetchone()
            
            if not user_check:
                print(f"[DB_TOOLS] 用户 {user_id} 不存在")
                return [{"error": "用户不存在"}]
            
            print(f"[DB_TOOLS] 用户验证通过: {user_check.username}, 角色: {user_check.role}")
            
            # 如果是学生，获取学生信息
            if user_check.role == 'student':
                student_info = session.execute(
                    text("""
                        SELECT s.id, s.student_no, s.name, s.user_id
                        FROM students s
                        WHERE s.user_id = :user_id
                    """),
                    {"user_id": user_id}
                ).fetchone()
                
                if student_info:
                    print(f"[DB_TOOLS] 学生信息: {student_info.student_no}, {student_info.name}")
                else:
                    print(f"[DB_TOOLS] 未找到学生信息，但用户角色为学生")
            
            # 查询借阅记录 - 直接使用 user_id
            results = session.execute(
                text("""
                    SELECT b.id, bk.title, bk.author, b.borrow_date, 
                           b.due_date, b.return_date, b.status, b.fine_amount
                    FROM borrows b
                    JOIN books bk ON b.book_id = bk.id
                    WHERE b.user_id = :user_id
                    ORDER BY b.borrow_date DESC
                """),
                {"user_id": user_id}
            ).fetchall()
            
            print(f"[DB_TOOLS] 查询到 {len(results)} 条借阅记录")
            
            return [{
                "id": r.id,
                "book_title": r.title,
                "author": r.author,
                "borrow_date": r.borrow_date.strftime("%Y-%m-%d") if r.borrow_date else None,
                "due_date": r.due_date.strftime("%Y-%m-%d") if r.due_date else None,
                "return_date": r.return_date.strftime("%Y-%m-%d") if r.return_date else None,
                "status": r.status,
                "fine": float(r.fine_amount) if r.fine_amount else 0
            } for r in results]
        except Exception as e:
            return [{"error": str(e)}]
        finally:
            session.close()
    
    @staticmethod
    def query_venues(venue_type: str = "", date: str = "") -> List[Dict]:
        """查询场地"""
        session = get_db_session()
        try:
            sql = """
                SELECT id, name, type, building, room_no, capacity, 
                       facilities, open_time, close_time, status
                FROM venues 
                WHERE status = 'available'
            """
            params = {}
            
            if venue_type:
                sql += " AND type = :venue_type"
                params["venue_type"] = venue_type
            
            results = session.execute(text(sql), params).fetchall()
            
            venues = []
            for r in results:
                venue = {
                    "id": r.id,
                    "name": r.name,
                    "type": r.type,
                    "building": r.building,
                    "room_no": r.room_no,
                    "capacity": r.capacity,
                    "facilities": r.facilities,
                    "open_time": str(r.open_time) if r.open_time else None,
                    "close_time": str(r.close_time) if r.close_time else None,
                    "status": r.status
                }
                
                # 如果指定了日期，查询该日期的预约情况
                if date:
                    reservations = session.execute(
                        text("""
                            SELECT start_time, end_time, status
                            FROM reservations
                            WHERE venue_id = :venue_id AND reserve_date = :date
                            AND status IN ('pending', 'approved')
                        """),
                        {"venue_id": r.id, "date": date}
                    ).fetchall()
                    
                    venue["reservations"] = [{
                        "start": str(res.start_time),
                        "end": str(res.end_time),
                        "status": res.status
                    } for res in reservations]
                
                venues.append(venue)
            
            return venues
        except Exception as e:
            return [{"error": str(e)}]
        finally:
            session.close()
    
    @staticmethod
    def query_user_reservations(user_id: int) -> List[Dict]:
        """查询用户预约记录"""
        session = get_db_session()
        try:
            results = session.execute(
                text("""
                    SELECT r.id, v.name as venue_name, v.building, v.room_no,
                           r.reserve_date, r.start_time, r.end_time, 
                           r.purpose, r.status, r.reject_reason
                    FROM reservations r
                    JOIN venues v ON r.venue_id = v.id
                    WHERE r.user_id = :user_id
                    ORDER BY r.reserve_date DESC, r.start_time DESC
                """),
                {"user_id": user_id}
            ).fetchall()
            
            return [{
                "id": r.id,
                "venue": f"{r.venue_name} ({r.building}-{r.room_no})",
                "date": r.reserve_date.strftime("%Y-%m-%d") if r.reserve_date else None,
                "time": f"{r.start_time} - {r.end_time}",
                "purpose": r.purpose,
                "status": r.status,
                "reject_reason": r.reject_reason
            } for r in results]
        except Exception as e:
            return [{"error": str(e)}]
        finally:
            session.close()
    
    @staticmethod
    def query_notifications(user_id: int, role: str, unread_only: bool = False) -> List[Dict]:
        """查询通知消息"""
        session = get_db_session()
        try:
            sql = """
                SELECT id, title, content, type, priority, is_read, created_at
                FROM notifications
                WHERE (receiver_id = :user_id OR receiver_id IS NULL)
                AND (target_type = 'all' OR target_type = :role)
            """
            params = {"user_id": user_id, "role": role}
            
            if unread_only:
                sql += " AND is_read = 0"
            
            sql += " ORDER BY created_at DESC LIMIT 20"
            
            results = session.execute(text(sql), params).fetchall()
            
            return [{
                "id": r.id,
                "title": r.title,
                "content": r.content[:100] + "..." if len(r.content) > 100 else r.content,
                "type": r.type,
                "priority": r.priority,
                "is_read": r.is_read,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None
            } for r in results]
        except Exception as e:
            return [{"error": str(e)}]
        finally:
            session.close()
    
    @staticmethod
    def query_tasks(user_id: int, role: str, status: str = "") -> List[Dict]:
        """查询任务"""
        session = get_db_session()
        try:
            if role == 'student':
                # 学生查看自己的任务
                sql = """
                    SELECT t.id, t.title, t.content, t.task_type, t.priority,
                           t.end_date, t.status, tc.completed_at
                    FROM tasks t
                    LEFT JOIN task_completions tc ON t.id = tc.task_id AND tc.user_id = :user_id
                    WHERE t.status = 'published'
                    AND (t.target_type = 'all' OR t.target_type = 'student'
                         OR (t.target_type = 'specific' AND JSON_CONTAINS(t.target_users, CAST(:user_id AS JSON))))
                """
            else:
                # 教师查看自己发布的任务
                sql = """
                    SELECT id, title, content, task_type, priority, 
                           end_date, status, created_at
                    FROM tasks
                    WHERE creator_id = :user_id
                """
            
            params = {"user_id": user_id}
            
            if status:
                sql += " AND t.status = :status"
                params["status"] = status
            
            sql += " ORDER BY t.end_date ASC LIMIT 20"
            
            results = session.execute(text(sql), params).fetchall()
            
            return [{
                "id": r.id,
                "title": r.title,
                "content": r.content[:100] + "..." if len(r.content) > 100 else r.content,
                "type": r.task_type,
                "priority": r.priority,
                "end_date": r.end_date.strftime("%Y-%m-%d") if r.end_date else None,
                "status": r.status,
                "completed": r.completed_at is not None if role == 'student' else None
            } for r in results]
        except Exception as e:
            return [{"error": str(e)}]
        finally:
            session.close()
    
    @staticmethod
    def create_reservation(user_id: int, venue_id: int, date: str, 
                          start_time: str, end_time: str, purpose: str) -> Dict:
        """创建预约"""
        session = get_db_session()
        try:
            # 检查时间冲突
            conflict = session.execute(
                text("""
                    SELECT COUNT(*) as count
                    FROM reservations
                    WHERE venue_id = :venue_id AND reserve_date = :date
                    AND status IN ('pending', 'approved')
                    AND ((start_time <= :start_time AND end_time > :start_time)
                         OR (start_time < :end_time AND end_time >= :end_time)
                         OR (start_time >= :start_time AND end_time <= :end_time))
                """),
                {
                    "venue_id": venue_id,
                    "date": date,
                    "start_time": start_time,
                    "end_time": end_time
                }
            ).fetchone()
            
            if conflict and conflict.count > 0:
                return {"success": False, "message": "该时间段已被预约"}
            
            # 创建预约
            result = session.execute(
                text("""
                    INSERT INTO reservations (venue_id, user_id, reserve_date, start_time, end_time, purpose, status)
                    VALUES (:venue_id, :user_id, :date, :start_time, :end_time, :purpose, 'pending')
                """),
                {
                    "venue_id": venue_id,
                    "user_id": user_id,
                    "date": date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "purpose": purpose
                }
            )
            
            session.commit()
            
            return {
                "success": True, 
                "message": "预约申请已提交，等待审批",
                "reservation_id": result.lastrowid
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()
    
    @staticmethod
    def publish_notification(sender_id: int, title: str, content: str, 
                           target_type: str = "all", receiver_id: Optional[int] = None) -> Dict:
        """发布通知"""
        session = get_db_session()
        try:
            result = session.execute(
                text("""
                    INSERT INTO notifications (sender_id, receiver_id, target_type, title, content, type, priority)
                    VALUES (:sender_id, :receiver_id, :target_type, :title, :content, 'announcement', 'normal')
                """),
                {
                    "sender_id": sender_id,
                    "receiver_id": receiver_id,
                    "target_type": target_type,
                    "title": title,
                    "content": content
                }
            )
            
            session.commit()
            
            return {
                "success": True,
                "message": "通知发布成功",
                "notification_id": result.lastrowid
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()
    
    @staticmethod
    def create_borrow(user_id: int, book_id: int) -> Dict:
        """创建借阅记录"""
        session = get_db_session()
        try:
            # 检查用户是否有超期未还的书
            overdue = session.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM borrows 
                    WHERE user_id = :user_id 
                    AND status = 'overdue'
                """),
                {"user_id": user_id}
            ).fetchone()
            
            if overdue and overdue.count > 0:
                return {"success": False, "message": f"您有{overdue.count}本超期未还的书，请先归还"}
            
            # 检查用户已借数量
            borrowed = session.execute(
                text("""
                    SELECT COUNT(*) as count 
                    FROM borrows 
                    WHERE user_id = :user_id 
                    AND status = 'borrowed'
                """),
                {"user_id": user_id}
            ).fetchone()
            
            if borrowed and borrowed.count >= 10:
                return {"success": False, "message": "您已借阅10本书，达到上限，请先归还部分书籍"}
            
            # 检查图书是否还有库存
            book = session.execute(
                text("SELECT available_quantity, title FROM books WHERE id = :book_id"),
                {"book_id": book_id}
            ).fetchone()
            
            if not book:
                return {"success": False, "message": "图书不存在"}
            
            if book.available_quantity <= 0:
                return {"success": False, "message": f"《{book.title}》暂时无可借库存"}
            
            # 计算应还日期（30天后）
            from datetime import datetime, timedelta
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            # 创建借阅记录
            result = session.execute(
                text("""
                    INSERT INTO borrows (user_id, book_id, borrow_date, due_date, status)
                    VALUES (:user_id, :book_id, CURDATE(), :due_date, 'borrowed')
                """),
                {"user_id": user_id, "book_id": book_id, "due_date": due_date}
            )
            
            # 减少库存
            session.execute(
                text("UPDATE books SET available_quantity = available_quantity - 1 WHERE id = :book_id"),
                {"book_id": book_id}
            )
            
            session.commit()
            
            return {
                "success": True,
                "message": f"借阅成功，应还日期：{due_date}",
                "borrow_id": result.lastrowid,
                "due_date": due_date
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": f"借阅失败：{str(e)}"}
        finally:
            session.close()


# 全局实例
db_tools = DatabaseTools()
