# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Django
from django.core.management.base import BaseCommand

# AWX
from awx.main.models import *
from awx.main import models as awxmodels
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from awx.main import access as accessmodels
from sys import exit


class Command(BaseCommand):
    """
    Shows differences in permissions between two users
    """

    help = '''Diffs two users' permissions.
    This code is based on https://gist.github.com/AlanCoding/c5ea1faced5c98e49282fc10fe9fc31d'''

    def add_arguments(self, parser):
        parser.add_argument('--username1', action='store', dest='username1', type=str, help='First username to compare')
        parser.add_argument('--username2', action='store', dest='username2', type=str, help='Second username to compare')
        parser.add_argument('--objectclass', '--class', '--object', action='store', dest='namefilter', type=str, default=None, help='Restrict comparisons to this one object class, e.g. Inventory')
        parser.add_argument('--debug', '-d', action='store_true', dest='debug_enabled', default=False, help='Enable debug-level output')

    def print_debug(self, message):
        if self.debug_enabled:
            print(f'DEBUG: {message}')

    def get_all_models(self, namefilter=None):
        from awx.main import models as awxmodels
        if not namefilter:
            ret_list = [ awxmodels.__dict__.get(modelname) for modelname in dir(awxmodels) if modelname.istitle() ]
        else:
            ret_list = [ awxmodels.__dict__.get(namefilter) ]
        ret_list.remove(Host) if Host in ret_list else None
        ret_list.remove(Job) if Job in ret_list else None
        #return ret_list
        return (Credential, Inventory, JobTemplate, Project)

    def get_access_class_for_model(self, model):
        self.print_debug(f'Requested model: {model}')
        accmodel = accessmodels.access_registry.get(model)
        self.print_debug(f'Access model: {accmodel}')
        return accmodel

    def get_all_perms_for_accessmodel(self, access_model):
        methodlist = [ permname for permname in access_model.__dict__.keys() if permname in self.good_perms ]
        return methodlist

    def test_user_perm(self, user, permname, target_object):
        accmodel = self.get_access_class_for_model(target_object.__class__)
        #self.print_debug(f'{accmodel = }')
        #self.print_debug(f'{permname = }')
        user_access = accmodel(user)
        #self.print_debug(f'{user_access = }')
        #self.print_debug(f'{target_object = }')
        #self.print_debug(f'method is {user_access.__getattribute__(permname)}')

        ## Raise an exception if permname is not one we can handle.
        assert permname in self.good_perms
        if permname in ('can_change'):
            # can_change() requires a kwarg with the intended change, e.g. a name change with { 'name': 'newname' }.
            return user_access.__getattribute__(permname)(target_object, {'name':'newname'})
        else:
            # All other perms require just a target object.
            return user_access.__getattribute__(permname)(target_object)

    def get_all_perms_for_model(self, model):
        content_type = ContentType.objects.filter(model=model.__name__.lower())
        return Permission.objects.filter(content_type__in=content_type)

    def id_this_object(self, obj):
        try:
            return obj.name
        except:
            if model.__name__ == 'Instance':
                return obj.hostname
            else:
                return f'id {obj.id}'

    def compare_user_perms2(self, user1, user2, namefilter=None):
        max_model_name = 0
        max_obj_id = 0
        max_perm = 0
        max_result = 0
        diffs_found = False
        print(f'Differences between {user1.username} and {user2.username}:')
        print(f'{"CLASS":<20} | {"OBJECT":<50} | {"PERMISSION":<20} | {user1.username:<20} | {user2.username:<20}')
        for model in self.get_all_models(namefilter=namefilter):
            access_model = self.get_access_class_for_model(model)
            permlist = self.get_all_perms_for_accessmodel(access_model)
            for model_obj in model.objects.all():
                obj_id = self.id_this_object(model_obj)
                for perm in permlist:
                    user1_result = str(self.test_user_perm(user1, perm, model_obj))
                    user2_result = str(self.test_user_perm(user2, perm, model_obj))
                    print(f'\r{model.__name__:<20} | {obj_id:<50} | {perm:<20} | {user1_result:<20} | {user2_result:<20}', end='')
                    max_model_name = len(model.__name__) if len(model.__name__) > max_model_name else max_model_name
                    max_obj_id = len(obj_id) if len(obj_id) > max_obj_id else max_obj_id
                    max_perm = len(perm) if len(perm) > max_perm else max_perm
                    max_result = len(str(user1_result)) if len(str(user1_result)) > max_result else max_result
                    if user1_result != user2_result:
                        diffs_found = True
                        print()
        # Overwrite the last line as it's always a non-diff line.
        print(f'\r{"":<130}')

        if not diffs_found:
            print(f'No difference found between users {user1.username} and {user2.username}')

    def handle(self, *args, **options):
        if options['username1']:
            user1 = User.objects.get(username=options['username1'])
        if options['username2']:
            user2 = User.objects.get(username=options['username2'])
        self.good_perms = ('can_read', 'can_use', 'can_change', 'can_start')
        self.debug_enabled = options.get('debug_enabled')
        self.compare_user_perms2(user1, user2, namefilter=options.get('namefilter'))
        # Make sure we give back the prompt with a new line.
        print()
