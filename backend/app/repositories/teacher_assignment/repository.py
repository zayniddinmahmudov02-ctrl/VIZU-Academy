from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.teacher_assignment import TeacherAssignment


class TeacherAssignmentRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return (
            self.db.query(TeacherAssignment)
            .options(joinedload(TeacherAssignment.teacher), joinedload(TeacherAssignment.course))
            .order_by(TeacherAssignment.created_at.desc())
            .all()
        )

    def get(self, assignment_id: UUID):
        return self.db.query(TeacherAssignment).filter(TeacherAssignment.id == assignment_id).first()

    def get_by_pair(self, teacher_id: UUID, course_id: UUID):
        return (
            self.db.query(TeacherAssignment)
            .filter(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.course_id == course_id,
            )
            .first()
        )

    def create(self, teacher_id: UUID, course_id: UUID):
        item = TeacherAssignment(teacher_id=teacher_id, course_id=course_id)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: TeacherAssignment):
        self.db.delete(item)
        self.db.commit()

    def course_ids_for_teacher(self, teacher_id: UUID) -> list[UUID]:
        rows = (
            self.db.query(TeacherAssignment.course_id)
            .filter(TeacherAssignment.teacher_id == teacher_id)
            .all()
        )
        return [row[0] for row in rows]
