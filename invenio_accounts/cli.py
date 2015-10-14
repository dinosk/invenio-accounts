# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Command Line Interface for accounts."""

from __future__ import absolute_import, print_function

from functools import wraps

import click
from flask import current_app
from flask_cli import with_appcontext
from flask_security.forms import ConfirmRegisterForm
from flask_security.script import AddRoleCommand, RemoveRoleCommand
from flask_security.utils import encrypt_password
from werkzeug.datastructures import MultiDict
from werkzeug.local import LocalProxy

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def commit(fn):
    """Decorator to commit changes in datastore."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        fn(*args, **kwargs)
        _datastore.commit()
    return wrapper


@click.group()
def accounts():
    """Account commands."""


@accounts.group()
def users():
    """User related commands."""


@accounts.group()
def roles():
    """Role related commands."""


@users.command(name='create')
@click.option('-e', '--email', default=None)
@click.password_option()
@click.option('-a', '--active', default=False, is_flag=True)
@with_appcontext
@commit
def createuser(email, password, active):
    """Create a user."""
    kwargs = dict(email=email, password=password, active='y' if active else '')

    form = ConfirmRegisterForm(MultiDict(kwargs), csrf_enabled=False)

    if form.validate():
        kwargs['password'] = encrypt_password(kwargs['password'])
        kwargs['active'] = active
        _datastore.create_user(**kwargs)
        click.secho('User created successfully.', fg='green')
        kwargs['password'] = '****'
        click.echo(kwargs)
    else:
        raise click.UsageError('Error creating user. %s' % form.errors)


@roles.command(name='create')
@click.option('-n', '--name', default=None)
@click.option('-d', '--description', default=None)
@with_appcontext
@commit
def createrole(**kwargs):
    """Create a role."""
    if not kwargs['name']:
        raise click.UsageError('ERROR: You must specify a role name.')
    _datastore.create_role(**kwargs)
    click.secho('Role "%(name)s" created successfully.' % kwargs, fg='green')


@roles.command()
@click.option('-u', '--user')
@click.option('-r', '--role')
@with_appcontext
@commit
def add(user, role):
    """Add user to role."""
    user, role = _datastore._prepare_role_modify_args(user, role)
    if user is None:
        raise click.UsageError('Cannot find user.')
    if role is None:
        raise click.UsageError('Cannot find role.')
    if _datastore.add_role_to_user(user, role):
        click.secho('Role "{0}" added to user "{1}" '
                    'successfully.'.format(role, user), fg='green')
    else:
        raise click.UsageError('Cannot add role to user.')


@roles.command()
@click.option('-u', '--user')
@click.option('-r', '--role')
@with_appcontext
@commit
def remove(user, role):
    """Remove user from role."""
    user, role = _datastore._prepare_role_modify_args(user, role)
    if user is None:
        raise click.UsageError('Cannot find user.')
    if role is None:
        raise click.UsageError('Cannot find role.')
    if _datastore.remove_role_from_user(user, role):
        click.secho('Role "{0}" removed from user "{1}" '
                    'successfully.'.format(role, user), fg='green')
    else:
        raise click.UsageError('Cannot remove role from user.')


@users.command()
@click.option('-u', '--user')
@with_appcontext
@commit
def activate(user):
    """Activate a user."""
    user_obj = _datastore.get_user(user)
    if user_obj is None:
        raise click.UsageError('ERROR: User not found.')
    if _datastore.activate_user(user_obj):
        click.secho('User "%s" has been activated.' % user, fg='green')
    else:
        click.secho('User "%s" was already activated.' % user, fg='yellow')


@users.command()
@click.option('-u', '--user')
@with_appcontext
@commit
def deactivate(user):
    """Deactivate a user."""
    user_obj = _datastore.get_user(user)
    if user_obj is None:
        raise click.UsageError('ERROR: User not found.')
    if _datastore.deactivate_user(user_obj):
        click.secho('User "%s" has been deactivated.' % user, fg='green')
    else:
        click.secho('User "%s" was already deactivated.' % user, fg='yellow')
