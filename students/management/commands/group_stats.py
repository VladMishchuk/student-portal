from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from student_portal.exceptions import StorageError
from student_portal.storage import load_group


class Command(BaseCommand):
    help = "Показує статистику групи з файлу JSON"

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path, help="шлях до файлу групи")

    def handle(self, *args, **options):
        try:
            group = load_group(options["path"])
        except StorageError as error:
            raise CommandError(error) from error
        self.stdout.write(f"Група {group.name}: {len(group)} студентів")
        self.stdout.write("Розподіл оцінок за шкалою ECTS:")
        for letter, count in sorted(group.ects_distribution().items()):
            self.stdout.write(f"  {letter}: {count}")
        self.stdout.write(self.style.SUCCESS("Готово"))
