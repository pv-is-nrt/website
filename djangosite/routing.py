# djangosite/routing.py  (new file)
class DatabaseRouter:
    ANALYTICS = {'base': {'Analytic'}}
    MESSAGES  = {'base': {'Message'}}

    def _hit(self, sets, model):
        return model.__name__ in sets.get(model._meta.app_label, set())

    def db_for_read(self, model, **hints):
        if self._hit(self.ANALYTICS, model): return 'analytics'
        if self._hit(self.MESSAGES, model):  return 'messages'
        return 'default'

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        # keep relations in one DB (none cross DBs here, but this is the guard)
        a = obj1._meta if hasattr(obj1, '_meta') else None
        b = obj2._meta if hasattr(obj2, '_meta') else None
        if a and self.db_for_write(type(obj1)) != 'default': return self.db_for_write(type(obj1)) == self.db_for_write(type(obj2))
        if b and self.db_for_write(type(obj2)) != 'default': return self.db_for_write(type(obj2)) == self.db_for_write(type(obj1))
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        model = hints.get('model')
        name = model.__name__ if model else model_name
        is_analytic = name in self.ANALYTICS.get(app_label, set())
        is_message  = name in self.MESSAGES.get(app_label, set())
        if db == 'analytics': return is_analytic
        if db == 'messages':  return is_message
        if db == 'default':   return not (is_analytic or is_message)   # keep these two OFF default
        return False
    