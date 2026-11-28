from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from student_portal.exceptions import StorageError
from student_portal.storage import load_group
from students.services import store_group


class Command(BaseCommand):
    help = "Імпортує групу з файлу JSON у базу даних"

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path, help="шлях до файлу групи")

    def handle(self, *args, **options):
        try:
            group = load_group(options["path"])
        except StorageError as error:
            raise CommandError(error) from error
        students_count, grades_count = store_group(group)
        self.stdout.write(
            self.style.SUCCESS(
                f"Група {group.name}: студентів - {students_count}, "
                f"оцінок - {grades_count}"
            )
        )
