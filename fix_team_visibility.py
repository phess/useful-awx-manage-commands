# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Django
from django.core.management.base import BaseCommand

# AWX
from awx.main.models import *
from sys import exit


class Command(BaseCommand):
    """
    Finds (optionally fix) the issue where a team won't appear for its members.
    """

    help = '''Find and optionally fix the issue where a team won't appear for its members.'''

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', dest='not_just_checking', default=False, help='Not just show what is wrong but actually FIX it.')
        parser.add_argument('--debug', '-d', action='store_true', dest='debug_enabled', default=False, help='Enable debug-level output.')

    def print_debug(self, message):
        if self.debug_enabled:
            print(f'DEBUG: {message}')

    def show_affected_team(self, team):
        """ Show a team's read_role.parents.all() as a means of proving its member_role is not present.
        """
        self.print_debug(f'Team {team.name} member_role: {team.member_role}')
        self.print_debug(f'Team {team.name} read_role parents (should include the member_role): {team.read_role.parents.all()}')

    def fix_team(self, team):
        """ Add this team's member_role to its read_role.parents list.
        """
        if team.member_role not in team.read_role.parents.all():
            team.read_role.parents.add(team.member_role)
            self.print_debug(f'Team {team.name} is modified. Writing to DB now.')
            team.read_role.save()
            self.print_debug(f'Team {team.name} written to DB.')

        # Read again from the DB before returning
        self.print_debug(f'Re-reading team {team.name} from DB to confirm its read_role.parents include member_role.')
        assert team.member_role in team.read_role.parents.all()

    def team_is_affected(self, team):
        """ Return whether a team's read_role.parents.all() DOES NOT the team's member_role, i.e. is affected by this issue.
        """
        return not team.read_role.parents.contains(team.member_role)


    def handle(self, *args, **options):
        self.debug_enabled = options['debug_enabled']
        print(f'Will now inspect {Team.objects.count()} teams')

        # Build list of affected teams
        affected_teams = [ t for t in Team.objects.all() if self.team_is_affected(t) ]

        for team in affected_teams:
            print(f'Team {team.name} is affected.')
            if self.debug_enabled:
                self.show_affected_team(team)
            if options['not_just_checking']:
                # Fix only if told to.
                try:
                    self.fix_team(team)
                    print('FIXED.')
                except Exception as e:
                    print('Unable to fix.')
                    raise e
            else:
                print('Re-run with --fix if you want me to fix it.')
        if len(affected_teams) == 0:
            print('No team is affected.')

        # Make sure we give back the prompt with a new line.
        print()
