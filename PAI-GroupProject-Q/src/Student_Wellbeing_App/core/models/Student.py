from dataclasses import dataclass


@dataclass
class Student:
    student_id: str
    first_name: str
    lastname: str
    email: str
    password: str
    year: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.lastname}"
