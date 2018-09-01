from django.db.models.signals import pre_delete
from django.dispatch import receiver

from accounts.models import AuthToken
from configurations.models import FixSymbolSessionMapping, FixSessionSetting
from symbols.models import Currency, Symbol


@receiver(pre_delete)
def delete_repo(sender, instance, **kwargs):
    if sender == FixSymbolSessionMapping or sender == FixSessionSetting or sender == Currency or sender == Symbol or sender == AuthToken:
        instance.preDelete()

