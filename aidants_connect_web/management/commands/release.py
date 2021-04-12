import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a new tag using provided version number"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only display changelog, do not tag-push anything",
        )

    def handle(self, *args, **options):
        if not options["dry_run"]:
            self.version = self.ask_for_new_version()

            if not self.confirm_if_ok():
                self.stdout.write(
                    "You’re right, there’s no rush. Try again when you are ready."
                )
                return
            self.stdout.write("OK, let’s tag this then!")
            self.tag_and_push_on_origin(self.version)

        self.changelog = self.display_and_get_changelog()

    def ask_for_new_version(self):
        self.stdout.write("Here are the latest versions:")
        os.system("git tag -l | tail -5")
        version = input("How will you name this new version? ")
        return version

    def confirm_if_ok(self):
        are_they_sure = input(
            self.style.WARNING(f"Version {self.version}, are you sure? (y/N) ")
        )
        return are_they_sure.lower().strip() == "y"

    def display_and_get_changelog(self):
        previous_version = os.popen("git tag | tail -1").read().strip()
        command = (
            f"git log --pretty='format:%s' --first-parent main {previous_version}..main"
        )
        changelog = os.popen(command).read()
        self.stdout.write(
            f"\nHere is the changelog since {previous_version},"
            "you may want to use it for production log:"
        )
        self.write_horizontal_line()
        self.stdout.write(changelog)
        self.write_horizontal_line()
        return changelog

    def tag_and_push_on_origin(self, version):
        os.system(f'git tag -a {version} -m ""')
        os.system("git push --tags")
        self.stdout.write(
            self.style.SUCCESS(f"Tag {version} was pushed to git origin!")
        )

    def write_horizontal_line(self):
        self.stdout.write("-" * 15)
