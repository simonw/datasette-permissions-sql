from datasette import hookimpl
import json


@hookimpl
def permission_allowed(datasette, actor, action, resource):
    async def inner():
        if actor is None:
            return
        params = {"action": action}
        if resource:
            if len(resource) == 2:
                resource_1, resource_2 = resource
            else:
                resource_1, resource_2 = resource, None
            params["resource_1"] = resource_1
            params["resource_2"] = resource_2
        for key, value in actor.items():
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value, default=repr)
            params["actor_{}".format(key)] = value
        for rule in datasette.plugin_config("datasette-permissions-sql") or []:
            sql = rule["sql"]
            rule_action = rule.get("action")
            rule_resource = rule.get("resource")
            # Optionally match on action/resource
            if rule_action is not None and rule_action != action:
                continue
            if rule_resource is not None and rule_resource != resource:
                continue
            # Execute the SQL
            db = datasette.get_database(rule.get("database"))
            result = await db.execute(sql, params)
            row = result.first()
            if row is None:
                return None
            if len(row) == 1 and str(row[0]) == "-1":
                return False
            return True

    return inner
