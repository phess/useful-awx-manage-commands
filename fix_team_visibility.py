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
        parser.add_argument('--team-id', '--id', action='store', dest='team_id_filter', type=int, default=0, help='Work ONLY on this particular Team ID.')
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

        # Build list of teams to inspect considering the team_id_filter if it was passed by the user.
        # NOTE: filters are encoded as 2-tuples, 'pk=5' becomes ('pk', 5) and 'pk__gt=99' becomes ('pk__gt', 99).
        if options['team_id_filter'] == 0:
            # No filter was passed, use a catch-all filter i.e. 'pk__gt=0'.
            query_filter = ('pk__gt', '0')
        else:
            # Set up a filter.
            query_filter = ('pk', options['team_id_filter'])
        
        team_list_to_consider = Team.objects.filter(query_filter)

        # Build list of affected teams
        affected_teams = [ t for t in team_list_to_consider if self.team_is_affected(t) ]

        print(f'Will now inspect {team_list_to_consider.count()} teams (out of {Team.objects.count()} teams)')
        print('Affected team list:')
        for team in affected_teams:
            print(f'- (ID {team.pk:>3}) "{team.name}" from org "{team.organization.name}"')
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
        if len(affected_teams) == 0:
            print('No team is affected.')
        elif not options['not_just_checking']:
            # yay double negative! \o/
            print('\nTIP: Re-run with --fix if you want me to fix these affected teams.')
            print('TIP2: Re-run with --fix --id XYZ if you want me to fix _only_ team ID XYZ.')
            

        # Make sure we give back the prompt with a new line.
        print()
